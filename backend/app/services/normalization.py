from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

from dateutil import parser


def normalize_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = re.sub(r"\s+", " ", value.strip())
    cleaned = re.sub(r"[^\w\s]", "", cleaned)
    return cleaned.upper() if cleaned else None


def normalize_identifier(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = re.sub(r"\s+", "", value.strip().upper())
    return cleaned or None


def normalize_date(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    try:
        parsed = parser.parse(text, dayfirst=False, fuzzy=True)
        return parsed.date().isoformat()
    except (ValueError, TypeError, OverflowError):
        return None


def normalize_time(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    text = value.strip().upper().replace(".", "")
    if not text:
        return None

    compact_match = re.fullmatch(r"(\d{1,2})(\d{2})", text)
    if compact_match:
        hours = int(compact_match.group(1))
        minutes = int(compact_match.group(2))
        if 0 <= hours <= 23 and 0 <= minutes <= 59:
            return f"{hours:02d}:{minutes:02d}"

    for fmt in ("%I:%M %p", "%I%p", "%H:%M", "%H%M"):
        try:
            return datetime.strptime(text, fmt).strftime("%H:%M")
        except ValueError:
            continue

    try:
        return parser.parse(text).strftime("%H:%M")
    except (ValueError, TypeError, OverflowError):
        return None


def normalize_decimal(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = re.sub(r"[^0-9.\-]", "", value.strip())
    if not cleaned:
        return None
    try:
        number = Decimal(cleaned)
    except InvalidOperation:
        return None
    return f"{number:.2f}"


def normalize_boolean(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    truthy = {"Y", "YES", "TRUE", "1", "PRESENT", "SIGNED"}
    falsy = {"N", "NO", "FALSE", "0", "MISSING", "UNSIGNED"}
    upper_value = value.strip().upper()
    if upper_value in truthy:
        return "true"
    if upper_value in falsy:
        return "false"
    return None


def normalize_value(field_key: str, raw_value: Optional[str]) -> Optional[str]:
    if field_key in {"client_name", "employee_name", "location", "supervisor_name"}:
        return normalize_text(raw_value)
    if field_key in {"work_order_number", "employee_id", "client_id"}:
        return normalize_identifier(raw_value)
    if field_key == "shift_date":
        return normalize_date(raw_value)
    if field_key in {"start_time", "end_time"}:
        return normalize_time(raw_value)
    if field_key in {"total_hours", "overtime_hours", "pay_rate", "bill_rate"}:
        return normalize_decimal(raw_value)
    if field_key == "signature_present":
        return normalize_boolean(raw_value)
    return raw_value.strip() if raw_value else None
