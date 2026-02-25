# Employee PDF Reconciliation MVP (Phase 1)

Phase 1 MVP skeleton for local development:
- FastAPI backend (`/backend`)
- React + Vite review UI (`/frontend`)
- SQLAlchemy models + Alembic migration
- Reconciliation engine v1 with deterministic rules
- Mock PDF extraction service
- Mock SharePoint uploader
- Unit tests for normalization and reconciliation

## Architecture Snapshot

- `backend/app/api`: record, approval, mapping, and metrics endpoints
- `backend/app/services`: normalization, reconciliation, extraction stub, SharePoint stub
- `backend/app/db`: SQLAlchemy models and session
- `backend/alembic`: DB migration scripts
- `frontend/src`: queue + detail review UI
- `tests/backend`: pytest unit tests

## Environment Variables

Do not hardcode credentials. Copy and set from examples:

- Backend: `backend/.env.example`
- Frontend: `frontend/.env.example`

Important backend values:
- `DATABASE_URL` (defaults to local SQLite)
- `LOCAL_STORAGE_PATH` (where uploaded PDFs are stored)
- `SHAREPOINT_TENANT_ID`, `SHAREPOINT_CLIENT_ID`, `SHAREPOINT_CLIENT_SECRET`

## Local Setup

### 1) Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
```

### 2) Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

## MVP API Endpoints

Base path: `/api`

- `POST /api/records/upload`
- `POST /api/records/{record_id}/process`
- `GET /api/records`
- `GET /api/records/{record_id}`
- `POST /api/records/{record_id}/approve`
- `POST /api/records/{record_id}/approve-with-exceptions`
- `POST /api/records/{record_id}/reject`
- `POST /api/records/{record_id}/sharepoint-upload`
- `POST /api/records/{record_id}/sharepoint-retry`
- `GET /api/sharepoint-mappings`
- `POST /api/sharepoint-mappings`
- `PUT /api/sharepoint-mappings/{id}`
- `GET /api/metrics/summary`

## Running Tests

```bash
cd backend
source .venv/bin/activate
PYTHONPATH=. pytest ../tests/backend -q
```

Covered today:
- text/date/time/decimal/boolean normalization
- exact/fuzzy/tolerance/missing/incomplete reconciliation outcomes

## Notes and TODOs

- TODO: Replace `MockPdfExtractionService` with real PDF parsing + OCR fallback.
- TODO: Replace `MockSharePointUploader` with Microsoft Graph uploader using env credentials.
- Auth/infrastructure are intentionally minimal in this first iteration.
