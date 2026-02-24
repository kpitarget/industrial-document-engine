# FIELD_RULES_MATRIX.md
## Phase 1 Field Extraction + Reconciliation Rules Matrix

Use this as the source of truth for extraction fields, normalization, comparison logic, and exception handling.

## Legend
- **Doc Sources:** C = Client PDF, W = Work Order PDF, E = Employee PDF
- **Compare Type:** exact / fuzzy / tolerance / presence / derived
- **Severity:** critical / warning
- **Required:** Y / N
- **Phase 1 Action:** auto-pass / warn / exception

---

## Field Matrix

| Canonical Field | Sources | Required | Normalize | Compare Type | Rule / Threshold | Severity | Phase 1 Action |
|---|---|---:|---|---|---|---|---|
| `client_name` | C,W | Y | trim, case, punctuation | fuzzy | similarity >= 0.90 | warning | warn |
| `client_id` | C,W | N | trim | exact | exact if present in both | warning | warn |
| `work_order_number` | C,W,E | Y | trim, uppercase | exact | exact match across all present values | critical | exception |
| `employee_name` | C,E | Y | trim, case, punctuation | fuzzy | similarity >= 0.90 | warning | warn |
| `employee_id` | C,E,W (if present) | Y | trim, uppercase | exact | exact match | critical | exception |
| `location` | C,W,E | N | trim, standard abbreviations | fuzzy | similarity >= 0.85 | warning | warn |
| `shift_date` | C,W,E | Y | convert to YYYY-MM-DD | exact | exact after normalization | critical | exception |
| `start_time` | C,W,E | N | convert to 24h | tolerance | +/- 15 minutes | warning | warn |
| `end_time` | C,W,E | N | convert to 24h | tolerance | +/- 15 minutes | warning | warn |
| `total_hours` | C,W,E | Y | numeric decimal | tolerance | +/- 0.25 hours | critical | exception |
| `overtime_hours` | C,W,E | N | numeric decimal | tolerance | +/- 0.25 hours | warning | warn |
| `pay_rate` | E | N | currency to decimal | exact | informational in MVP | warning | auto-pass |
| `bill_rate` | C/W | N | currency to decimal | exact | informational in MVP | warning | auto-pass |
| `supervisor_name` | C,W,E | N | trim, case, punctuation | fuzzy | similarity >= 0.85 | warning | warn |
| `signature_present` | E | Y | boolean | presence | must be true | critical | exception |

---

## Normalization Rules (Phase 1)

### Text normalization
Apply to name/location text fields:
- trim whitespace
- collapse repeated spaces
- uppercase for comparison key (keep original for display)
- remove punctuation for fuzzy compare key
- optional alias mapping (Phase 2): `MIKE` ↔ `MICHAEL`

### Date normalization
Convert all recognized formats to `YYYY-MM-DD`, including:
- `MM/DD/YY`
- `MM/DD/YYYY`
- `YYYY-MM-DD`
- `Month DD, YYYY`

If date cannot be parsed:
- field status = `missing` or `mismatch`
- create extraction/parsing error log entry

### Time normalization
Convert to a consistent 24-hour time representation (e.g., `HH:MM`).

Handle:
- `8:00 AM`
- `08:00`
- `8AM`
- `0800`

If one source omits AM/PM and ambiguity exists:
- flag `warning` (or `mismatch` if impossible to infer)

### Numeric normalization
Convert hours and rates to decimal:
- `8`, `8.0`, `8.00` → `8.00`
- remove commas and currency symbols
- preserve 2 decimals for display

---

## Derived Validation Rules (Phase 1)
These are secondary checks used for warnings/exceptions.

### DV-1: End time after start time
If both `start_time` and `end_time` exist on a document:
- compute duration
- if negative/invalid, flag warning (or exception if business requires)

### DV-2: Total hours aligns with time duration
If `start_time`, `end_time`, and `total_hours` exist:
- compare derived duration to `total_hours`
- if variance > 0.25 hours, flag warning

### DV-3: Overtime sanity check
If `overtime_hours` > `total_hours`, flag exception

### DV-4: Signature requirement
If employee PDF `signature_present` = false, flag exception

---

## Record Status Resolution Logic (Phase 1)
Use the following priority order:
1. **incomplete** — one or more required docs missing
2. **exception** — any critical field mismatch / missing required field / required signature absent
3. **matched_with_warnings** — no critical exceptions, but one or more warnings
4. **matched** — all required checks passed and no warnings

---

## Fuzzy Matching Guidance (Implementation)
### Recommended approach
- Normalize string first
- Use a string similarity metric (e.g., token sort ratio / Levenshtein)
- Store both:
  - score (0.00–1.00)
  - threshold used

### MVP thresholds
- names: `0.90`
- location/supervisor: `0.85`

If score is within 0.05 of threshold:
- mark as warning and include score for reviewer visibility

---

## Missing Data Rules
### Missing Required Field
If required field missing from any required source:
- field status = `missing`
- severity = critical
- record status likely `exception`

### Missing Optional Field
- field status = `missing`
- severity = warning
- do not block approval by default

---

## Override Rules (Reviewer)
Reviewers may:
- approve a record with warnings
- approve a record with exceptions (if business permits, using `approved_with_exceptions`)
- reject a record and add notes

Reviewer actions must create an audit log entry with:
- user
- timestamp
- prior status
- new status
- notes

---

## Open Questions to Confirm with Client (Before Build)
1. Is `work_order_number` present on all 3 PDFs?
2. Is `employee_id` available on all documents, or only some?
3. What are approved tolerances for start/end time differences?
4. Are overnight shifts in scope for Phase 1?
5. Is signature detection a checkbox/text field or image/signature line presence?
6. Should missing optional fields block approval for any specific client?
