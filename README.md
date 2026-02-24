# Employee PDF Reconciliation MVP (Phase 1)

This repo contains the planning and build documents for a Phase 1 MVP that ingests 3 PDFs (Client, Work Order, Employee), extracts and compares key fields, supports review/approval, and files approved documents to SharePoint.

## Core Workflow
1. Upload 3 PDFs
2. Extract and normalize fields
3. Reconcile values across all 3 documents
4. Review/approve exceptions
5. File approved PDFs into client-specific SharePoint invoice folders

## What to Give Codex First
Start Codex with:
- `PROJECT_PLAN.md`
- `BUILD_SPEC.md`
- `FIELD_RULES_MATRIX.md`
- `TASKS.md`

## Suggested First Codex Prompt
Read `PROJECT_PLAN.md` and `BUILD_SPEC.md` first. Build a production-oriented Phase 1 MVP skeleton for local development with:
- backend API
- frontend review UI
- database models
- reconciliation engine v1
- test coverage for normalization/reconciliation
- mock implementations for PDF extraction and SharePoint upload

Then generate or update `TASKS.md` with the next implementation tasks in priority order.

## Suggested Repo Structure (for code)
```text
/
├── docs/
├── backend/
├── frontend/
├── shared/
├── tests/
├── samples/
└── infra/
```

## Notes
- Keep secrets in environment variables only
- Use mock/stub services first for OCR and SharePoint
- Build deterministic rules first; use AI only where needed
