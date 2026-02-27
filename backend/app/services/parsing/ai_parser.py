from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Optional

from app.core.config import settings
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

ROW_FIELDS = {
    "work_order_number",
    "employee_id",
    "employee_name",
    "shift_date",
    "start_time",
    "end_time",
    "total_hours",
    "location",
}


class OpenAIDocumentParser:
    """LLM-based parser for OCR text.

    Uses environment variables:
    - OPENAI_API_KEY
    - OPENAI_EXTRACTION_MODEL (optional, default: gpt-4.1-mini)
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        self.api_key = api_key or settings.openai_api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or settings.openai_extraction_model or os.getenv("OPENAI_EXTRACTION_MODEL", "gpt-4.1-mini")

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def parse(self, doc_type: str, filename: str, extracted_text: str) -> Optional[ParsedDocument]:
        if not self.enabled:
            return None
        text = extracted_text.strip()
        if not text:
            return None

        payload = self._build_payload(doc_type=doc_type, filename=filename, extracted_text=text[:20000])
        response = self._call_openai(payload)
        if not response:
            return None

        parsed = self._parse_completion_json(response)
        if not parsed:
            return None
        if not self._validate_output_schema(parsed):
            return None

        fields = self._coerce_fields(parsed.get("fields", {}))
        rows = self._coerce_rows(parsed.get("rows", []))
        if not rows and not any(fields.values()):
            return None

        return ParsedDocument(
            doc_type=doc_type,
            parser_name="openai_structured_parser",
            parser_version="v0.1",
            fields=fields,
            rows=rows,
        )

    def _build_payload(self, doc_type: str, filename: str, extracted_text: str) -> dict[str, Any]:
        system = (
            "You extract structured payroll/worksheet data from OCR text. "
            "Return only valid JSON, no markdown. "
            "Prefer null over guessing. "
            "For rows, output one row per employee entry when present."
        )
        user = {
            "task": "Extract canonical fields and employee rows from OCR text",
            "doc_type": doc_type,
            "filename": filename,
            "canonical_fields": CANONICAL_FIELDS,
            "rules": {
                "dates_should_be": "YYYY-MM-DD when identifiable",
                "times_should_be": "HH:MM 24h when identifiable",
                "rows": "include work_order_number/employee_name/employee_id/shift_date/start_time/end_time/total_hours/location if present",
            },
            "output_shape": {
                "fields": {field: "string|null" for field in CANONICAL_FIELDS},
                "rows": [
                    {
                        "row_index": "integer",
                        "fields": {
                            "work_order_number": "string|null",
                            "employee_id": "string|null",
                            "employee_name": "string|null",
                            "shift_date": "string|null",
                            "start_time": "string|null",
                            "end_time": "string|null",
                            "total_hours": "string|null",
                            "location": "string|null",
                        },
                    }
                ],
            },
            "ocr_text": extracted_text,
        }
        return {
            "model": self.model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(user)},
            ],
        }

    def _call_openai(self, payload: dict[str, Any]) -> Optional[dict[str, Any]]:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
            return None

    def _parse_completion_json(self, response: dict[str, Any]) -> Optional[dict[str, Any]]:
        try:
            content = response["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            return None
        if not isinstance(content, str):
            return None
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            return None
        return parsed if isinstance(parsed, dict) else None

    def _validate_output_schema(self, payload: dict[str, Any]) -> bool:
        fields = payload.get("fields")
        rows = payload.get("rows")
        if not isinstance(fields, dict) or not isinstance(rows, list):
            return False

        for field_name, value in fields.items():
            if field_name not in CANONICAL_FIELDS:
                continue
            if not _is_scalar_or_none(value):
                return False

        for row in rows:
            if not isinstance(row, dict):
                return False
            row_fields = row.get("fields")
            if not isinstance(row_fields, dict):
                return False

            row_index = row.get("row_index")
            if row_index is not None and (not isinstance(row_index, int) or isinstance(row_index, bool)):
                return False

            for field_name, value in row_fields.items():
                if field_name not in ROW_FIELDS:
                    continue
                if not _is_scalar_or_none(value):
                    return False

        return True

    def _coerce_fields(self, raw_fields: Any) -> dict[str, Optional[str]]:
        fields: dict[str, Optional[str]] = {field: None for field in CANONICAL_FIELDS}
        if not isinstance(raw_fields, dict):
            return fields
        for field in CANONICAL_FIELDS:
            value = raw_fields.get(field)
            if value is None:
                fields[field] = None
            else:
                text = str(value).strip()
                fields[field] = text if text else None
        return fields

    def _coerce_rows(self, raw_rows: Any) -> list[ExtractedEmployeeRow]:
        if not isinstance(raw_rows, list):
            return []

        rows: list[ExtractedEmployeeRow] = []
        for fallback_index, row in enumerate(raw_rows):
            if not isinstance(row, dict):
                continue
            fields = row.get("fields")
            if not isinstance(fields, dict):
                continue
            row_index_raw = row.get("row_index")
            row_index = row_index_raw if isinstance(row_index_raw, int) else fallback_index
            rows.append(
                ExtractedEmployeeRow(
                    row_index=row_index,
                    fields={
                        "work_order_number": _as_optional_string(fields.get("work_order_number")),
                        "employee_id": _as_optional_string(fields.get("employee_id")),
                        "employee_name": _as_optional_string(fields.get("employee_name")),
                        "shift_date": _as_optional_string(fields.get("shift_date")),
                        "start_time": _as_optional_string(fields.get("start_time")),
                        "end_time": _as_optional_string(fields.get("end_time")),
                        "total_hours": _as_optional_string(fields.get("total_hours")),
                        "location": _as_optional_string(fields.get("location")),
                    },
                )
            )
        return rows


def _as_optional_string(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def _is_scalar_or_none(value: Any) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))
