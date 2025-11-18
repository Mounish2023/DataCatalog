from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_db
from app import schemas, audit
from app.models.models import Column, User
from .auth_routes import get_current_user

router = APIRouter(prefix="/api/tables/{table_id}/columns", tags=["columns"])

@router.put("/{column_id}", response_model=dict)
def update_column(
    table_id: str, 
    column_id: str, 
    payload: schemas.ColumnUpdate, 
    session: Session = Depends(get_db), 
    user: User = Depends(get_current_user)
):
    col = session.get(Column, column_id)
    if not col or col.table_id != table_id:
        raise HTTPException(status_code=404, detail="column not found")
    before = {
        "business_description": col.business_description, 
        "constraints": col.constraints,
        "sample_values": col.sample_values
    }
    if payload.business_description is not None:
        col.business_description = payload.business_description
    if payload.constraints is not None:
        col.constraints = payload.constraints
    if payload.sample_values is not None:
        col.sample_values = payload.sample_values
    col.version += 1
    col.updated_at = __import__("datetime").datetime.utcnow()
    session.add(col)
    session.commit()
    audit.record_audit(
        session, user.id, "edit_column", "column", 
        col.id, before=str(before), after=str(payload.dict())
    )
    return {"msg": "updated"}
