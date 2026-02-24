# SAMPLE_DATA_README.md
## Sample Documents for Development and Testing

Place redacted PDFs here for parser development and UAT.

## Folder Structure (Suggested)
```text
samples/
  client/
  work_order/
  employee/
  complete_sets/
```

## Naming Convention (Suggested)
For complete sets:
- `SET001_client.pdf`
- `SET001_work_order.pdf`
- `SET001_employee.pdf`

## Include Variety
Please include examples of:
- clean digital PDFs
- scanned PDFs (if applicable)
- slight layout variations
- known mismatches (hours, names, dates)
- missing fields
- missing signatures (if applicable)

## Redaction Guidance
Remove or mask sensitive information before sharing:
- SSNs
- personal addresses
- direct bank/payroll data
- any non-essential PII

## What Helps the Build Most
For each set, add a small note file (optional):
- expected match/mismatch result
- known issues in the source docs
- template version if known
