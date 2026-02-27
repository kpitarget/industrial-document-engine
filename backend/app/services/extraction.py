from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.services.parsing.contracts import ExtractedEmployeeRow, ParsedDocument
from app.services.parsing.real_pdf_parser import MacOSVisionPdfTextExtractor, RuleBasedPdfParser
from app.services.parsing.ai_parser import OpenAIDocumentParser


@dataclass
class ExtractedPayload:
    parser_name: str
    parser_version: str
    fields: dict[str, Optional[str]]


class MockPdfExtractionService:
    """OCR-backed parser with deterministic fallback for local MVP flow.

    TODO: Add non-macOS OCR provider and parser profile registry for production.
    """

    def __init__(self) -> None:
        self.text_extractor = MacOSVisionPdfTextExtractor()
        self.ai_parser = OpenAIDocumentParser()
        self.rule_parser = RuleBasedPdfParser()

    def extract(self, doc_type: str, filename: str, storage_path: Optional[str] = None) -> ExtractedPayload:
        parsed = self.parse(doc_type=doc_type, filename=filename, storage_path=storage_path)
        return ExtractedPayload(
            parser_name=parsed.parser_name,
            parser_version=parsed.parser_version,
            fields=parsed.fields,
        )

    def _mock_extract(self, doc_type: str, filename: str) -> ExtractedPayload:
        basename = filename.lower()
        base_fields = {
            "client_name": "Acme Industries",
            "client_id": "C-102",
            "work_order_number": "WO4412",
            "employee_name": "Mike Rowan",
            "employee_id": "E10352",
            "location": "Plant 2",
            "shift_date": "02/20/2026",
            "start_time": "8:00 AM",
            "end_time": "4:00 PM",
            "total_hours": "8.0",
            "overtime_hours": "0",
            "supervisor_name": "John Carter",
            "signature_present": "yes",
            "pay_rate": "$28.50",
            "bill_rate": "$45.00",
        }

        if "mismatch" in basename or doc_type == "employee":
            base_fields["total_hours"] = "7.5"

        if doc_type == "work_order":
            base_fields["signature_present"] = None
            base_fields["pay_rate"] = None
        if doc_type == "client":
            base_fields["pay_rate"] = None
        if doc_type == "employee":
            base_fields["bill_rate"] = None

        return ExtractedPayload(parser_name="mock_parser", parser_version="v1", fields=base_fields)

    def parse(self, doc_type: str, filename: str, storage_path: Optional[str] = None) -> ParsedDocument:
        if storage_path:
            source = Path(storage_path)
            if source.exists():
                extracted_text = self.text_extractor.extract_text(str(source))
                if extracted_text:
                    ai_parsed = self.ai_parser.parse(
                        doc_type=doc_type,
                        filename=filename,
                        extracted_text=extracted_text,
                    )
                    parsed = self.rule_parser.parse(
                        doc_type=doc_type,
                        filename=filename,
                        extracted_text=extracted_text,
                    )
                    merged = _prefer_primary(ai_parsed, parsed) if ai_parsed else parsed
                    if merged.rows or any(value for value in merged.fields.values()):
                        return merged

        extracted = self._mock_extract(doc_type=doc_type, filename=filename)
        rows = self._extract_rows(doc_type=doc_type, filename=filename, base_fields=extracted.fields)
        return ParsedDocument(
            doc_type=doc_type,
            parser_name=extracted.parser_name,
            parser_version=extracted.parser_version,
            fields=extracted.fields,
            rows=rows,
        )

    def _extract_rows(self, doc_type: str, filename: str, base_fields: dict[str, Optional[str]]) -> list[ExtractedEmployeeRow]:
        basename = filename.lower()

        # Simulate multi-employee sheet parsing for realistic workflow testing.
        # TODO: Replace this with OCR/table extraction output from real documents.
        is_multi_employee = any(token in basename for token in ("daily", "jsa", "ctk", "crew", "timesheet", "multi"))
        if not is_multi_employee:
            return [
                ExtractedEmployeeRow(
                    row_index=0,
                    fields={
                        "work_order_number": base_fields.get("work_order_number"),
                        "employee_id": base_fields.get("employee_id"),
                        "employee_name": base_fields.get("employee_name"),
                        "shift_date": base_fields.get("shift_date"),
                        "start_time": base_fields.get("start_time"),
                        "end_time": base_fields.get("end_time"),
                        "total_hours": base_fields.get("total_hours"),
                        "location": base_fields.get("location"),
                    },
                )
            ]

        employee_rows = [
            {
                "employee_id": "E10352",
                "employee_name": "Mike Rowan",
                "start_time": "8:00 AM",
                "end_time": "4:00 PM",
                "total_hours": "8.0",
            },
            {
                "employee_id": "E10417",
                "employee_name": "Kate Moran",
                "start_time": "7:30 AM",
                "end_time": "3:30 PM",
                "total_hours": "8.0",
            },
            {
                "employee_id": "E10501",
                "employee_name": "James Tonin",
                "start_time": "8:00 AM",
                "end_time": "4:30 PM",
                "total_hours": "8.5",
            },
        ]

        rows: list[ExtractedEmployeeRow] = []
        for index, row in enumerate(employee_rows):
            row_total_hours = row["total_hours"]
            if doc_type == "employee" and "mismatch" in basename and index == 1:
                row_total_hours = "7.5"
            rows.append(
                ExtractedEmployeeRow(
                    row_index=index,
                    fields={
                        "work_order_number": base_fields.get("work_order_number"),
                        "employee_id": row["employee_id"],
                        "employee_name": row["employee_name"],
                        "shift_date": base_fields.get("shift_date"),
                        "start_time": row["start_time"],
                        "end_time": row["end_time"],
                        "total_hours": row_total_hours,
                        "location": base_fields.get("location"),
                    },
                )
            )

        return rows


def _prefer_primary(primary: ParsedDocument, fallback: ParsedDocument) -> ParsedDocument:
    fields = dict(fallback.fields)
    for key, value in primary.fields.items():
        if value not in (None, ""):
            fields[key] = value

    rows = primary.rows if primary.rows else fallback.rows
    return ParsedDocument(
        doc_type=primary.doc_type,
        parser_name=f"{primary.parser_name}+{fallback.parser_name}",
        parser_version=f"{primary.parser_version}+{fallback.parser_version}",
        fields=fields,
        rows=rows,
    )
