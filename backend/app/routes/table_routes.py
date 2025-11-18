from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List

from app.database import get_db
from app import schemas, audit
from app.models.models import Table, ColumnMetadata, User
from .auth_routes import get_current_user

router = APIRouter(prefix="/api/tables", tags=["tables"])

@router.get("", response_model=List[dict])
def list_tables(
    q: str = None, 
    session: Session = Depends(get_db), 
    user: User = Depends(get_current_user)
):
    stmt = select(Table)
    if q:
        stmt = select(Table).where(
            Table.technical_name.ilike(f"%{q}%") | 
            Table.display_name.ilike(f"%{q}%")
        )
    results = session.exec(stmt).all()
    return [
        {
            "id": t.id, 
            "technical_name": t.technical_name, 
            "display_name": t.display_name, 
            "description": t.description
        } for t in results
    ]

@router.get("/{table_id}", response_model=dict)
def get_table(
    table_id: str, 
    session: Session = Depends(get_db), 
    user: User = Depends(get_current_user)
):
    t = session.get(Table, table_id)
    if not t:
        raise HTTPException(status_code=404, detail="Table not found")
    cols = session.exec(select(ColumnMetadata).where(ColumnMetadata.table_id == t.id)).all()
    return {
        "id": t.id, 
        "technical_name": t.technical_name, 
        "display_name": t.display_name, 
        "description": t.description, 
        "columns": [
            {
                "id": c.id, 
                "name": c.name, 
                "data_type": c.data_type, 
                "is_nullable": c.is_nullable, 
                "business_description": c.business_description, 
                "sample_values": (c.sample_values or "").split("|") if c.sample_values else []
            } for c in cols
        ]
    }

@router.post("", response_model=dict)
def create_table(
    payload: schemas.TableCreate, 
    session: Session = Depends(get_db), 
    user: User = Depends(get_current_user)
):
    if session.exec(select(Table).where(Table.technical_name == payload.technical_name)).first():
        raise HTTPException(status_code=400, detail="Table exists")
    t = Table(
        technical_name=payload.technical_name, 
        display_name=payload.display_name, 
        description=payload.description
    )
    session.add(t)
    session.commit()
    audit.record_audit(
        session, user.id, "create_table", "table", 
        t.id, before=None, after=str(payload.dict())
    )
    return {"id": t.id}

@router.put("/{table_id}", response_model=dict)
def update_table(
    table_id: str, 
    payload: schemas.TableUpdate, 
    session: Session = Depends(get_db), 
    user: User = Depends(get_current_user)
):
    t = session.get(Table, table_id)
    if not t:
        raise HTTPException(status_code=404, detail="not found")
    before = {
        "display_name": t.display_name, 
        "description": t.description,
        "owner_user_id": t.owner_user_id,
        "business_purpose": t.business_purpose,
        "status": t.status
    }
    if payload.display_name is not None: 
        t.display_name = payload.display_name
    if payload.description is not None: 
        t.description = payload.description
    if payload.owner_user_id is not None: 
        t.owner_user_id = payload.owner_user_id
    if payload.business_purpose is not None: 
        t.business_purpose = payload.business_purpose
    if payload.status is not None: 
        t.status = payload.status
    t.updated_at = __import__("datetime").datetime.utcnow()
    session.add(t)
    session.commit()
    audit.record_audit(
        session, user.id, "edit_table", "table", 
        t.id, before=str(before), after=str(payload.dict())
    )
    return {"msg": "updated"}

@router.delete("/{table_id}")
def delete_table(
    table_id: str, 
    session: Session = Depends(get_db), 
    user: User = Depends(get_current_user)
):
    t = session.get(Table, table_id)
    if not t:
        raise HTTPException(status_code=404, detail="not found")
    session.delete(t)
    session.commit()
    audit.record_audit(
        session, user.id, "delete_table", "table", table_id
    )
    return {"msg": "deleted"}
