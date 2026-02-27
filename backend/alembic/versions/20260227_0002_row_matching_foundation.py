"""row matching foundation

Revision ID: 20260227_0002
Revises: 20260224_0001
Create Date: 2026-02-27 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260227_0002"
down_revision = "20260224_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "document_batches" not in tables:
        op.create_table(
            "document_batches",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("batch_key", sa.String(length=64), nullable=False),
            sa.Column("status", sa.String(length=64), nullable=False),
            sa.Column("source", sa.String(length=64), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        tables.add("document_batches")

    batch_indexes = {index["name"] for index in inspector.get_indexes("document_batches")}
    if op.f("ix_document_batches_batch_key") not in batch_indexes:
        op.create_index(op.f("ix_document_batches_batch_key"), "document_batches", ["batch_key"], unique=True)

    record_columns = {column["name"] for column in inspector.get_columns("records")}
    if "batch_id" not in record_columns:
        with op.batch_alter_table("records", schema=None) as batch_op:
            batch_op.add_column(sa.Column("batch_id", sa.Integer(), nullable=True))
            batch_op.create_index(batch_op.f("ix_records_batch_id"), ["batch_id"], unique=False)
            batch_op.create_foreign_key(
                "fk_records_batch_id_document_batches",
                "document_batches",
                ["batch_id"],
                ["id"],
                ondelete="SET NULL",
            )
    else:
        record_indexes = {index["name"] for index in inspector.get_indexes("records")}
        if op.f("ix_records_batch_id") not in record_indexes:
            op.create_index(op.f("ix_records_batch_id"), "records", ["batch_id"], unique=False)

        record_fks = inspector.get_foreign_keys("records")
        has_batch_fk = any(fk.get("constrained_columns") == ["batch_id"] for fk in record_fks)
        if not has_batch_fk:
            with op.batch_alter_table("records", schema=None) as batch_op:
                batch_op.create_foreign_key(
                    "fk_records_batch_id_document_batches",
                    "document_batches",
                    ["batch_id"],
                    ["id"],
                    ondelete="SET NULL",
                )

    if "extracted_rows" not in tables:
        op.create_table(
            "extracted_rows",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("batch_id", sa.Integer(), nullable=True),
            sa.Column("record_id", sa.Integer(), nullable=True),
            sa.Column("document_id", sa.Integer(), nullable=False),
            sa.Column("doc_type", sa.String(length=32), nullable=False),
            sa.Column("row_index", sa.Integer(), nullable=False),
            sa.Column("row_key", sa.String(length=128), nullable=True),
            sa.Column("employee_id", sa.String(length=64), nullable=True),
            sa.Column("employee_name", sa.String(length=255), nullable=True),
            sa.Column("work_order_number", sa.String(length=64), nullable=True),
            sa.Column("shift_date", sa.String(length=16), nullable=True),
            sa.Column("start_time", sa.String(length=16), nullable=True),
            sa.Column("end_time", sa.String(length=16), nullable=True),
            sa.Column("total_hours", sa.String(length=32), nullable=True),
            sa.Column("raw_json", sa.Text(), nullable=False),
            sa.Column("normalized_json", sa.Text(), nullable=False),
            sa.Column("parser_name", sa.String(length=64), nullable=False),
            sa.Column("parser_version", sa.String(length=32), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["batch_id"], ["document_batches.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["record_id"], ["records.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        tables.add("extracted_rows")

    extracted_row_indexes = {index["name"] for index in inspector.get_indexes("extracted_rows")}
    for index_name, columns in [
        (op.f("ix_extracted_rows_batch_id"), ["batch_id"]),
        (op.f("ix_extracted_rows_doc_type"), ["doc_type"]),
        (op.f("ix_extracted_rows_document_id"), ["document_id"]),
        (op.f("ix_extracted_rows_employee_id"), ["employee_id"]),
        (op.f("ix_extracted_rows_record_id"), ["record_id"]),
        (op.f("ix_extracted_rows_row_key"), ["row_key"]),
    ]:
        if index_name not in extracted_row_indexes:
            op.create_index(index_name, "extracted_rows", columns, unique=False)

    if "row_match_groups" not in tables:
        op.create_table(
            "row_match_groups",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("batch_id", sa.Integer(), nullable=False),
            sa.Column("record_id", sa.Integer(), nullable=True),
            sa.Column("match_key", sa.String(length=128), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("confidence", sa.Float(), nullable=True),
            sa.Column("reason", sa.Text(), nullable=True),
            sa.Column("client_row_id", sa.Integer(), nullable=True),
            sa.Column("work_order_row_id", sa.Integer(), nullable=True),
            sa.Column("employee_row_id", sa.Integer(), nullable=True),
            sa.Column("payload_json", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["batch_id"], ["document_batches.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["client_row_id"], ["extracted_rows.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["employee_row_id"], ["extracted_rows.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["record_id"], ["records.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["work_order_row_id"], ["extracted_rows.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        tables.add("row_match_groups")

    row_group_indexes = {index["name"] for index in inspector.get_indexes("row_match_groups")}
    for index_name, columns in [
        (op.f("ix_row_match_groups_batch_id"), ["batch_id"]),
        (op.f("ix_row_match_groups_match_key"), ["match_key"]),
        (op.f("ix_row_match_groups_record_id"), ["record_id"]),
        (op.f("ix_row_match_groups_status"), ["status"]),
    ]:
        if index_name not in row_group_indexes:
            op.create_index(index_name, "row_match_groups", columns, unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_row_match_groups_status"), table_name="row_match_groups")
    op.drop_index(op.f("ix_row_match_groups_record_id"), table_name="row_match_groups")
    op.drop_index(op.f("ix_row_match_groups_match_key"), table_name="row_match_groups")
    op.drop_index(op.f("ix_row_match_groups_batch_id"), table_name="row_match_groups")
    op.drop_table("row_match_groups")

    op.drop_index(op.f("ix_extracted_rows_row_key"), table_name="extracted_rows")
    op.drop_index(op.f("ix_extracted_rows_record_id"), table_name="extracted_rows")
    op.drop_index(op.f("ix_extracted_rows_employee_id"), table_name="extracted_rows")
    op.drop_index(op.f("ix_extracted_rows_document_id"), table_name="extracted_rows")
    op.drop_index(op.f("ix_extracted_rows_doc_type"), table_name="extracted_rows")
    op.drop_index(op.f("ix_extracted_rows_batch_id"), table_name="extracted_rows")
    op.drop_table("extracted_rows")

    with op.batch_alter_table("records", schema=None) as batch_op:
        batch_op.drop_constraint("fk_records_batch_id_document_batches", type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_records_batch_id"))
        batch_op.drop_column("batch_id")

    op.drop_index(op.f("ix_document_batches_batch_key"), table_name="document_batches")
    op.drop_table("document_batches")
