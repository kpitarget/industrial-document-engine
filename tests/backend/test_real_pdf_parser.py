from __future__ import annotations

from app.services.parsing.real_pdf_parser import RuleBasedPdfParser


def test_ctk_parser_extracts_rows_and_common_fields() -> None:
    parser = RuleBasedPdfParser()
    text = """
MWIS REPRESENTATIVE
JOB NUMBER
10060
DATE
2/20/26
WO # 6203072
AREA / MILL LOCATION
Down coiler
MWIS WORKFORCE
CTK CLOCK IN
CTK CLOCK OUT
Judson Atchison
7:00 AM
11:45 Am
Michael Thompson
7:00 AM
1:08 pm
Jaime Robinson
7:00 AM
1:08 pM
OWNER REPRESENTATIVE - NAME & TITLE
"""

    parsed = parser.parse(doc_type="work_order", filename="ctk sheet.pdf", extracted_text=text)

    assert parsed.fields["work_order_number"] == "10060"
    assert parsed.fields["shift_date"] == "2026-02-20"
    assert parsed.fields["location"] == "DOWN COILER"
    assert len(parsed.rows) == 3
    assert parsed.rows[0].fields["employee_name"] == "Judson Atchison"
    assert parsed.rows[0].fields["start_time"] == "07:00"
    assert parsed.rows[0].fields["end_time"] == "11:45"


def test_daily_report_parser_reads_workforce_section() -> None:
    parser = RuleBasedPdfParser()
    text = """
JOB NUMBER
10060
DATE
2/20/26
WO# 6203072
MWIS WORKFORCE
Judson Atchison
7:00 AM
12:13 PM
Michael Thompson
7:00 AM
1:30 PM
DESCRIPTION OF WORK PERFORMED TODAY
"""

    parsed = parser.parse(doc_type="client", filename="daily report.pdf", extracted_text=text)

    assert parsed.fields["work_order_number"] == "10060"
    assert parsed.fields["shift_date"] == "2026-02-20"
    assert len(parsed.rows) == 2
    assert parsed.rows[1].fields["employee_name"] == "Michael Thompson"


def test_jsa_parser_extracts_names_and_signature() -> None:
    parser = RuleBasedPdfParser()
    text = """
DATE
2/20/26
JOB #
10060
1. Judson Atchison
2. Michael Thompson
3. James Corley
Task Steps
Foreman:
Howard Queen
Signing this Form Indicates that you have Reviewed and Understand the Job Tasks, Hazards and Mitigations.
"""

    parsed = parser.parse(doc_type="employee", filename="daily jsa-1.pdf", extracted_text=text)

    assert parsed.fields["work_order_number"] == "10060"
    assert parsed.fields["shift_date"] == "2026-02-20"
    assert parsed.fields["signature_present"] == "true"
    assert parsed.fields["supervisor_name"] == "Howard Queen"
    assert len(parsed.rows) == 3
    assert parsed.rows[0].fields["employee_name"] == "Judson Atchison"
