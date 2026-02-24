# TASKS.md
## Initial Build Backlog for Codex (Priority Order)

This is the recommended execution order for Phase 1 MVP.

---

## 1) Repo Scaffolding and Local Setup
**Goal:** Create runnable backend + frontend skeleton.

### Tasks
- Create backend project scaffold (FastAPI preferred)
- Create frontend scaffold (React + Vite preferred)
- Add `.env.example` files
- Add root `Makefile` or npm scripts for local startup
- Add pre-commit/lint/test scripts (lightweight)

### Done when
- Both apps run locally
- Health check endpoint responds
- Frontend loads

---

## 2) Database Models and Migrations
**Goal:** Define core schema for MVP.

### Tasks
- Create models:
  - clients
  - records
  - documents
  - extracted_fields
  - reconciliation_results
  - approvals
  - sharepoint_mappings
  - audit_logs
- Add migrations
- Seed minimal test data (1–2 clients)

### Done when
- DB migrates successfully
- Tables visible
- Seed script runs

---

## 3) File Upload and Record Creation Flow
**Goal:** Accept and store 3 PDFs per record.

### Tasks
- `POST /api/records/upload`
- Support doc type tags (client / work_order / employee)
- Save files to local storage path
- Create record + document rows
- Return record_id + status

### Done when
- Placeholder PDFs can be uploaded
- Record and document metadata persist

---

## 4) Mock Extraction Service and Parser Interfaces
**Goal:** Create extraction architecture without real OCR yet.

### Tasks
- Create `PdfExtractor` interface
- Create `OcrService` interface (stub)
- Create `TemplateParser` interface
- Implement mock parser returning sample extracted fields
- Save extracted fields to DB

### Done when
- Processing endpoint can populate `extracted_fields` with mock data

---

## 5) Normalization Library
**Goal:** Standardize field values for comparison.

### Tasks
- Build text normalizer
- Build date normalizer
- Build time normalizer
- Build numeric/currency normalizer
- Unit tests for normalizers

### Done when
- Tests cover common input variants from field matrix

---

## 6) Reconciliation Engine v1
**Goal:** Compare fields across the 3 documents using rule matrix.

### Tasks
- Implement exact/fuzzy/tolerance comparisons
- Generate field-level statuses and reasons
- Compute record-level status
- Store reconciliation results
- Add unit tests for:
  - exact mismatch
  - fuzzy warning
  - tolerance pass/fail
  - missing required field
  - incomplete record

### Done when
- `POST /api/records/{id}/process` returns deterministic comparison output

---

## 7) Record Queue API + UI
**Goal:** View records awaiting review.

### Tasks
- `GET /api/records` with filters
- Frontend queue page
- Status chips / badges
- Search by employee ID and work order #

### Done when
- Reviewer can see records and filter by status

---

## 8) Record Detail Comparison UI
**Goal:** Review field-by-field comparison.

### Tasks
- `GET /api/records/{id}` detail endpoint
- Build side-by-side comparison grid
- Highlight mismatches/warnings
- Display source values by doc type
- Show audit history (if available)

### Done when
- Reviewer can inspect a record clearly and identify mismatches

---

## 9) Approval Workflow API + UI
**Goal:** Allow reviewer decisions and notes.

### Tasks
- Approve endpoint
- Approve-with-exceptions endpoint
- Reject endpoint
- Add reviewer notes field
- Persist approval + audit logs
- UI action panel with confirmation

### Done when
- Approval actions update status and create audit logs

---

## 10) SharePoint Mapping and Mock Upload
**Goal:** Close the loop after approval.

### Tasks
- CRUD endpoints for `sharepoint_mappings`
- Basic admin UI for mappings
- Mock `SharePointUploader` service
- Filename generation utility
- Upload attempt logging
- Retry endpoint

### Done when
- Approved records can trigger mock upload and log destination path

---

## 11) Metrics Summary Endpoint + Dashboard Cards
**Goal:** Provide basic operational visibility.

### Tasks
- `GET /api/metrics/summary`
- Add dashboard cards:
  - processed
  - matched
  - exceptions
  - approved
  - upload failures

### Done when
- Metrics appear on queue/dashboard view

---

## 12) Real PDF Extraction (Phase 1.5 / Next)
**Goal:** Replace mock extractor with real parser pipeline.

### Tasks
- Add PDF text extraction implementation
- Add OCR fallback implementation
- Add template parser for each doc type
- Add parser versioning
- Tune against sample PDFs

### Done when
- Real sample records process end-to-end with acceptable accuracy

---

## 13) Real SharePoint Integration (Phase 1.5 / Next)
**Goal:** Replace mock upload with Microsoft Graph upload.

### Tasks
- Implement auth flow / app credentials
- Resolve site/library/folder path
- Upload approved files
- Capture file IDs / links (optional)
- Retry and error handling

### Done when
- Approved docs upload to real SharePoint test folder

---

## 14) QA, UAT, and Production Hardening
**Goal:** Prepare for launch.

### Tasks
- End-to-end tests
- Error handling polish
- Logging and monitoring checks
- UAT issue fixes
- SOP/admin guide updates

### Done when
- UAT signoff complete
- Launch checklist complete

---

## Notes for Codex
- Keep commits/checkpoints small
- Prefer stubs over blocked progress
- Add TODOs where real integrations will replace mocks
- Follow `FIELD_RULES_MATRIX.md` and `BUILD_SPEC.md` as source of truth
