# BUILD_SPEC.md
## Employee PDF Reconciliation MVP - Phase 1 Build Spec

## Goal
Build a web application that ingests 3 PDFs (Client, Work Order, Employee), extracts key fields, reconciles them, supports review/approval, and files approved records into SharePoint client invoice folders.

## Implementation Philosophy
- **Rules-first, AI-assisted** (not AI-only)
- **Template-based extraction** for predictable reliability
- **Human review for exceptions**
- **Auditability and traceability** for all approvals and uploads

## Suggested Tech Stack (recommended, flexible)
### Backend
- Python + FastAPI
- SQLAlchemy (or SQLModel) + Alembic
- PostgreSQL (SQLite allowed for local prototype only)

### Frontend
- React + Vite (or Next.js)
- TypeScript preferred
- Minimal UI for queue/detail/approval workflow

### Storage / Integrations
- Local file storage for dev
- S3-compatible object storage optional for staging/prod
- SharePoint via Microsoft Graph API (stub first, then real integration)
- OCR provider behind a service interface (stub first)

### Testing
- Pytest (backend)
- Vitest/RTL (frontend optional for MVP)
- Unit tests required for normalization + reconciliation logic

---

## Core Entities (Data Model)
1. **Client**
2. **Record** (one reconciliation unit for a set of 3 documents)
3. **Document** (Client / Work Order / Employee PDF)
4. **ExtractedField** (field values extracted per document)
5. **ReconciliationResult** (field-by-field comparison output)
6. **Approval** (approval/rejection/override actions)
7. **SharePointMapping** (client → SharePoint folder mapping)
8. **AuditLog** (processing + system event logging)
9. **UploadBatch** (optional, useful for batch uploads)

---

## Required Fields to Extract and Compare
Use these canonical field keys in code:

- `client_name`
- `client_id` (optional)
- `work_order_number`
- `employee_name`
- `employee_id`
- `location`
- `shift_date`
- `start_time`
- `end_time`
- `total_hours`
- `overtime_hours`
- `pay_rate` (optional)
- `bill_rate` (optional)
- `supervisor_name`
- `signature_present`

### Source Tracking Requirement
For each extracted field, store:
- document type (client/work_order/employee)
- raw value
- normalized value
- confidence (optional in MVP but recommended)
- parser name/version
- extraction timestamp

---

## Match Rules (Phase 1 Defaults)
### Exact Match
- `work_order_number`
- `employee_id`
- `shift_date` (after normalization)

### Fuzzy Match
- `employee_name`
- `client_name`
- `location`
- `supervisor_name` (optional fuzzy threshold)

### Tolerance Match
- `total_hours` ±0.25
- `overtime_hours` ±0.25

### Conditional/Derived Checks
- `end_time` should be after `start_time` (same-day assumption in MVP)
- `total_hours` should approximately equal derived duration (if both times exist)
- `signature_present` required on employee doc (configurable)

---

## Record Status Rules
### Field-Level Status Values
- `match`
- `warning`
- `mismatch`
- `missing`

### Record-Level Status Values
- `matched`
- `matched_with_warnings`
- `exception`
- `incomplete`

### Approval Status Values
- `pending_review`
- `approved`
- `approved_with_exceptions`
- `rejected`

---

## MVP Screens (UI)
1. **Record Queue**
   - list of processed records
   - filters: status, client, date range
   - search by work order # / employee ID

2. **Record Detail / Comparison Screen**
   - side-by-side values by doc type
   - visual mismatch highlighting
   - source docs preview links (optional MVP)
   - processing log panel (optional MVP)

3. **Approval Action Panel**
   - approve
   - approve with exceptions
   - reject
   - add reviewer notes

4. **SharePoint Mapping Admin (Basic)**
   - list mappings
   - create/edit path for client
   - activate/deactivate mapping

---

## API Endpoints (MVP)
### Records / Intake
- `POST /api/records/upload`
- `POST /api/records/{record_id}/process`
- `GET /api/records`
- `GET /api/records/{record_id}`

### Review / Approval
- `POST /api/records/{record_id}/approve`
- `POST /api/records/{record_id}/approve-with-exceptions`
- `POST /api/records/{record_id}/reject`

### SharePoint Filing
- `POST /api/records/{record_id}/sharepoint-upload`
- `POST /api/records/{record_id}/sharepoint-retry`

### Admin / Mapping
- `GET /api/sharepoint-mappings`
- `POST /api/sharepoint-mappings`
- `PUT /api/sharepoint-mappings/{id}`

### Metrics
- `GET /api/metrics/summary`

---

## PDF Extraction Service Design (Important)
Codex should implement extraction using an interface so parsers are swappable.

### Suggested interfaces
- `DocumentClassifier` (manual tag in MVP, auto later)
- `PdfExtractor` (text extraction)
- `OcrService` (fallback for scanned/image PDFs)
- `TemplateParser` (per doc type and template version)
- `FieldNormalizer`
- `ReconciliationEngine`
- `SharePointUploader`

### MVP Implementation Notes
- Create **mock/stub** OCR and SharePoint implementations first
- Implement real integrations behind interfaces in later tasks
- Add parser versioning to handle template changes over time

---

## SharePoint Filing Rules (Phase 1)
### Upload Conditions
Only upload if `approval_status` is one of:
- `approved`
- `approved_with_exceptions`

### Path Resolution
Use `SharePointMapping` table keyed by normalized client name or client_id.

### Filename Convention
`[Client]_[WorkOrder]_[EmployeeID]_[ShiftDate]_[DocType].pdf`

Examples:
- `Acme_WO4412_E10352_2026-02-20_Client.pdf`
- `Acme_WO4412_E10352_2026-02-20_WorkOrder.pdf`
- `Acme_WO4412_E10352_2026-02-20_Employee.pdf`

### Upload Logging
Store:
- attempt timestamp
- destination path
- success/failure
- error message (if any)
- retry count

---

## Non-Functional Requirements
- Use environment variables for secrets and config
- No hardcoded credentials
- Structured logs (JSON preferred)
- Basic retry handling for upload failures
- Graceful error responses
- PII-safe logging (avoid dumping raw PDFs or sensitive values into logs)
- Basic role separation (admin vs reviewer) if auth is included in MVP
- Unit tests for normalization and reconciliation rules required

---

## Deliverables for Build Iteration 1 (Codex Task 1)
- Running backend skeleton
- Running frontend skeleton
- DB models + migrations
- API endpoint stubs
- Reconciliation engine v1 (real logic)
- Mock PDF extraction service
- Mock SharePoint upload service
- Basic queue + detail UI pages
- README setup instructions
- Unit tests for normalization + reconciliation

---

## Definition of Done (Iteration 1)
- App runs locally
- Can create a record and attach 3 placeholder docs
- Reconciliation endpoint returns field-level statuses
- Queue and detail pages render mock/real data
- Unit tests pass for matching rules
- TODO markers exist for OCR and real SharePoint integration

---

## Coding Standards / Guardrails for Codex
- Keep modules small and readable
- Prefer explicit names over abstractions
- Add comments only where logic is non-obvious
- Create TODOs for external integrations
- Write tests before/alongside rule engine changes
- Do not over-engineer auth or infrastructure in iteration 1
