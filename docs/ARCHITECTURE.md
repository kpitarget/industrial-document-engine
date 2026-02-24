# ARCHITECTURE.md
## Phase 1 MVP Technical Architecture (Practical)

## Overview
This MVP should be built with a clean separation between:
1. intake/upload
2. extraction
3. normalization/reconciliation
4. review/approval
5. SharePoint filing

Keep interfaces stable so real OCR and SharePoint can be added without rewriting core logic.

---

## Recommended Components

### 1) Web Frontend
- Queue view
- Record detail comparison
- Approval actions
- SharePoint mapping admin (basic)

### 2) API Backend
- Upload endpoints
- Processing endpoints
- Record query endpoints
- Approval endpoints
- SharePoint endpoints
- Metrics endpoints

### 3) Data Store (PostgreSQL)
Stores:
- records
- documents
- extracted fields
- reconciliation results
- approvals
- mappings
- audit logs

### 4) File Storage
- Dev: local filesystem
- Prod: object storage (optional) or secure file share

### 5) Extraction Subsystem
Interfaces:
- PDF text extractor
- OCR fallback
- Template parsers
- Normalizers

### 6) Reconciliation Engine
Pure deterministic logic where possible.
This should be testable independently.

### 7) SharePoint Integration Adapter
Abstraction over Microsoft Graph.
Start with mock adapter in dev.

---

## Processing Sequence (Phase 1)
1. User uploads 3 PDFs
2. Backend creates `record` and `document` entries
3. User (or system) triggers processing
4. Extraction service parses each PDF into canonical fields
5. Normalizer standardizes values
6. Reconciliation engine compares field values
7. Results stored for UI review
8. Reviewer approves/rejects
9. Approved record triggers SharePoint upload
10. Upload action logged to audit trail

---

## Service Interface Pattern (Important)
Codex should use interfaces (or protocol classes) for:
- `ExtractionService`
- `ParserRegistry`
- `NormalizationService`
- `ReconciliationEngine`
- `SharePointUploader`

### Why
This prevents hard dependencies and makes Phase 2 much easier.

---

## Suggested Backend Module Layout
```text
backend/app/
  api/
    routes_records.py
    routes_approvals.py
    routes_sharepoint.py
    routes_metrics.py
  models/
  schemas/
  services/
    extraction/
      extractor_interface.py
      pdf_text_extractor.py
      ocr_service_interface.py
      parser_registry.py
      parsers/
        client_parser_v1.py
        work_order_parser_v1.py
        employee_parser_v1.py
    normalization/
      normalizers.py
    reconciliation/
      engine.py
      rules.py
    sharepoint/
      uploader_interface.py
      mock_uploader.py
      graph_uploader.py   # TODO later
  db/
  tests/
```

---

## Suggested Frontend Module Layout
```text
frontend/src/
  pages/
    QueuePage.tsx
    RecordDetailPage.tsx
    MappingAdminPage.tsx
  components/
    RecordTable.tsx
    ComparisonGrid.tsx
    StatusBadge.tsx
    ApprovalPanel.tsx
  api/
    client.ts
  types/
```

---

## Data Design Notes
### `records`
Represents one reconciliation set, not one document.

### `documents`
Each uploaded PDF is a child document with `doc_type`:
- `client`
- `work_order`
- `employee`

### `extracted_fields`
One row per field per document (normalized + raw values).

### `reconciliation_results`
Can store either:
- one row per field comparison
- or a JSON blob summary (simpler MVP)
Prefer rows for reporting, JSON for speed. Hybrid is okay.

---

## Logging Strategy
### Audit Logs (business events)
- record created
- processing started/completed
- approval action
- upload attempted/success/failed
- mapping changed

### App Logs (technical events)
- parser errors
- normalization errors
- upload exceptions
- unexpected API errors

Avoid raw PDF content in logs.

---

## MVP Design Tradeoffs (Intentional)
- Manual doc type tagging (faster, safer than auto-classification)
- Stub OCR and SharePoint initially (lets team build UI + logic now)
- Simple role model (admin/reviewer) instead of full IAM
- Basic dashboard instead of full analytics suite

These are good Phase 1 choices and reduce risk.
