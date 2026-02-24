# IMPLEMENTATION_PROMPTS_FOR_CODEX.md
## Ready-to-Use Prompts for Codex

Use these prompts in sequence for best results.

---

## Prompt 1: Scaffold + Models + UI Skeleton
Read `PROJECT_PLAN.md`, `BUILD_SPEC.md`, `FIELD_RULES_MATRIX.md`, and `API_SPEC.md`.

Create a production-oriented Phase 1 MVP skeleton for local development with:
- backend API (FastAPI preferred)
- frontend review UI (React preferred)
- database models + migrations
- reconciliation engine v1 (real logic)
- mock PDF extraction service
- mock SharePoint uploader
- unit tests for normalization and reconciliation
- a clear `README.md` with setup steps

Constraints:
- use environment variables for secrets
- no hardcoded credentials
- keep modules small and readable
- include TODOs where OCR and real SharePoint integration will be added
- don’t over-engineer auth or infrastructure in the first iteration

At the end, update `TASKS.md` with the next 10 implementation tasks based on what you completed.

---

## Prompt 2: Implement Real Extraction Pipeline
Implement the real PDF extraction pipeline behind the existing interfaces.

Use the parser interfaces already created and add:
- PDF text extraction
- OCR fallback service integration interface
- template parsers for client/work order/employee PDFs
- parser versioning support
- extraction error handling and logging
- tests for sample input parsing where possible

Do not break the reconciliation API contract in `API_SPEC.md`.

---

## Prompt 3: Implement Real SharePoint Upload
Replace the mock SharePoint uploader with a real Microsoft Graph integration while preserving the same uploader interface.

Requirements:
- resolve destination from `sharepoint_mappings`
- upload only approved records
- apply filename convention from `BUILD_SPEC.md`
- log upload attempts, failures, and retries
- keep credentials/config in env vars
- add integration tests or testable adapter boundaries

---

## Prompt 4: QA Hardening Pass
Run a quality hardening pass on the codebase.

Please:
- improve error handling and validation
- add missing unit tests
- add integration tests for key APIs
- tighten type definitions
- clean up TODOs by categorizing them (Phase 1.5 vs Phase 2)
- update `README.md` and `TASKS.md`
