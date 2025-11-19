from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import List

from app.database import get_db
from app import schemas, audit
from app.services import ingest

from app.models.models import Table, User, Column
from .auth_routes import get_current_user

router = APIRouter(tags=["data"])

@router.get("/api/export/json")
async def export_json(
    table_ids: str = None, 
    session: AsyncSession = Depends(get_db), 
    user: User = Depends(get_current_user)
):
    """
    table_ids: comma-separated ids (optional). If missing, export all tables.
    """
    # If specific table IDs are provided
    if table_ids:
        ids = [int(id.strip()) for id in table_ids.split(",") if id.strip().isdigit()]
        if not ids:
            raise HTTPException(status_code=400, detail="Invalid table IDs provided")
            
        result = await session.execute(
            select(Table).where(Table.id.in_(ids))
        )
        tables = result.scalars().all()
    else:
        # Get all tables if no IDs provided
        result = await session.execute(select(Table))
        tables = result.scalars().all()

    payload = []
    for t in tables:
        # Get columns for this table
        result = await session.execute(
            select(Column)
            .where(Column.table_id == t.id)
            .order_by(Column.id)
        )
        cols = result.scalars().all()
        
        payload.append({
            "id": t.id,
            "technical_name": t.technical_name,
            "display_name": t.display_name,
            "description": t.description,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "updated_at": t.updated_at.isoformat() if t.updated_at else None,
            "columns": [
                {
                    "name": c.name,
                    "data_type": c.data_type,
                    "is_nullable": c.is_nullable,
                    "default_value": c.default_value,
                    "constraints": c.constraints,
                    "business_description": c.business_description,
                    "sample_values": (c.sample_values or "").split("|") if c.sample_values else []
                }
                for c in cols
            ]
        })
    return payload

@router.post("/api/ingest")
async def ingest_data(
    payload: schemas.IngestRequest, 
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    imported = await ingest.ingest_from_target(
        session=session, 
        target_db_url=payload.target_db_url, 
        schema=payload.schema, 
        name_like=payload.name_like
    )
    await audit.record_audit(
        session, user.id, "ingest", "catalog", 
        None, before=None, after=str(imported)
    )
    return {"imported": imported}
