from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.services.normalization import normalize_date, normalize_text, normalize_time
from app.services.parsing.contracts import ExtractedEmployeeRow, ParsedDocument

CANONICAL_FIELDS = [
    "client_name",
    "client_id",
    "work_order_number",
    "employee_name",
    "employee_id",
    "location",
    "shift_date",
    "start_time",
    "end_time",
    "total_hours",
    "overtime_hours",
    "pay_rate",
    "bill_rate",
    "supervisor_name",
    "signature_present",
]

_TIME_RE = re.compile(r"(\d{1,2})\s*[:.,]?\s*(\d{2})\s*([AaPp][A-Za-z^]?)?")
_WO_RE = re.compile(r"\bWO\s*#?\s*([A-Z0-9\-]{4,})\b", re.IGNORECASE)
_JOB_RE = re.compile(r"\bJOB\s*#?\s*[:\-]?\s*(\d{3,})\b", re.IGNORECASE)
_DATE_RE = re.compile(r"\b\d{1,2}\s*/\s*\d{1,3}\s*/\s*\d{2,4}\b")


def _clean_line(line: str) -> str:
    collapsed = re.sub(r"\s+", " ", line.strip())
    return collapsed


def _normalize_ocr_date(value: str) -> Optional[str]:
    compact = value.replace(" ", "")
    match = re.match(r"^(\d{1,2})/(\d{1,3})/(\d{2,4})$", compact)
    if not match:
        return normalize_date(value)

    month = int(match.group(1))
    raw_day = match.group(2)
    year = match.group(3)
    if len(raw_day) == 3 and raw_day.startswith("20"):
        raw_day = "20"
    day = int(raw_day)
    if len(year) == 2:
        year = f"20{year}"

    try:
        parsed = datetime(int(year), month, day)
    except ValueError:
        return normalize_date(value)
    return parsed.date().isoformat()


def _normalize_ocr_time(value: str) -> Optional[str]:
    cleaned = value.strip()
    cleaned = cleaned.replace(",", ":").replace(".", ":")
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.replace("^", "M")
    cleaned = re.sub(r"\bAN\b", "AM", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bAR\b", "AM", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bAU\b", "AM", cleaned, flags=re.IGNORECASE)

    match = _TIME_RE.search(cleaned)
    if not match:
        if re.fullmatch(r"\d{3,4}", cleaned):
            if len(cleaned) == 3:
                cleaned = f"{cleaned[0]}:{cleaned[1:]}"
            else:
                cleaned = f"{cleaned[:2]}:{cleaned[2:]}"
        return normalize_time(cleaned)

    hour = int(match.group(1))
    minute = int(match.group(2))
    if not (0 <= minute <= 59 and 0 <= hour <= 23):
        return None
    suffix = (match.group(3) or "").upper()
    if suffix.startswith("A"):
        suffix = "AM"
    elif suffix.startswith("P"):
        suffix = "PM"
    else:
        suffix = ""

    candidate = f"{hour}:{minute:02d}" + (f" {suffix}" if suffix else "")
    return normalize_time(candidate)


def _is_probable_name(line: str) -> bool:
    if any(ch.isdigit() for ch in line):
        return False

    cleaned = re.sub(r'^[^A-Za-z"]+', "", line).strip(' "\'')
    if len(cleaned) < 5:
        return False

    upper = cleaned.upper()
    blocked_terms = {
        "MWIS",
        "JOB",
        "SHIFT",
        "DATE",
        "WORKFORCE",
        "CLOCK",
        "OWNER",
        "SIGNATURE",
        "DESCRIPTION",
        "EQUIPMENT",
        "TASK",
        "HAZARD",
        "MITIGATIONS",
        "SITE MANAGER",
        "FOREMAN",
        "TIME IN",
        "TIME OUT",
    }
    if upper in blocked_terms:
        return False
    if any(term in upper for term in ("CLOCK", "WORKFORCE", "REPRESENTATIVE")):
        return False
    if any(term in upper for term in ("LIFT", "COMPRESSOR", "IMPACTS", "TRUCK", "MACHINE", "FORKLIFT", "TOOL")):
        return False

    parts = cleaned.split()
    if len(parts) < 2:
        return False
    return all(len(part) >= 2 for part in parts[:2])


def _title_name(value: str) -> str:
    normalized = normalize_text(value) or value
    return " ".join(part.capitalize() for part in normalized.split())


def _duration_hours(start_time: Optional[str], end_time: Optional[str]) -> Optional[str]:
    if not start_time or not end_time:
        return None
    try:
        start = datetime.strptime(start_time, "%H:%M")
        end = datetime.strptime(end_time, "%H:%M")
    except ValueError:
        return None

    minutes = int((end - start).total_seconds() / 60)
    if minutes < 0:
        minutes += 24 * 60
    return f"{minutes / 60:.2f}"


@dataclass
class _CommonFields:
    client_name: Optional[str]
    work_order_number: Optional[str]
    shift_date: Optional[str]
    location: Optional[str]


class MacOSVisionPdfTextExtractor:
    def __init__(self) -> None:
        self.script_path = Path(__file__).with_name("macos_vision_ocr.swift")

    def extract_text(self, pdf_path: str) -> Optional[str]:
        if sys.platform != "darwin":
            return None
        if not self.script_path.exists():
            return None

        source = Path(pdf_path)
        if not source.exists() or source.stat().st_size < 1024:
            return None

        env = os.environ.copy()
        cache_path = "/tmp/swift-module-cache"
        env["CLANG_MODULE_CACHE_PATH"] = cache_path
        env["SWIFT_MODULECACHE_PATH"] = cache_path
        Path(cache_path).mkdir(parents=True, exist_ok=True)

        try:
            run = subprocess.run(
                ["swift", str(self.script_path), str(source)],
                check=False,
                capture_output=True,
                text=True,
                timeout=45,
                env=env,
            )
        except (OSError, subprocess.SubprocessError):
            return None

        if run.returncode != 0:
            return None

        text = run.stdout.strip()
        return text if text else None


class RuleBasedPdfParser:
    def parse(
        self,
        doc_type: str,
        filename: str,
        extracted_text: str,
    ) -> ParsedDocument:
        lines = [_clean_line(line) for line in extracted_text.splitlines()]
        lines = [line for line in lines if line]
        common = self._extract_common(lines, extracted_text)

        if doc_type == "work_order":
            rows = self._parse_ctk_rows(lines, common)
            fields = self._build_fields(common=common, rows=rows, signature_present=None, supervisor_name=None)
            return ParsedDocument(
                doc_type=doc_type,
                parser_name="macos_vision_ctk_parser",
                parser_version="v0.1",
                fields=fields,
                rows=rows,
            )

        if doc_type == "employee":
            rows, supervisor_name, signature_present = self._parse_jsa_rows(lines, common, extracted_text)
            fields = self._build_fields(
                common=common,
                rows=rows,
                signature_present=signature_present,
                supervisor_name=supervisor_name,
            )
            return ParsedDocument(
                doc_type=doc_type,
                parser_name="macos_vision_jsa_parser",
                parser_version="v0.1",
                fields=fields,
                rows=rows,
            )

        rows = self._parse_daily_report_rows(lines, common)
        fields = self._build_fields(common=common, rows=rows, signature_present=None, supervisor_name=None)
        return ParsedDocument(
            doc_type=doc_type,
            parser_name="macos_vision_daily_report_parser",
            parser_version="v0.1",
            fields=fields,
            rows=rows,
        )

    def _extract_common(self, lines: list[str], raw_text: str) -> _CommonFields:
        upper_text = raw_text.upper()
        client_name = "MW INDUSTRIAL SERVICES" if "MWIS" in upper_text else None

        work_order_number = None
        wo_match = _WO_RE.search(raw_text)
        if wo_match:
            work_order_number = wo_match.group(1).replace(" ", "")

        job_number = None
        for idx, line in enumerate(lines):
            upper_line = line.upper()
            if "JOB" in upper_line and ("NUMBER" in upper_line or "#" in upper_line):
                for offset in range(1, 4):
                    if idx + offset < len(lines):
                        candidate = re.sub(r"[^0-9]", "", lines[idx + offset])
                        if len(candidate) >= 3:
                            job_number = candidate
                            break
                if job_number:
                    break
            inline_job = _JOB_RE.search(line)
            if inline_job:
                job_number = inline_job.group(1)
                break

        # Use job number when available because it appears across all three real sample sheets.
        if job_number:
            work_order_number = job_number

        shift_date = None
        date_match = _DATE_RE.search(raw_text)
        if date_match:
            shift_date = _normalize_ocr_date(date_match.group(0))

        location = None
        for idx, line in enumerate(lines):
            if "AREA" in line.upper() and "LOCATION" in line.upper():
                for offset in range(1, 3):
                    if idx + offset < len(lines):
                        candidate = lines[idx + offset]
                        if _is_probable_name(candidate):
                            location = candidate
                            break
                break
        if location:
            location = normalize_text(location)

        return _CommonFields(
            client_name=client_name,
            work_order_number=work_order_number,
            shift_date=shift_date,
            location=location,
        )

    def _extract_section(self, lines: list[str], start_markers: list[str], end_markers: list[str]) -> list[str]:
        start_index = 0
        for idx, line in enumerate(lines):
            if any(marker in line.upper() for marker in start_markers):
                start_index = idx + 1
                break

        end_index = len(lines)
        for idx in range(start_index, len(lines)):
            if any(marker in lines[idx].upper() for marker in end_markers):
                end_index = idx
                break

        return lines[start_index:end_index]

    def _rows_from_name_time_section(self, section_lines: list[str], common: _CommonFields) -> list[ExtractedEmployeeRow]:
        rows: list[ExtractedEmployeeRow] = []
        current_name: Optional[str] = None
        times: list[str] = []

        def flush_current() -> None:
            nonlocal current_name, times
            if not current_name:
                times = []
                return
            start_time = times[0] if times else None
            end_time = times[1] if len(times) > 1 else None
            rows.append(
                ExtractedEmployeeRow(
                    row_index=len(rows),
                    fields={
                        "work_order_number": common.work_order_number,
                        "employee_id": None,
                        "employee_name": current_name,
                        "shift_date": common.shift_date,
                        "start_time": start_time,
                        "end_time": end_time,
                        "total_hours": _duration_hours(start_time, end_time),
                        "location": common.location,
                    },
                )
            )
            current_name = None
            times = []

        for line in section_lines:
            cleaned = re.sub(r'^[^A-Za-z0-9"]+', "", line).strip(' "\'')
            if _is_probable_name(cleaned):
                flush_current()
                current_name = _title_name(cleaned)
                continue

            normalized_time = _normalize_ocr_time(cleaned)
            if normalized_time and current_name:
                times.append(normalized_time)
                if len(times) >= 2:
                    flush_current()

        flush_current()
        return rows

    def _parse_daily_report_rows(self, lines: list[str], common: _CommonFields) -> list[ExtractedEmployeeRow]:
        workforce_section = self._extract_section(
            lines=lines,
            start_markers=["MWIS WORKFORCE"],
            end_markers=["DESCRIPTION OF WORK", "OWNER REPRESENTATIVE"],
        )
        rows = self._rows_from_name_time_section(workforce_section, common)
        return rows

    def _parse_ctk_rows(self, lines: list[str], common: _CommonFields) -> list[ExtractedEmployeeRow]:
        workforce_section = self._extract_section(
            lines=lines,
            start_markers=["MWIS WORKFORCE"],
            end_markers=["OWNER REPRESENTATIVE", "SIGNATURE"],
        )
        rows = self._rows_from_name_time_section(workforce_section, common)
        return rows

    def _parse_jsa_rows(
        self, lines: list[str], common: _CommonFields, raw_text: str
    ) -> tuple[list[ExtractedEmployeeRow], Optional[str], Optional[str]]:
        jsa_section = self._extract_section(
            lines=lines,
            start_markers=["JOB #", "DATE"],
            end_markers=["TASK STEPS", "HAZARDS IDENTIFIED"],
        )

        names: list[str] = []
        for line in jsa_section:
            cleaned = re.sub(r"^[0-9./\"'\\-]+\s*", "", line).strip()
            if _is_probable_name(cleaned):
                normalized = _title_name(cleaned)
                if normalized not in names:
                    names.append(normalized)

        rows = [
            ExtractedEmployeeRow(
                row_index=index,
                fields={
                    "work_order_number": common.work_order_number,
                    "employee_id": None,
                    "employee_name": name,
                    "shift_date": common.shift_date,
                    "start_time": None,
                    "end_time": None,
                    "total_hours": None,
                    "location": common.location,
                },
            )
            for index, name in enumerate(names)
        ]

        supervisor_name = None
        for idx, line in enumerate(lines):
            if "FOREMAN" in line.upper():
                if idx + 1 < len(lines) and _is_probable_name(lines[idx + 1]):
                    supervisor_name = _title_name(lines[idx + 1])
                break

        signature_present = "true" if "SIGNING THIS FORM INDICATES" in raw_text.upper() else None
        return rows, supervisor_name, signature_present

    def _build_fields(
        self,
        common: _CommonFields,
        rows: list[ExtractedEmployeeRow],
        signature_present: Optional[str],
        supervisor_name: Optional[str],
    ) -> dict[str, Optional[str]]:
        first_row_fields = rows[0].fields if rows else {}
        fields: dict[str, Optional[str]] = {key: None for key in CANONICAL_FIELDS}
        fields.update(
            {
                "client_name": common.client_name,
                "work_order_number": common.work_order_number,
                "employee_name": first_row_fields.get("employee_name"),
                "employee_id": first_row_fields.get("employee_id"),
                "location": common.location,
                "shift_date": common.shift_date,
                "start_time": first_row_fields.get("start_time"),
                "end_time": first_row_fields.get("end_time"),
                "total_hours": first_row_fields.get("total_hours"),
                "overtime_hours": None,
                "supervisor_name": supervisor_name,
                "signature_present": signature_present,
            }
        )
        return fields
