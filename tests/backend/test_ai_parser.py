from __future__ import annotations

from app.services.parsing.ai_parser import OpenAIDocumentParser


def test_ai_parser_returns_none_when_disabled() -> None:
    parser = OpenAIDocumentParser(api_key=None)
    parsed = parser.parse(doc_type="client", filename="daily report.pdf", extracted_text="some text")
    assert parsed is None


def test_ai_parser_coerces_fields_and_rows(monkeypatch) -> None:
    parser = OpenAIDocumentParser(api_key="test-key", model="gpt-test")

    fake_response = {
        "choices": [
            {
                "message": {
                    "content": """
{
  "fields": {
    "client_name": "MWIS",
    "work_order_number": "10060",
    "shift_date": "2026-02-20"
  },
  "rows": [
    {
      "row_index": 0,
      "fields": {
        "employee_name": "Judson Atchison",
        "start_time": "07:00",
        "end_time": "11:45",
        "work_order_number": "10060"
      }
    }
  ]
}
"""
                }
            }
        ]
    }

    monkeypatch.setattr(parser, "_call_openai", lambda payload: fake_response)
    parsed = parser.parse(doc_type="work_order", filename="ctk sheet.pdf", extracted_text="ocr text")

    assert parsed is not None
    assert parsed.parser_name == "openai_structured_parser"
    assert parsed.fields["client_name"] == "MWIS"
    assert parsed.fields["work_order_number"] == "10060"
    assert parsed.fields["shift_date"] == "2026-02-20"
    assert len(parsed.rows) == 1
    assert parsed.rows[0].fields["employee_name"] == "Judson Atchison"


def test_ai_parser_rejects_invalid_schema_when_rows_missing(monkeypatch) -> None:
    parser = OpenAIDocumentParser(api_key="test-key", model="gpt-test")
    fake_response = {
        "choices": [
            {
                "message": {
                    "content": """
{
  "fields": {
    "client_name": "MWIS"
  }
}
"""
                }
            }
        ]
    }

    monkeypatch.setattr(parser, "_call_openai", lambda payload: fake_response)
    parsed = parser.parse(doc_type="client", filename="daily report.pdf", extracted_text="ocr text")
    assert parsed is None


def test_ai_parser_rejects_invalid_schema_for_nested_field_values(monkeypatch) -> None:
    parser = OpenAIDocumentParser(api_key="test-key", model="gpt-test")
    fake_response = {
        "choices": [
            {
                "message": {
                    "content": """
{
  "fields": {
    "client_name": {"value": "MWIS"}
  },
  "rows": []
}
"""
                }
            }
        ]
    }

    monkeypatch.setattr(parser, "_call_openai", lambda payload: fake_response)
    parsed = parser.parse(doc_type="client", filename="daily report.pdf", extracted_text="ocr text")
    assert parsed is None


def test_ai_parser_rejects_invalid_row_index_type(monkeypatch) -> None:
    parser = OpenAIDocumentParser(api_key="test-key", model="gpt-test")
    fake_response = {
        "choices": [
            {
                "message": {
                    "content": """
{
  "fields": {
    "client_name": "MWIS"
  },
  "rows": [
    {
      "row_index": "zero",
      "fields": {"employee_name": "Judson Atchison"}
    }
  ]
}
"""
                }
            }
        ]
    }

    monkeypatch.setattr(parser, "_call_openai", lambda payload: fake_response)
    parsed = parser.parse(doc_type="work_order", filename="ctk sheet.pdf", extracted_text="ocr text")
    assert parsed is None
