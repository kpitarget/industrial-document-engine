from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Optional


DOC_TYPES = ("client", "work_order", "employee")


@dataclass
class RowCandidate:
    row_id: int
    doc_type: str
    row_index: int
    normalized_fields: dict[str, Optional[str]]


@dataclass
class RowMatchCandidate:
    match_key: str
    status: str
    confidence: float
    reason: str
    row_ids_by_doc: dict[str, Optional[int]]
    payload: dict[str, object]


def build_match_key(fields: dict[str, Optional[str]]) -> str:
    work_order_number = fields.get("work_order_number")
    employee_id = fields.get("employee_id")
    employee_name = fields.get("employee_name")
    shift_date = fields.get("shift_date")

    if work_order_number and employee_id and shift_date:
        return f"{work_order_number}|{employee_id}|{shift_date}"
    if work_order_number and employee_name and shift_date:
        return f"{work_order_number}|{employee_name}|{shift_date}"
    return ""


def match_row_candidates(rows: list[RowCandidate]) -> list[RowMatchCandidate]:
    by_key: dict[str, list[RowCandidate]] = defaultdict(list)
    unkeyed_counter = 0
    for row in rows:
        key = build_match_key(row.normalized_fields)
        if not key:
            key = f"UNKEYED::{row.doc_type}:{row.row_index}:{unkeyed_counter}"
            unkeyed_counter += 1
        by_key[key].append(row)

    matches: list[RowMatchCandidate] = []
    for key, grouped_rows in by_key.items():
        by_doc: dict[str, RowCandidate] = {}
        duplicate_docs: set[str] = set()
        for row in sorted(grouped_rows, key=lambda item: item.row_index):
            if row.doc_type in by_doc:
                duplicate_docs.add(row.doc_type)
                continue
            by_doc[row.doc_type] = row

        row_ids_by_doc = {doc_type: by_doc.get(doc_type).row_id if by_doc.get(doc_type) else None for doc_type in DOC_TYPES}
        missing_docs = [doc_type for doc_type in DOC_TYPES if doc_type not in by_doc]

        if key.startswith("UNKEYED::"):
            status = "insufficient_data"
            confidence = 0.2
            reason = "Row missing one or more key fields: work_order_number, employee identifier, shift_date"
        elif duplicate_docs:
            status = "conflict"
            confidence = 0.4
            reason = f"Duplicate rows found for document types: {', '.join(sorted(duplicate_docs))}"
        elif not missing_docs:
            status = "matched"
            confidence = 1.0
            reason = "Matched across client, work_order, and employee documents"
        else:
            status = "partial"
            confidence = round(len(by_doc) / len(DOC_TYPES), 2)
            reason = f"Missing row from document types: {', '.join(missing_docs)}"

        matches.append(
            RowMatchCandidate(
                match_key=key,
                status=status,
                confidence=confidence,
                reason=reason,
                row_ids_by_doc=row_ids_by_doc,
                payload={
                    "missing_docs": missing_docs,
                    "duplicate_docs": sorted(duplicate_docs),
                    "present_docs": sorted(by_doc.keys()),
                },
            )
        )

    return sorted(matches, key=lambda item: item.match_key)
