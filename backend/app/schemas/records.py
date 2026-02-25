from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DocumentOut(BaseModel):
    document_id: int
    doc_type: str
    filename: str
    status: str


class UploadResponse(BaseModel):
    record_id: str
    status: str
    documents: list[DocumentOut]


class ProcessResponseField(BaseModel):
    field_key: str
    status: str
    severity: str
    threshold: Optional[float] = None
    values: dict[str, Optional[str]]
    normalized_values: dict[str, Optional[str]]
    reason: Optional[str] = None


class ProcessResponse(BaseModel):
    record_id: str
    record_status: str
    field_results: list[ProcessResponseField]


class RecordListItem(BaseModel):
    record_id: str
    client_name: Optional[str]
    work_order_number: Optional[str]
    employee_id: Optional[str]
    shift_date: Optional[str]
    record_status: str
    approval_status: str
    created_at: datetime


class RecordListResponse(BaseModel):
    items: list[RecordListItem]
    page: int
    page_size: int
    total: int


class RecordDetailResponse(BaseModel):
    record_id: str
    record_status: str
    approval_status: str
    documents: list[DocumentOut]
    field_results: list[ProcessResponseField]
    audit_log: list[dict[str, str]]


class ApprovalRequest(BaseModel):
    reviewer_name: str = Field(min_length=1)
    notes: Optional[str] = None


class ApprovalResponse(BaseModel):
    record_id: str
    approval_status: str
    approved_at: datetime


class SharePointUploadResponse(BaseModel):
    record_id: str
    upload_status: str
    destination_path: str
    files_uploaded: int
    retry_count: int = 0
