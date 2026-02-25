from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: Optional[dict[str, Any]] = None


class AuditLogItem(BaseModel):
    event: str
    timestamp: datetime
    details: Optional[str] = None
