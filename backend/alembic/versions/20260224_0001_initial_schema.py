"""initial schema

Revision ID: 20260224_0001
Revises:
Create Date: 2026-02-24 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260224_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "clients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("client_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_clients_id"), "clients", ["id"], unique=False)
    op.create_index(op.f("ix_clients_name"), "clients", ["name"], unique=True)

    op.create_table(
        "records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("external_key", sa.String(length=64), nullable=False),
        sa.Column("client_name", sa.String(length=255), nullable=True),
        sa.Column("work_order_number", sa.String(length=64), nullable=True),
        sa.Column("employee_id", sa.String(length=64), nullable=True),
        sa.Column("shift_date", sa.String(length=16), nullable=True),
        sa.Column("record_status", sa.String(length=64), nullable=False),
        sa.Column("approval_status", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_records_external_key"), "records", ["external_key"], unique=True)

    op.create_table(
        "sharepoint_mappings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_name", sa.String(length=255), nullable=False),
        sa.Column("client_id", sa.String(length=64), nullable=True),
        sa.Column("site_id", sa.String(length=255), nullable=True),
        sa.Column("library_id", sa.String(length=255), nullable=True),
        sa.Column("folder_path", sa.String(length=512), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sharepoint_mappings_client_name"), "sharepoint_mappings", ["client_name"], unique=False)

    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("record_id", sa.Integer(), nullable=False),
        sa.Column("doc_type", sa.String(length=32), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("storage_path", sa.String(length=512), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["record_id"], ["records.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_documents_doc_type"), "documents", ["doc_type"], unique=False)
    op.create_index(op.f("ix_documents_record_id"), "documents", ["record_id"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("record_id", sa.Integer(), nullable=True),
        sa.Column("event", sa.String(length=128), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["record_id"], ["records.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_record_id"), "audit_logs", ["record_id"], unique=False)

    op.create_table(
        "approvals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("record_id", sa.Integer(), nullable=False),
        sa.Column("reviewer_name", sa.String(length=255), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["record_id"], ["records.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_approvals_record_id"), "approvals", ["record_id"], unique=False)

    op.create_table(
        "extracted_fields",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("record_id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("field_key", sa.String(length=64), nullable=False),
        sa.Column("raw_value", sa.Text(), nullable=True),
        sa.Column("normalized_value", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("parser_name", sa.String(length=64), nullable=False),
        sa.Column("parser_version", sa.String(length=32), nullable=False),
        sa.Column("extracted_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["record_id"], ["records.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_extracted_fields_document_id"), "extracted_fields", ["document_id"], unique=False)
    op.create_index(op.f("ix_extracted_fields_field_key"), "extracted_fields", ["field_key"], unique=False)
    op.create_index(op.f("ix_extracted_fields_record_id"), "extracted_fields", ["record_id"], unique=False)

    op.create_table(
        "reconciliation_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("record_id", sa.Integer(), nullable=False),
        sa.Column("field_key", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("threshold", sa.Float(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("values_json", sa.Text(), nullable=False),
        sa.Column("normalized_values_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["record_id"], ["records.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reconciliation_results_field_key"), "reconciliation_results", ["field_key"], unique=False)
    op.create_index(op.f("ix_reconciliation_results_record_id"), "reconciliation_results", ["record_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_reconciliation_results_record_id"), table_name="reconciliation_results")
    op.drop_index(op.f("ix_reconciliation_results_field_key"), table_name="reconciliation_results")
    op.drop_table("reconciliation_results")

    op.drop_index(op.f("ix_extracted_fields_record_id"), table_name="extracted_fields")
    op.drop_index(op.f("ix_extracted_fields_field_key"), table_name="extracted_fields")
    op.drop_index(op.f("ix_extracted_fields_document_id"), table_name="extracted_fields")
    op.drop_table("extracted_fields")

    op.drop_index(op.f("ix_approvals_record_id"), table_name="approvals")
    op.drop_table("approvals")

    op.drop_index(op.f("ix_audit_logs_record_id"), table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index(op.f("ix_documents_record_id"), table_name="documents")
    op.drop_index(op.f("ix_documents_doc_type"), table_name="documents")
    op.drop_table("documents")

    op.drop_index(op.f("ix_sharepoint_mappings_client_name"), table_name="sharepoint_mappings")
    op.drop_table("sharepoint_mappings")

    op.drop_index(op.f("ix_records_external_key"), table_name="records")
    op.drop_table("records")

    op.drop_index(op.f("ix_clients_name"), table_name="clients")
    op.drop_index(op.f("ix_clients_id"), table_name="clients")
    op.drop_table("clients")
