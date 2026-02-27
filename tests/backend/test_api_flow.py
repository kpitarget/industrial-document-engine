from __future__ import annotations

import os
import shutil
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import func, select

# Use test-specific local resources for this integration test.
os.environ["DATABASE_URL"] = "sqlite:///./test_mvp.db"
os.environ["LOCAL_STORAGE_PATH"] = "./test_storage"

from app.db.base import Base
from app.db.models import DocumentBatch, ExtractedField, ExtractedRow, ReconciliationResult, Record, RowMatchGroup
from app.db.session import SessionLocal, engine
from app.main import app


client = TestClient(app)


def setup_module() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_module() -> None:
    Base.metadata.drop_all(bind=engine)
    test_db = Path("test_mvp.db")
    if test_db.exists():
        test_db.unlink()
    test_storage = Path("test_storage")
    if test_storage.exists():
        shutil.rmtree(test_storage)


def test_upload_process_persists_reconciliation_results() -> None:
    files = {
        "client_document": ("client.pdf", b"%PDF-1.4 client", "application/pdf"),
        "work_order_document": ("work_order.pdf", b"%PDF-1.4 work order", "application/pdf"),
        "employee_document": ("employee.pdf", b"%PDF-1.4 employee mismatch", "application/pdf"),
    }

    upload_response = client.post("/api/records/upload", files=files)
    assert upload_response.status_code == 200
    payload = upload_response.json()
    assert payload["status"] == "ready_for_processing"

    record_id = payload["record_id"]
    process_response = client.post(f"/api/records/{record_id}/process")
    assert process_response.status_code == 200

    processed = process_response.json()
    assert processed["record_status"] in {"matched", "matched_with_warnings", "exception"}
    assert len(processed["field_results"]) > 0

    with SessionLocal() as db:
        record_count = db.scalar(select(func.count()).select_from(Record))
        extracted_count = db.scalar(select(func.count()).select_from(ExtractedField))
        extracted_row_count = db.scalar(select(func.count()).select_from(ExtractedRow))
        results_count = db.scalar(select(func.count()).select_from(ReconciliationResult))
        row_group_count = db.scalar(select(func.count()).select_from(RowMatchGroup))
        batch_count = db.scalar(select(func.count()).select_from(DocumentBatch))

        assert record_count == 1
        assert extracted_count and extracted_count > 0
        assert extracted_row_count and extracted_row_count > 0
        assert results_count and results_count > 0
        assert row_group_count and row_group_count > 0
        assert batch_count == 1

    queue_response = client.get("/api/records")
    assert queue_response.status_code == 200
    queue_items = queue_response.json()["items"]
    assert len(queue_items) == 1

    detail_response = client.get(f"/api/records/{record_id}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["record_id"] == record_id
    assert len(detail["field_results"]) > 0


def test_upload_requires_at_least_one_document() -> None:
    response = client.post("/api/records/upload", files={})
    assert response.status_code == 400
    payload = response.json()
    assert payload["code"] == "empty_upload"
    assert "At least one document is required" in payload["message"]


def test_upload_rejects_non_pdf_file() -> None:
    files = {
        "client_document": ("client.txt", b"not a pdf", "text/plain"),
    }
    response = client.post("/api/records/upload", files=files)
    assert response.status_code == 400
    payload = response.json()
    assert payload["code"] in {"invalid_document_type", "invalid_content_type"}


def test_records_filters_support_client_id_and_date_range() -> None:
    files = {
        "client_document": ("client-filter.pdf", b"%PDF-1.4 client", "application/pdf"),
        "work_order_document": ("work_order-filter.pdf", b"%PDF-1.4 work order", "application/pdf"),
        "employee_document": ("employee-filter.pdf", b"%PDF-1.4 employee", "application/pdf"),
    }

    upload_response = client.post("/api/records/upload", files=files)
    record_id = upload_response.json()["record_id"]
    client.post(f"/api/records/{record_id}/process")

    by_client = client.get("/api/records", params={"client_id": "C-102"})
    assert by_client.status_code == 200
    assert by_client.json()["total"] >= 1

    in_range = client.get("/api/records", params={"date_from": "2026-02-01", "date_to": "2026-02-28"})
    assert in_range.status_code == 200
    assert in_range.json()["total"] >= 1

    out_of_range = client.get("/api/records", params={"date_from": "2026-03-01"})
    assert out_of_range.status_code == 200
    assert out_of_range.json()["total"] == 0


def test_records_filter_rejects_invalid_date_format() -> None:
    response = client.get("/api/records", params={"date_from": "02-20-2026"})
    assert response.status_code == 400
    payload = response.json()
    assert payload["code"] == "invalid_query_param"
