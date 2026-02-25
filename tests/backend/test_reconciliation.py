from __future__ import annotations

from app.services.reconciliation import reconcile


def _base_field_values() -> dict[str, dict[str, str | None]]:
    return {
        "client_name": {"client": "ACME INDUSTRIES", "work_order": "ACME INDUSTRIES", "employee": None},
        "client_id": {"client": "C102", "work_order": "C102", "employee": None},
        "work_order_number": {"client": "WO4412", "work_order": "WO4412", "employee": "WO4412"},
        "employee_name": {"client": "MIKE ROWAN", "work_order": None, "employee": "MIKE ROWAN"},
        "employee_id": {"client": "E10352", "work_order": "E10352", "employee": "E10352"},
        "location": {"client": "PLANT 2", "work_order": "PLANT 2", "employee": "PLANT 2"},
        "shift_date": {"client": "2026-02-20", "work_order": "2026-02-20", "employee": "2026-02-20"},
        "start_time": {"client": "08:00", "work_order": "08:05", "employee": "08:00"},
        "end_time": {"client": "16:00", "work_order": "16:10", "employee": "16:00"},
        "total_hours": {"client": "8.00", "work_order": "8.00", "employee": "8.00"},
        "overtime_hours": {"client": "0.00", "work_order": "0.00", "employee": "0.00"},
        "pay_rate": {"client": None, "work_order": None, "employee": "28.50"},
        "bill_rate": {"client": "45.00", "work_order": "45.00", "employee": None},
        "supervisor_name": {"client": "JOHN CARTER", "work_order": "JOHN CARTER", "employee": "JOHN CARTER"},
        "signature_present": {"client": None, "work_order": None, "employee": "true"},
    }


def test_exact_mismatch_becomes_exception() -> None:
    values = _base_field_values()
    values["employee_id"]["employee"] = "E99999"

    field_results, record_status = reconcile(values, has_all_required_docs=True)
    employee_id_result = next(row for row in field_results if row.field_key == "employee_id")

    assert employee_id_result.status == "mismatch"
    assert record_status == "exception"


def test_fuzzy_below_threshold_is_warning() -> None:
    values = _base_field_values()
    values["location"]["employee"] = "WAREHOUSE 9"

    field_results, record_status = reconcile(values, has_all_required_docs=True)
    location_result = next(row for row in field_results if row.field_key == "location")

    assert location_result.status == "warning"
    assert record_status == "matched_with_warnings"


def test_numeric_tolerance_failure_is_exception() -> None:
    values = _base_field_values()
    values["total_hours"]["employee"] = "7.50"

    field_results, record_status = reconcile(values, has_all_required_docs=True)
    total_hours_result = next(row for row in field_results if row.field_key == "total_hours")

    assert total_hours_result.status == "mismatch"
    assert record_status == "exception"


def test_missing_required_field_is_exception() -> None:
    values = _base_field_values()
    values["work_order_number"]["employee"] = None

    field_results, record_status = reconcile(values, has_all_required_docs=True)
    work_order_result = next(row for row in field_results if row.field_key == "work_order_number")

    assert work_order_result.status == "missing"
    assert record_status == "exception"


def test_missing_required_document_marks_incomplete() -> None:
    values = _base_field_values()

    _, record_status = reconcile(values, has_all_required_docs=False)

    assert record_status == "incomplete"


def test_derived_time_sequence_warning_is_emitted() -> None:
    values = _base_field_values()
    values["start_time"]["employee"] = "17:00"
    values["end_time"]["employee"] = "16:00"

    field_results, record_status = reconcile(values, has_all_required_docs=True)
    derived = [row for row in field_results if row.field_key == "derived_end_after_start_employee"]

    assert len(derived) == 1
    assert derived[0].status == "warning"
    assert record_status == "matched_with_warnings"


def test_derived_overtime_sanity_sets_exception() -> None:
    values = _base_field_values()
    values["overtime_hours"]["employee"] = "9.00"
    values["total_hours"]["employee"] = "8.00"

    field_results, record_status = reconcile(values, has_all_required_docs=True)
    derived = [row for row in field_results if row.field_key == "derived_overtime_sanity_employee"]

    assert len(derived) == 1
    assert derived[0].status == "mismatch"
    assert derived[0].severity == "critical"
    assert record_status == "exception"
