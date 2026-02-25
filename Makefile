.PHONY: backend-install backend-migrate backend-run backend-test frontend-install frontend-run

backend-install:
	cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

backend-migrate:
	cd backend && . .venv/bin/activate && alembic upgrade head

backend-run:
	cd backend && . .venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

backend-test:
	cd backend && . .venv/bin/activate && PYTHONPATH=. pytest ../tests/backend -q

frontend-install:
	cd frontend && npm install

frontend-run:
	cd frontend && npm run dev
