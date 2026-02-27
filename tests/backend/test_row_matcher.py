from __future__ import annotations

from app.services.matching.row_matcher import RowCandidate, build_match_key, match_row_candidates


def test_build_match_key_prefers_employee_id() -> None:
    key = build_match_key(
        {
            "work_order_number": "WO4412",
            "employee_id": "E10352",
            "employee_name": "MIKE ROWAN",
            "shift_date": "2026-02-20",
        }
    )
    assert key == "WO4412|E10352|2026-02-20"


def test_match_row_candidates_returns_full_match() -> None:
    rows = [
        RowCandidate(
            row_id=1,
            doc_type="client",
            row_index=0,
            normalized_fields={"work_order_number": "WO4412", "employee_id": "E10352", "shift_date": "2026-02-20"},
        ),
        RowCandidate(
            row_id=2,
            doc_type="work_order",
            row_index=0,
            normalized_fields={"work_order_number": "WO4412", "employee_id": "E10352", "shift_date": "2026-02-20"},
        ),
        RowCandidate(
            row_id=3,
            doc_type="employee",
            row_index=0,
            normalized_fields={"work_order_number": "WO4412", "employee_id": "E10352", "shift_date": "2026-02-20"},
        ),
    ]

    matches = match_row_candidates(rows)
    assert len(matches) == 1
    assert matches[0].status == "matched"
    assert matches[0].row_ids_by_doc["client"] == 1
    assert matches[0].row_ids_by_doc["work_order"] == 2
    assert matches[0].row_ids_by_doc["employee"] == 3


def test_match_row_candidates_partial_when_doc_missing() -> None:
    rows = [
        RowCandidate(
            row_id=1,
            doc_type="client",
            row_index=0,
            normalized_fields={"work_order_number": "WO4412", "employee_id": "E10352", "shift_date": "2026-02-20"},
        ),
        RowCandidate(
            row_id=2,
            doc_type="employee",
            row_index=0,
            normalized_fields={"work_order_number": "WO4412", "employee_id": "E10352", "shift_date": "2026-02-20"},
        ),
    ]

    matches = match_row_candidates(rows)
    assert len(matches) == 1
    assert matches[0].status == "partial"
    assert "work_order" in matches[0].reason


def test_match_row_candidates_conflict_on_duplicate_doc_type() -> None:
    rows = [
        RowCandidate(
            row_id=1,
            doc_type="employee",
            row_index=0,
            normalized_fields={"work_order_number": "WO4412", "employee_id": "E10352", "shift_date": "2026-02-20"},
        ),
        RowCandidate(
            row_id=2,
            doc_type="employee",
            row_index=1,
            normalized_fields={"work_order_number": "WO4412", "employee_id": "E10352", "shift_date": "2026-02-20"},
        ),
    ]

    matches = match_row_candidates(rows)
    assert len(matches) == 1
    assert matches[0].status == "conflict"
    assert "Duplicate rows" in matches[0].reason


def test_match_row_candidates_insufficient_data_for_unkeyed_rows() -> None:
    rows = [
        RowCandidate(
            row_id=1,
            doc_type="employee",
            row_index=0,
            normalized_fields={"work_order_number": None, "employee_id": None, "shift_date": None},
        )
    ]

    matches = match_row_candidates(rows)
    assert len(matches) == 1
    assert matches[0].status == "insufficient_data"
