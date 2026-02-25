# Product Hardening Task Board

## Completed In This Cycle
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
1. Add keyboard-first triage shortcuts (next/previous record, approve, reject, focus search).
2. Add queue table column sorting controls (shift date, record status, work order, approval).
3. Add compact quick-filter chips for common views (Exceptions, Pending Review, Approved Today).
4. Add mismatch row highlighting in comparison grid with stronger visual emphasis and icon legend.
5. Add inline field search/filter inside Comparison Grid for large records.
6. Add persistent scroll position + selected row memory when switching between queue and detail.
7. Add toast notifications for upload/process/approval outcomes with accessible live regions.
8. Add a reusable empty-state illustration style pack for queue/detail/error states.
9. Add frontend visual regression tests/snapshots for key dashboard screens.
10. Add print/export-friendly CSS mode for sharing record detail reviews.

## Known Issues
- Backend currently runs on Python 3.9 in this environment; code has compatibility adjustments, but project should target Python 3.11+ in production.
- Upload endpoint still uses fixed multipart field names; generic array + `doc_type` payload is not implemented yet.
- SharePoint and OCR remain mock implementations by design for Phase 1.
- `client_id` filtering currently reads from persisted extracted fields, which assumes records have been processed before filtering.
