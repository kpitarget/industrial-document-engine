from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import AuditLog, Record
from app.db.session import get_db
from app.schemas.metrics import MetricsSummary

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/summary", response_model=MetricsSummary)
def get_metrics_summary(db: Session = Depends(get_db)) -> MetricsSummary:
    def count_by_status(field: str, value: str) -> int:
        column = Record.record_status if field == "record_status" else Record.approval_status
        return (
            db.scalar(select(func.count()).select_from(Record).where(column == value))
            or 0
        )

    upload_failures = (
        db.scalar(
            select(func.count()).select_from(AuditLog).where(
                AuditLog.event == "sharepoint_upload", AuditLog.details.ilike("%failure%")
            )
        )
        or 0
    )

    return MetricsSummary(
        records_processed=db.scalar(select(func.count()).select_from(Record)) or 0,
        matched=count_by_status("record_status", "matched"),
        matched_with_warnings=count_by_status("record_status", "matched_with_warnings"),
        exceptions=count_by_status("record_status", "exception"),
        approved=count_by_status("approval_status", "approved"),
        approved_with_exceptions=count_by_status("approval_status", "approved_with_exceptions"),
        rejected=count_by_status("approval_status", "rejected"),
        upload_failures=upload_failures,
    )
