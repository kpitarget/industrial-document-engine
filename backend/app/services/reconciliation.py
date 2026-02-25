from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from statistics import mean
from typing import Optional

from rapidfuzz.fuzz import ratio


DOC_TYPES = ["client", "work_order", "employee"]


FIELD_RULES: dict[str, dict[str, object]] = {
    "client_name": {
        "required": True,
        "compare": "fuzzy",
        "threshold": 0.90,
        "severity": "warning",
        "docs": ["client", "work_order"],
        "required_docs": ["client", "work_order"],
    },
    "client_id": {"required": False, "compare": "exact", "severity": "warning", "docs": ["client", "work_order"]},
    "work_order_number": {
        "required": True,
        "compare": "exact",
        "severity": "critical",
        "docs": ["client", "work_order", "employee"],
        "required_docs": ["client", "work_order", "employee"],
    },
    "employee_name": {
        "required": True,
        "compare": "fuzzy",
        "threshold": 0.90,
        "severity": "warning",
        "docs": ["client", "employee"],
        "required_docs": ["client", "employee"],
    },
    "employee_id": {
        "required": True,
        "compare": "exact",
        "severity": "critical",
        "docs": ["client", "work_order", "employee"],
        "required_docs": ["client", "employee"],
    },
    "location": {"required": False, "compare": "fuzzy", "threshold": 0.85, "severity": "warning", "docs": DOC_TYPES},
    "shift_date": {
        "required": True,
        "compare": "exact",
        "severity": "critical",
        "docs": DOC_TYPES,
        "required_docs": DOC_TYPES,
    },
    "start_time": {"required": False, "compare": "time_tolerance", "threshold": 15, "severity": "warning", "docs": DOC_TYPES},
    "end_time": {"required": False, "compare": "time_tolerance", "threshold": 15, "severity": "warning", "docs": DOC_TYPES},
    "total_hours": {
        "required": True,
        "compare": "numeric_tolerance",
        "threshold": 0.25,
        "severity": "critical",
        "docs": DOC_TYPES,
        "required_docs": DOC_TYPES,
    },
    "overtime_hours": {
        "required": False,
        "compare": "numeric_tolerance",
        "threshold": 0.25,
        "severity": "warning",
        "docs": DOC_TYPES,
    },
    "pay_rate": {"required": False, "compare": "info", "severity": "warning", "docs": ["employee"]},
    "bill_rate": {"required": False, "compare": "info", "severity": "warning", "docs": ["client", "work_order"]},
    "supervisor_name": {"required": False, "compare": "fuzzy", "threshold": 0.85, "severity": "warning", "docs": DOC_TYPES},
    "signature_present": {
        "required": True,
        "compare": "presence_true",
        "severity": "critical",
        "docs": ["employee"],
        "required_docs": ["employee"],
    },
}


@dataclass
class FieldResult:
    field_key: str
    status: str
    severity: str
    threshold: Optional[float]
    reason: Optional[str]
    values: dict[str, Optional[str]]
    normalized_values: dict[str, Optional[str]]


def _all_present(values: list[Optional[str]]) -> bool:
    return all(value not in (None, "") for value in values)


def _status_for_severity(severity: str) -> str:
    return "mismatch" if severity == "critical" else "warning"


def _parse_time_to_minutes(value: str) -> int:
    parsed = datetime.strptime(value, "%H:%M")
    return parsed.hour * 60 + parsed.minute


def _add_derived_validation_results(
    field_values: dict[str, dict[str, Optional[str]]],
    results: list[FieldResult],
) -> None:
    # DV-1: End time after start time (same-day assumption in MVP).
    for doc_type in DOC_TYPES:
        start_time = field_values.get("start_time", {}).get(doc_type)
        end_time = field_values.get("end_time", {}).get(doc_type)
        if not start_time or not end_time:
            continue

        try:
            start_minutes = _parse_time_to_minutes(start_time)
            end_minutes = _parse_time_to_minutes(end_time)
        except ValueError:
            continue

        if end_minutes <= start_minutes:
            results.append(
                FieldResult(
                    field_key=f"derived_end_after_start_{doc_type}",
                    status="warning",
                    severity="warning",
                    threshold=None,
                    reason="End time is not after start time",
                    values={doc_type: f"{start_time} -> {end_time}"},
                    normalized_values={doc_type: f"{start_time} -> {end_time}"},
                )
            )

    # DV-2: Total hours aligns with derived duration (warning if variance > 0.25).
    for doc_type in DOC_TYPES:
        start_time = field_values.get("start_time", {}).get(doc_type)
        end_time = field_values.get("end_time", {}).get(doc_type)
        total_hours = field_values.get("total_hours", {}).get(doc_type)
        if not start_time or not end_time or not total_hours:
            continue

        try:
            start_minutes = _parse_time_to_minutes(start_time)
            end_minutes = _parse_time_to_minutes(end_time)
            numeric_total_hours = float(total_hours)
        except (ValueError, TypeError):
            continue

        duration_hours = (end_minutes - start_minutes) / 60
        variance = abs(duration_hours - numeric_total_hours)
        if variance > 0.25:
            results.append(
                FieldResult(
                    field_key=f"derived_hours_alignment_{doc_type}",
                    status="warning",
                    severity="warning",
                    threshold=0.25,
                    reason="Derived duration differs from total_hours by more than 0.25",
                    values={doc_type: f"duration={duration_hours:.2f}, total_hours={numeric_total_hours:.2f}"},
                    normalized_values={doc_type: f"duration={duration_hours:.2f}, total_hours={numeric_total_hours:.2f}"},
                )
            )

    # DV-3: Overtime sanity check (critical if overtime > total_hours).
    for doc_type in DOC_TYPES:
        overtime_hours = field_values.get("overtime_hours", {}).get(doc_type)
        total_hours = field_values.get("total_hours", {}).get(doc_type)
        if not overtime_hours or not total_hours:
            continue
        try:
            overtime_numeric = float(overtime_hours)
            total_numeric = float(total_hours)
        except (ValueError, TypeError):
            continue

        if overtime_numeric > total_numeric:
            results.append(
                FieldResult(
                    field_key=f"derived_overtime_sanity_{doc_type}",
                    status="mismatch",
                    severity="critical",
                    threshold=None,
                    reason="overtime_hours exceeds total_hours",
                    values={doc_type: f"overtime={overtime_numeric:.2f}, total={total_numeric:.2f}"},
                    normalized_values={doc_type: f"overtime={overtime_numeric:.2f}, total={total_numeric:.2f}"},
                )
            )


def reconcile(field_values: dict[str, dict[str, Optional[str]]], has_all_required_docs: bool = True) -> tuple[list[FieldResult], str]:
    results: list[FieldResult] = []

    for field_key, rule in FIELD_RULES.items():
        normalized_values = {doc_type: field_values.get(field_key, {}).get(doc_type) for doc_type in DOC_TYPES}
        values = dict(normalized_values)
        relevant_docs = list(rule.get("docs", DOC_TYPES))
        required_docs = list(rule.get("required_docs", relevant_docs))
        present_values = [normalized_values.get(doc) for doc in relevant_docs if normalized_values.get(doc) is not None]
        required = bool(rule["required"])
        severity = str(rule["severity"])
        compare = str(rule["compare"])

        if required and not _all_present([normalized_values.get(doc) for doc in required_docs]):
            results.append(
                FieldResult(
                    field_key=field_key,
                    status="missing",
                    severity=severity,
                    threshold=float(rule.get("threshold")) if rule.get("threshold") else None,
                    reason="Missing required value from one or more documents",
                    values=values,
                    normalized_values=normalized_values,
                )
            )
            continue

        if not present_values:
            results.append(
                FieldResult(
                    field_key=field_key,
                    status="missing",
                    severity=severity,
                    threshold=float(rule.get("threshold")) if rule.get("threshold") else None,
                    reason="Field not present in uploaded documents",
                    values=values,
                    normalized_values=normalized_values,
                )
            )
            continue

        if compare == "info":
            results.append(
                FieldResult(
                    field_key=field_key,
                    status="match",
                    severity=severity,
                    threshold=None,
                    reason="Informational field in MVP",
                    values=values,
                    normalized_values=normalized_values,
                )
            )
            continue

        if compare == "exact":
            if len(set(present_values)) == 1:
                status = "match"
                reason = "Exact match"
            else:
                status = _status_for_severity(severity)
                reason = "Exact values do not match"
            results.append(
                FieldResult(
                    field_key=field_key,
                    status=status,
                    severity=severity,
                    threshold=None,
                    reason=reason,
                    values=values,
                    normalized_values=normalized_values,
                )
            )
            continue

        if compare == "fuzzy":
            threshold = float(rule["threshold"])
            if len(present_values) == 1:
                score = 1.0
            else:
                pair_scores = []
                for i, first in enumerate(present_values):
                    for second in present_values[i + 1 :]:
                        pair_scores.append(ratio(first, second) / 100)
                score = mean(pair_scores) if pair_scores else 1.0
            if score >= threshold:
                status = "match"
                reason = f"Similarity {score:.2f} meets threshold {threshold:.2f}"
            else:
                status = _status_for_severity(severity)
                reason = f"Similarity {score:.2f} below threshold {threshold:.2f}"
            results.append(
                FieldResult(
                    field_key=field_key,
                    status=status,
                    severity=severity,
                    threshold=threshold,
                    reason=reason,
                    values=values,
                    normalized_values=normalized_values,
                )
            )
            continue

        if compare == "numeric_tolerance":
            threshold = float(rule["threshold"])
            decimals = [float(value) for value in present_values]
            if max(decimals) - min(decimals) <= threshold:
                status = "match"
                reason = "Within numeric tolerance"
            else:
                status = _status_for_severity(severity)
                reason = "Variance exceeds tolerance"
            results.append(
                FieldResult(
                    field_key=field_key,
                    status=status,
                    severity=severity,
                    threshold=threshold,
                    reason=reason,
                    values=values,
                    normalized_values=normalized_values,
                )
            )
            continue

        if compare == "time_tolerance":
            threshold = float(rule["threshold"])
            minutes = [_parse_time_to_minutes(value) for value in present_values]
            if max(minutes) - min(minutes) <= threshold:
                status = "match"
                reason = "Within time tolerance"
            else:
                status = _status_for_severity(severity)
                reason = "Time variance exceeds tolerance"
            results.append(
                FieldResult(
                    field_key=field_key,
                    status=status,
                    severity=severity,
                    threshold=threshold,
                    reason=reason,
                    values=values,
                    normalized_values=normalized_values,
                )
            )
            continue

        if compare == "presence_true":
            employee_value = normalized_values.get("employee")
            if employee_value == "true":
                status = "match"
                reason = "Required signature is present"
            else:
                status = _status_for_severity(severity)
                reason = "Required signature is missing"
            results.append(
                FieldResult(
                    field_key=field_key,
                    status=status,
                    severity=severity,
                    threshold=None,
                    reason=reason,
                    values=values,
                    normalized_values=normalized_values,
                )
            )

    _add_derived_validation_results(field_values=field_values, results=results)
    record_status = resolve_record_status(results=results, has_all_required_docs=has_all_required_docs)
    return results, record_status


def resolve_record_status(results: list[FieldResult], has_all_required_docs: bool) -> str:
    if not has_all_required_docs:
        return "incomplete"

    has_exception = any(
        result.status in {"mismatch", "missing"} and result.severity == "critical" for result in results
    )
    if has_exception:
        return "exception"

    has_warnings = any(result.status == "warning" for result in results)
    if has_warnings:
        return "matched_with_warnings"

    return "matched"
