from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List

from app.database import get_db
from app import schemas, audit
from app.services import ingest

from app.models.models import Table, User, Column
from .auth_routes import get_current_user

router = APIRouter(tags=["data"])

@router.get("/api/export/json")
def export_json(
    table_ids: str = None, 
    session: Session = Depends(get_db), 
    user: User = Depends(get_current_user)
):
    """
    table_ids: comma-separated ids (optional). If missing, export all tables.
    """
    stmt = select(Table)
    if table_ids:
        ids = [i.strip() for i in table_ids.split(",")]
        stmt = select(Table).where(Table.id.in_(ids))
    tables = session.exec(stmt).all()
    payload = {"tables": []}
    for t in tables:
        cols = session.exec(select(Column).where(Column.table_id == t.id)).all()
        payload["tables"].append({
            "technical_name": t.technical_name,
            "display_name": t.display_name,
            "description": t.description,
            "owner_user_id": t.owner_user_id,
            "business_purpose": t.business_purpose,
            "columns": [
                {
                    "name": c.name,
                    "data_type": c.data_type,
                    "is_nullable": c.is_nullable,
                    "constraints": c.constraints,
                    "business_description": c.business_description,
                    "sample_values": (c.sample_values or "").split("|") if c.sample_values else []
                }
                for c in cols
            ]
        })
    return payload

@router.post("/api/ingest")
def ingest_data(
    payload: schemas.IngestRequest, 
    session: Session = Depends(get_db), 
    user: User = Depends(get_current_user)
):
    imported = ingest.ingest_from_target(
        session=session, 
        target_db_url=payload.target_db_url, 
        schema=payload.schema, 
        name_like=payload.name_like
    )
    audit.record_audit(
        session, user.id, "ingest", "catalog", 
        None, before=None, after=str(imported)
    )
    return {"imported": imported}
