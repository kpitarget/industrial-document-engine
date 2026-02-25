from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ExtractedPayload:
    parser_name: str
    parser_version: str
    fields: dict[str, Optional[str]]


class MockPdfExtractionService:
    """Deterministic extraction stub for local MVP flow.

    TODO: Replace with real PDF text extraction and OCR fallback pipeline.
    """

    def extract(self, doc_type: str, filename: str) -> ExtractedPayload:
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
