from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class SharePointMappingIn(BaseModel):
    client_name: str
    client_id: Optional[str] = None
    site_id: Optional[str] = None
    library_id: Optional[str] = None
    folder_path: str
    is_active: bool = True


class SharePointMappingOut(SharePointMappingIn):
    id: int
