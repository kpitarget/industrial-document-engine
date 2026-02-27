# Product Hardening Task Board

## Completed In This Cycle
- Added strict JSON schema validation for AI parser responses (top-level shape, row shape, and scalar field values).
- Added AI parser tests for malformed payload rejection scenarios.
- Added OpenAI-backed structured extraction parser (`OpenAIDocumentParser`) for OCR text.
- Wired extraction flow to prefer AI parsing when `OPENAI_API_KEY` is configured.
- Added parser merge strategy: AI output is used first, rule-based parser fills gaps, mock parser remains final fallback.
- Added backend config/env support for AI extraction model selection (`OPENAI_EXTRACTION_MODEL`).
- Added unit tests for AI parser behavior without external API calls.
- Updated README and backend `.env.example` with AI extraction setup instructions.
- Implemented a real OCR-backed parser path for local macOS development using native Vision OCR (`swift` + `PDFKit` + `Vision`).
- Added reusable OCR script at `backend/app/services/parsing/macos_vision_ocr.swift` and Python wrapper extractor.
- Added rules-based document parser (`RuleBasedPdfParser`) for:
  - Daily Report parsing
  - CTK sheet parsing
  - Daily JSA parsing
- Added extraction heuristics for job/work-order, shift date, location, workforce names, and clock-in/out times.
- Added row derivation from parsed workforce sections so multi-employee rows are generated from OCR text.
- Switched processing flow to pass `storage_path` into parsing so extraction uses actual uploaded PDFs when possible.
- Kept deterministic mock extraction fallback for non-macOS or OCR failures to preserve MVP reliability.
- Added unit tests for real parser rules (`tests/backend/test_real_pdf_parser.py`).
- Verified full backend test suite passes after parser integration (`26 passed`).
- Added row-matching data foundation: `document_batches`, `extracted_rows`, and `row_match_groups` models + Alembic migration.
- Added `records.batch_id` linkage so records can be grouped under a shared document batch key.
- Added parser contracts (`ParsedDocument`, `ExtractedEmployeeRow`, `DocumentParser`) to support row-level extraction outputs.
- Extended mock extraction service to emit multi-employee rows for sheet-like filenames (`daily`, `jsa`, `ctk`, `timesheet`, etc.).
- Implemented deterministic row matcher v1 with statuses: `matched`, `partial`, `conflict`, `insufficient_data`.
- Integrated row extraction and row-match persistence into `POST /api/records/{record_id}/process` while preserving existing field-level reconciliation behavior.
- Updated upload flow to create/reuse `DocumentBatch` via `record_group_key` without changing API contract.
- Added backend unit tests for row keying and row match grouping behavior.
- Verified migration applies cleanly on SQLite (`alembic upgrade head` against a clean test DB).
- Verified backend regression suite passes after changes (`23 passed`).
- Added consistent API error envelope (`code`, `message`, `details`) via global FastAPI exception handlers.
- Added upload validation for empty uploads, non-PDF files, unsupported content type, and max file size.
- Improved queue/detail frontend error messaging to surface backend error messages.
- Improved record detail UX to show document list, audit timeline, and reconciliation rule details.
- Added integration tests for upload validation and API error responses.
- Implemented derived validation rules DV-1, DV-2, and DV-3 in reconciliation output.
- Added API query filter support for `client_id`, `date_from`, and `date_to` on `GET /api/records`.
- Added tests for derived validation behavior and new list-filter query behavior.
- Reset frontend UX foundation with a consistent design system (spacing, typography, color roles, cards, tables, badges, buttons).
- Redesigned Record Queue into a polished operations dashboard layout with summary cards, improved filter area, and production-style records table.
- Redesigned Record Detail into a structured review workspace with metadata header, comparison grid, audit timeline, and dedicated approval action panel.
- Added reusable UI primitives (`Button`, `Card`, `StateBlock`, `SummaryCard`) for consistent future UX iteration.
- Added clean loading, empty, and error states on both Queue and Detail pages.
- Reworked Record Detail layout to a non-overlapping top action-bar pattern with comparison-first flow.
- Added reusable `ApprovalActionsBar` component to keep approval UX consistent and safer.
- Enforced single-column app shell layout to eliminate cross-panel overlap risk.

## Next Priority Tasks
1. Add robust prompt+schema hardening for AI parser outputs (strict JSON schema validation + retry on malformed output).
2. Add parser confidence scoring per extracted row/field and persist confidence in `extracted_rows`.
3. Add document template profile detection (`daily_report_v1`, `ctk_v1`, `jsa_v1`) with explicit parser selection metrics.
4. Add OCR post-processing cleanup dictionary for common operator names to improve cross-doc row matching.
5. Add row-level API payload in record detail so frontend can review parsed workforce rows and match groups directly.
6. Add frontend row review panel with unresolved/missing employee row triage workflow.
7. Add API endpoint to preview OCR text snippets for parser debugging (admin/dev only).
8. Add integration tests using fixture OCR text snapshots to guard parser regressions per document template.
9. Add extraction fallback pipeline for non-macOS environments (Tesseract or cloud OCR adapter behind interface).
10. Add a parser diagnostics report in UI (which parser ran, OCR availability, rows found, key missing fields).

## Known Issues
- Backend currently runs on Python 3.9 in this environment; code has compatibility adjustments, but project should target Python 3.11+ in production.
- Upload endpoint still uses fixed multipart field names; generic array + `doc_type` payload is not implemented yet.
- SharePoint and OCR remain mock implementations by design for Phase 1.
- `client_id` filtering currently reads from persisted extracted fields, which assumes records have been processed before filtering.
- Row matching is currently deterministic and key-based; it does not yet perform fuzzy cross-document row alignment when key fields are missing.
- macOS Vision OCR parser is currently local-only; non-macOS environments still rely on mock fallback.
- JSA sheet OCR quality is noisier than CTK/Daily Report and may require fuzzy matching + name-cleanup tuning for stable multi-doc alignment.
