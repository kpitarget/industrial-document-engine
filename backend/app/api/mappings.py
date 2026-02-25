from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import SharePointMapping
from app.db.session import get_db
from app.schemas.mappings import SharePointMappingIn, SharePointMappingOut

router = APIRouter(prefix="/sharepoint-mappings", tags=["sharepoint-mappings"])


@router.get("", response_model=list[SharePointMappingOut])
def list_mappings(db: Session = Depends(get_db)) -> list[SharePointMappingOut]:
    rows = db.execute(select(SharePointMapping).order_by(SharePointMapping.client_name)).scalars().all()
    return [SharePointMappingOut.model_validate(row, from_attributes=True) for row in rows]


@router.post("", response_model=SharePointMappingOut)
def create_mapping(payload: SharePointMappingIn, db: Session = Depends(get_db)) -> SharePointMappingOut:
    row = SharePointMapping(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return SharePointMappingOut.model_validate(row, from_attributes=True)


@router.put("/{mapping_id}", response_model=SharePointMappingOut)
def update_mapping(mapping_id: int, payload: SharePointMappingIn, db: Session = Depends(get_db)) -> SharePointMappingOut:
    row = db.get(SharePointMapping, mapping_id)
    if not row:
        raise HTTPException(status_code=404, detail="Mapping not found")
    for key, value in payload.model_dump().items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return SharePointMappingOut.model_validate(row, from_attributes=True)
