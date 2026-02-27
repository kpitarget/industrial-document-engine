from __future__ import annotations

import json
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import (
    Approval,
    AuditLog,
    Document,
    DocumentBatch,
    ExtractedField,
    ExtractedRow,
    Record,
    ReconciliationResult,
    RowMatchGroup,
    SharePointMapping,
)
from app.db.session import get_db
from app.schemas.records import (
    ApprovalRequest,
    ApprovalResponse,
    DocumentOut,
    ProcessResponse,
    ProcessResponseField,
    RecordDetailResponse,
    RecordListItem,
    RecordListResponse,
    SharePointUploadResponse,
    UploadResponse,
)
from app.services.extraction import MockPdfExtractionService
from app.services.matching import RowCandidate, build_match_key, match_row_candidates
from app.services.normalization import normalize_value
from app.services.reconciliation import DOC_TYPES, reconcile
from app.services.sharepoint import MockSharePointUploader

router = APIRouter(prefix="/records", tags=["records"])

extraction_service = MockPdfExtractionService()
sharepoint_uploader = MockSharePointUploader()


def _record_id(record: Record) -> str:
    return f"rec_{record.id}"


def _parse_record_id(record_id: str) -> int:
    try:
        return int(record_id.replace("rec_", ""))
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "invalid_record_id",
                "message": "Invalid record id",
                "details": {"record_id": record_id},
            },
        ) from exc


def _get_record(db: Session, record_id: str) -> Record:
    record = db.get(Record, _parse_record_id(record_id))
    if not record:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "record_not_found",
                "message": "Record not found",
                "details": {"record_id": record_id},
            },
        )
    return record


def _write_file(doc_type: str, file: UploadFile) -> str:
    filename = file.filename or ""
    content_type = file.content_type or ""
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "invalid_document_type",
                "message": "Only PDF documents are supported",
                "details": {"doc_type": doc_type, "filename": filename},
            },
        )
    if content_type and content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "invalid_content_type",
                "message": "Unsupported file content type",
                "details": {"doc_type": doc_type, "content_type": content_type},
            },
        )

    storage_root = Path(settings.local_storage_path)
    storage_root.mkdir(parents=True, exist_ok=True)
    generated_name = f"{uuid.uuid4()}_{filename}"
    doc_path = storage_root / doc_type / generated_name
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    content = file.file.read()
    max_size_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_size_bytes:
        raise HTTPException(
            status_code=413,
            detail={
                "code": "file_too_large",
                "message": f"File exceeds max size of {settings.max_upload_size_mb}MB",
                "details": {"doc_type": doc_type, "filename": filename},
            },
        )
    doc_path.write_bytes(content)
    return str(doc_path)


def _has_required_docs(record: Record) -> bool:
    present = {doc.doc_type for doc in record.documents}
    return all(doc_type in present for doc_type in DOC_TYPES)


def _field_results_for_record(db: Session, record: Record) -> list[ProcessResponseField]:
    rows = (
        db.execute(
            select(ReconciliationResult).where(ReconciliationResult.record_id == record.id).order_by(ReconciliationResult.field_key)
        )
        .scalars()
        .all()
    )
    return [
        ProcessResponseField(
            field_key=row.field_key,
            status=row.status,
            severity=row.severity,
            threshold=row.threshold,
            values=json.loads(row.values_json),
            normalized_values=json.loads(row.normalized_values_json),
            reason=row.reason,
        )
        for row in rows
    ]


def _touch_audit(db: Session, record_id: int, event: str, details: Optional[str] = None) -> None:
    db.add(AuditLog(record_id=record_id, event=event, details=details))


def _parse_iso_date(value: str, field_name: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "invalid_query_param",
                "message": f"Invalid {field_name}. Expected YYYY-MM-DD",
                "details": {field_name: value},
            },
        ) from exc


@router.post("/upload", response_model=UploadResponse)
def upload_record_documents(
    client_document: Optional[UploadFile] = File(default=None),
    work_order_document: Optional[UploadFile] = File(default=None),
    employee_document: Optional[UploadFile] = File(default=None),
    record_group_key: Optional[str] = Form(default=None),
    db: Session = Depends(get_db),
) -> UploadResponse:
    if not any([client_document, work_order_document, employee_document]):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "empty_upload",
                "message": "At least one document is required",
                "details": None,
            },
        )

    batch_key = record_group_key or f"batch_{uuid.uuid4().hex[:12]}"
    external_key = f"key_{uuid.uuid4().hex[:12]}"

    batch = db.execute(select(DocumentBatch).where(DocumentBatch.batch_key == batch_key)).scalars().first()
    if not batch:
        batch = DocumentBatch(batch_key=batch_key, status="received", source="upload")
        db.add(batch)
        db.flush()

    record = Record(external_key=external_key, batch_id=batch.id)
    db.add(record)
    db.flush()

    incoming = {
        "client": client_document,
        "work_order": work_order_document,
        "employee": employee_document,
    }
    created_documents: list[Document] = []

    for doc_type, file in incoming.items():
        if file is None:
            continue
        path = _write_file(doc_type=doc_type, file=file)
        doc = Document(
            record_id=record.id,
            doc_type=doc_type,
            filename=file.filename,
            storage_path=path,
            status="uploaded",
        )
        db.add(doc)
        created_documents.append(doc)

    present_doc_types = {doc.doc_type for doc in created_documents}
    record.record_status = "ready_for_processing" if all(doc_type in present_doc_types for doc_type in DOC_TYPES) else "incomplete"
    _touch_audit(db, record.id, "record_created", f"Documents uploaded (batch={batch.batch_key})")
    db.commit()

    return UploadResponse(
        record_id=_record_id(record),
        status=record.record_status,
        documents=[
            DocumentOut(document_id=doc.id, doc_type=doc.doc_type, filename=doc.filename, status=doc.status)
            for doc in created_documents
        ],
    )


@router.post("/{record_id}/process", response_model=ProcessResponse)
def process_record(record_id: str, db: Session = Depends(get_db)) -> ProcessResponse:
    record = _get_record(db, record_id)

    db.query(ExtractedField).filter(ExtractedField.record_id == record.id).delete()
    db.query(ReconciliationResult).filter(ReconciliationResult.record_id == record.id).delete()
    db.query(RowMatchGroup).filter(RowMatchGroup.record_id == record.id).delete()
    db.query(ExtractedRow).filter(ExtractedRow.record_id == record.id).delete()

    if record.batch_id is None:
        generated_batch_key = f"batch_{uuid.uuid4().hex[:12]}"
        batch = DocumentBatch(batch_key=generated_batch_key, status="received", source="backfill")
        db.add(batch)
        db.flush()
        record.batch_id = batch.id

    normalized_matrix: dict[str, dict[str, Optional[str]]] = {}
    extracted_row_payloads: list[tuple[ExtractedRow, dict[str, Optional[str]]]] = []
    for document in record.documents:
        parsed_document = extraction_service.parse(
            doc_type=document.doc_type,
            filename=document.filename,
            storage_path=document.storage_path,
        )
        for field_key, raw_value in parsed_document.fields.items():
            normalized = normalize_value(field_key=field_key, raw_value=raw_value)
            db.add(
                ExtractedField(
                    record_id=record.id,
                    document_id=document.id,
                    field_key=field_key,
                    raw_value=raw_value,
                    normalized_value=normalized,
                    parser_name=parsed_document.parser_name,
                    parser_version=parsed_document.parser_version,
                )
            )
            normalized_matrix.setdefault(field_key, {})[document.doc_type] = normalized

        for extracted_row in parsed_document.rows:
            normalized_row = {
                field_key: normalize_value(field_key=field_key, raw_value=raw_value)
                for field_key, raw_value in extracted_row.fields.items()
            }
            row_model = ExtractedRow(
                batch_id=record.batch_id,
                record_id=record.id,
                document_id=document.id,
                doc_type=document.doc_type,
                row_index=extracted_row.row_index,
                row_key=None,
                employee_id=normalized_row.get("employee_id"),
                employee_name=normalized_row.get("employee_name"),
                work_order_number=normalized_row.get("work_order_number"),
                shift_date=normalized_row.get("shift_date"),
                start_time=normalized_row.get("start_time"),
                end_time=normalized_row.get("end_time"),
                total_hours=normalized_row.get("total_hours"),
                raw_json=json.dumps(extracted_row.fields),
                normalized_json=json.dumps(normalized_row),
                parser_name=parsed_document.parser_name,
                parser_version=parsed_document.parser_version,
            )
            db.add(row_model)
            extracted_row_payloads.append((row_model, normalized_row))

    db.flush()

    row_candidates: list[RowCandidate] = []
    for row_model, normalized_row in extracted_row_payloads:
        row_key = build_match_key(normalized_row)
        row_model.row_key = row_key or None
        row_candidates.append(
            RowCandidate(
                row_id=row_model.id,
                doc_type=row_model.doc_type,
                row_index=row_model.row_index,
                normalized_fields=normalized_row,
            )
        )

    matched_rows = match_row_candidates(row_candidates)
    for matched_row in matched_rows:
        db.add(
            RowMatchGroup(
                batch_id=record.batch_id,
                record_id=record.id,
                match_key=matched_row.match_key,
                status=matched_row.status,
                confidence=matched_row.confidence,
                reason=matched_row.reason,
                client_row_id=matched_row.row_ids_by_doc.get("client"),
                work_order_row_id=matched_row.row_ids_by_doc.get("work_order"),
                employee_row_id=matched_row.row_ids_by_doc.get("employee"),
                payload_json=json.dumps(matched_row.payload),
            )
        )

    has_all_docs = _has_required_docs(record)
    results, record_status = reconcile(field_values=normalized_matrix, has_all_required_docs=has_all_docs)

    for row in results:
        db.add(
            ReconciliationResult(
                record_id=record.id,
                field_key=row.field_key,
                status=row.status,
                severity=row.severity,
                threshold=row.threshold,
                reason=row.reason,
                values_json=json.dumps(row.values),
                normalized_values_json=json.dumps(row.normalized_values),
            )
        )

    # Keep queue fields hydrated for UI filters/search.
    record.client_name = normalized_matrix.get("client_name", {}).get("client")
    record.work_order_number = normalized_matrix.get("work_order_number", {}).get("client")
    record.employee_id = normalized_matrix.get("employee_id", {}).get("employee")
    record.shift_date = normalized_matrix.get("shift_date", {}).get("employee")
    record.record_status = record_status
    if record.batch:
        has_row_issues = any(match.status in {"conflict", "insufficient_data"} for match in matched_rows)
        record.batch.status = "needs_review" if has_row_issues else "processed"
    _touch_audit(
        db,
        record.id,
        "record_processed",
        f"Result status: {record_status}, rows={len(extracted_row_payloads)}, groups={len(matched_rows)}",
    )
    db.commit()

    field_results = _field_results_for_record(db, record)
    return ProcessResponse(record_id=_record_id(record), record_status=record_status, field_results=field_results)


@router.get("", response_model=RecordListResponse)
def list_records(
    status: Optional[str] = Query(default=None),
    client_id: Optional[str] = Query(default=None),
    date_from: Optional[str] = Query(default=None),
    date_to: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
) -> RecordListResponse:
    query = select(Record)

    if status:
        query = query.where(Record.record_status == status)

    if client_id:
        query = query.where(
            Record.id.in_(
                select(ExtractedField.record_id).where(
                    ExtractedField.field_key == "client_id",
                    ExtractedField.normalized_value == client_id,
                )
            )
        )

    if date_from:
        parsed_from = _parse_iso_date(date_from, "date_from")
        query = query.where(Record.shift_date.is_not(None), Record.shift_date >= parsed_from.isoformat())

    if date_to:
        parsed_to = _parse_iso_date(date_to, "date_to")
        query = query.where(Record.shift_date.is_not(None), Record.shift_date <= parsed_to.isoformat())

    if q:
        like_value = f"%{q}%"
        query = query.where(or_(Record.work_order_number.ilike(like_value), Record.employee_id.ilike(like_value)))

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    records = (
        db.execute(query.order_by(Record.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).scalars().all()
    )

    return RecordListResponse(
        items=[
            RecordListItem(
                record_id=_record_id(record),
                client_name=record.client_name,
                work_order_number=record.work_order_number,
                employee_id=record.employee_id,
                shift_date=record.shift_date,
                record_status=record.record_status,
                approval_status=record.approval_status,
                created_at=record.created_at,
            )
            for record in records
        ],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/{record_id}", response_model=RecordDetailResponse)
def get_record_detail(record_id: str, db: Session = Depends(get_db)) -> RecordDetailResponse:
    record = _get_record(db, record_id)
    logs = (
        db.execute(select(AuditLog).where(AuditLog.record_id == record.id).order_by(AuditLog.created_at.asc()))
        .scalars()
        .all()
    )
    return RecordDetailResponse(
        record_id=_record_id(record),
        record_status=record.record_status,
        approval_status=record.approval_status,
        documents=[
            DocumentOut(document_id=doc.id, doc_type=doc.doc_type, filename=doc.filename, status=doc.status)
            for doc in record.documents
        ],
        field_results=_field_results_for_record(db, record),
        audit_log=[
            {
                "event": log.event,
                "timestamp": log.created_at.isoformat(),
                "details": log.details or "",
            }
            for log in logs
        ],
    )


def _apply_approval_action(
    db: Session,
    record: Record,
    action: str,
    approval_status: str,
    payload: ApprovalRequest,
) -> ApprovalResponse:
    previous_status = record.approval_status
    record.approval_status = approval_status
    approval = Approval(
        record_id=record.id,
        reviewer_name=payload.reviewer_name,
        action=action,
        notes=payload.notes,
    )
    db.add(approval)
    _touch_audit(
        db,
        record.id,
        "approval_updated",
        f"{previous_status} -> {approval_status} by {payload.reviewer_name}",
    )
    db.commit()
    return ApprovalResponse(record_id=_record_id(record), approval_status=approval_status, approved_at=datetime.utcnow())


@router.post("/{record_id}/approve", response_model=ApprovalResponse)
def approve_record(record_id: str, payload: ApprovalRequest, db: Session = Depends(get_db)) -> ApprovalResponse:
    record = _get_record(db, record_id)
    return _apply_approval_action(db, record, "approve", "approved", payload)


@router.post("/{record_id}/approve-with-exceptions", response_model=ApprovalResponse)
def approve_with_exceptions(
    record_id: str, payload: ApprovalRequest, db: Session = Depends(get_db)
) -> ApprovalResponse:
    record = _get_record(db, record_id)
    return _apply_approval_action(db, record, "approve_with_exceptions", "approved_with_exceptions", payload)


@router.post("/{record_id}/reject", response_model=ApprovalResponse)
def reject_record(record_id: str, payload: ApprovalRequest, db: Session = Depends(get_db)) -> ApprovalResponse:
    record = _get_record(db, record_id)
    return _apply_approval_action(db, record, "reject", "rejected", payload)


@router.post("/{record_id}/sharepoint-upload", response_model=SharePointUploadResponse)
def sharepoint_upload(record_id: str, db: Session = Depends(get_db)) -> SharePointUploadResponse:
    record = _get_record(db, record_id)
    if record.approval_status not in {"approved", "approved_with_exceptions"}:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "record_not_approved",
                "message": "Record must be approved before upload",
                "details": {"approval_status": record.approval_status},
            },
        )

    mapping = (
        db.execute(
            select(SharePointMapping).where(
                SharePointMapping.client_name == (record.client_name or ""),
                SharePointMapping.is_active.is_(True),
            )
        )
        .scalars()
        .first()
    )
    destination_path = mapping.folder_path if mapping else "/Clients/Unmapped/Invoices"

    result = sharepoint_uploader.upload_record(destination_path=destination_path, files_uploaded=len(record.documents))
    _touch_audit(db, record.id, "sharepoint_upload", f"{result.status} -> {result.destination_path}")
    db.commit()

    return SharePointUploadResponse(
        record_id=_record_id(record),
        upload_status=result.status,
        destination_path=result.destination_path,
        files_uploaded=result.files_uploaded,
        retry_count=0,
    )


@router.post("/{record_id}/sharepoint-retry", response_model=SharePointUploadResponse)
def sharepoint_retry(record_id: str, db: Session = Depends(get_db)) -> SharePointUploadResponse:
    response = sharepoint_upload(record_id=record_id, db=db)
    response.retry_count = 1
    return response
