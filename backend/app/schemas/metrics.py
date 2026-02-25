from pydantic import BaseModel


class MetricsSummary(BaseModel):
    records_processed: int
    matched: int
    matched_with_warnings: int
    exceptions: int
    approved: int
    approved_with_exceptions: int
    rejected: int
    upload_failures: int
