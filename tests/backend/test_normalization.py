from app.services.normalization import (
    normalize_boolean,
    normalize_date,
    normalize_decimal,
    normalize_identifier,
    normalize_text,
    normalize_time,
)


def test_normalize_text_removes_punctuation_and_case() -> None:
    assert normalize_text("  Mike, Rowan ") == "MIKE ROWAN"


def test_normalize_identifier_strips_spaces_and_uppercases() -> None:
    assert normalize_identifier(" e10 352 ") == "E10352"


def test_normalize_date_handles_multiple_formats() -> None:
    assert normalize_date("02/20/2026") == "2026-02-20"
    assert normalize_date("February 20, 2026") == "2026-02-20"


def test_normalize_time_handles_12h_and_compact() -> None:
    assert normalize_time("8:00 AM") == "08:00"
    assert normalize_time("0800") == "08:00"


def test_normalize_decimal_handles_currency() -> None:
    assert normalize_decimal("$1,200.5") == "1200.50"


def test_normalize_boolean_maps_truthy_values() -> None:
    assert normalize_boolean("yes") == "true"
    assert normalize_boolean("no") == "false"
