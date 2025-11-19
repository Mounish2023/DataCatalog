from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app import schemas, audit
from app.models.models import ColumnMetadata, User
from .auth_routes import get_current_user

router = APIRouter(prefix="/api/tables/{table_id}/columns", tags=["columns"])

@router.put("/{column_id}", response_model=dict)
async def update_column(
    table_id: str, 
    column_id: str, 
    payload: schemas.ColumnUpdate, 
    session: AsyncSession = Depends(get_db), 
    user: User = Depends(get_current_user)  
):
    
    
    print(f"Updating column: column_id={column_id}, table_id={table_id}")
    
    # Debug: Log the column lookup
    col = await session.get(ColumnMetadata, column_id)
    print(f"Found column: {col}")
    
    if not col:
        print(f"Column not found with ID: {column_id}")
        raise HTTPException(status_code=404, detail="column not found")
        
    if str(col.table_id) != table_id:
        print(f"Column {column_id} belongs to table {col.table_id}, but request was for table {table_id}")
        raise HTTPException(status_code=404, detail="column not found in the specified table")
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
    # col.version += 1
    col.updated_at = __import__("datetime").datetime.utcnow()
    session.add(col)
    await session.commit()
    await audit.record_audit(
        session, user.id, "edit_column", "column", 
        col.id, before=str(before), after=str(payload.model_dump())
    )
    return {"msg": "updated"}
