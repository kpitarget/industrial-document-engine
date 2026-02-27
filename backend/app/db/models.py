from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    client_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Record(Base):
    __tablename__ = "records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    batch_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("document_batches.id", ondelete="SET NULL"), nullable=True, index=True
    )
    client_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    work_order_number: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    employee_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    shift_date: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    record_status: Mapped[str] = mapped_column(String(64), default="incomplete")
    approval_status: Mapped[str] = mapped_column(String(64), default="pending_review")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    batch: Mapped[Optional["DocumentBatch"]] = relationship(back_populates="records")
    documents: Mapped[list["Document"]] = relationship(back_populates="record", cascade="all, delete-orphan")
    extracted_fields: Mapped[list["ExtractedField"]] = relationship(back_populates="record", cascade="all, delete-orphan")
    extracted_rows: Mapped[list["ExtractedRow"]] = relationship(back_populates="record", cascade="all, delete-orphan")
    reconciliation_results: Mapped[list["ReconciliationResult"]] = relationship(
        back_populates="record", cascade="all, delete-orphan"
    )
    row_match_groups: Mapped[list["RowMatchGroup"]] = relationship(back_populates="record", cascade="all, delete-orphan")
    approvals: Mapped[list["Approval"]] = relationship(back_populates="record", cascade="all, delete-orphan")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="record", cascade="all, delete-orphan")


class DocumentBatch(Base):
    __tablename__ = "document_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    batch_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(64), default="received")
    source: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    records: Mapped[list[Record]] = relationship(back_populates="batch")
    extracted_rows: Mapped[list["ExtractedRow"]] = relationship(back_populates="batch", cascade="all, delete-orphan")
    row_match_groups: Mapped[list["RowMatchGroup"]] = relationship(back_populates="batch", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    record_id: Mapped[int] = mapped_column(ForeignKey("records.id", ondelete="CASCADE"), index=True)
    doc_type: Mapped[str] = mapped_column(String(32), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    storage_path: Mapped[str] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(64), default="uploaded")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    record: Mapped[Record] = relationship(back_populates="documents")
    extracted_rows: Mapped[list["ExtractedRow"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class ExtractedRow(Base):
    __tablename__ = "extracted_rows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    batch_id: Mapped[Optional[int]] = mapped_column(ForeignKey("document_batches.id", ondelete="CASCADE"), nullable=True, index=True)
    record_id: Mapped[Optional[int]] = mapped_column(ForeignKey("records.id", ondelete="CASCADE"), nullable=True, index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    doc_type: Mapped[str] = mapped_column(String(32), index=True)
    row_index: Mapped[int] = mapped_column(Integer, default=0)
    row_key: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    employee_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    employee_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    work_order_number: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    shift_date: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    start_time: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    end_time: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    total_hours: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    raw_json: Mapped[str] = mapped_column(Text, default="{}")
    normalized_json: Mapped[str] = mapped_column(Text, default="{}")
    parser_name: Mapped[str] = mapped_column(String(64), default="mock_parser")
    parser_version: Mapped[str] = mapped_column(String(32), default="v1")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    batch: Mapped[Optional[DocumentBatch]] = relationship(back_populates="extracted_rows")
    record: Mapped[Optional[Record]] = relationship(back_populates="extracted_rows")
    document: Mapped[Document] = relationship(back_populates="extracted_rows")


class RowMatchGroup(Base):
    __tablename__ = "row_match_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("document_batches.id", ondelete="CASCADE"), index=True)
    record_id: Mapped[Optional[int]] = mapped_column(ForeignKey("records.id", ondelete="CASCADE"), nullable=True, index=True)
    match_key: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    client_row_id: Mapped[Optional[int]] = mapped_column(ForeignKey("extracted_rows.id", ondelete="SET NULL"), nullable=True)
    work_order_row_id: Mapped[Optional[int]] = mapped_column(ForeignKey("extracted_rows.id", ondelete="SET NULL"), nullable=True)
    employee_row_id: Mapped[Optional[int]] = mapped_column(ForeignKey("extracted_rows.id", ondelete="SET NULL"), nullable=True)
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    batch: Mapped[DocumentBatch] = relationship(back_populates="row_match_groups")
    record: Mapped[Optional[Record]] = relationship(back_populates="row_match_groups")


class ExtractedField(Base):
    __tablename__ = "extracted_fields"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    record_id: Mapped[int] = mapped_column(ForeignKey("records.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    field_key: Mapped[str] = mapped_column(String(64), index=True)
    raw_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    normalized_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    parser_name: Mapped[str] = mapped_column(String(64), default="mock_parser")
    parser_version: Mapped[str] = mapped_column(String(32), default="v1")
    extracted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    record: Mapped[Record] = relationship(back_populates="extracted_fields")


class ReconciliationResult(Base):
    __tablename__ = "reconciliation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    record_id: Mapped[int] = mapped_column(ForeignKey("records.id", ondelete="CASCADE"), index=True)
    field_key: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32))
    severity: Mapped[str] = mapped_column(String(32))
    threshold: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    values_json: Mapped[str] = mapped_column(Text)
    normalized_values_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    record: Mapped[Record] = relationship(back_populates="reconciliation_results")


class Approval(Base):
    __tablename__ = "approvals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    record_id: Mapped[int] = mapped_column(ForeignKey("records.id", ondelete="CASCADE"), index=True)
    reviewer_name: Mapped[str] = mapped_column(String(255))
    action: Mapped[str] = mapped_column(String(64))
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    record: Mapped[Record] = relationship(back_populates="approvals")


class SharePointMapping(Base):
    __tablename__ = "sharepoint_mappings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_name: Mapped[str] = mapped_column(String(255), index=True)
    client_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    site_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    library_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    folder_path: Mapped[str] = mapped_column(String(512))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    record_id: Mapped[Optional[int]] = mapped_column(ForeignKey("records.id", ondelete="CASCADE"), nullable=True, index=True)
    event: Mapped[str] = mapped_column(String(128))
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    record: Mapped[Record] = relationship(back_populates="audit_logs")
