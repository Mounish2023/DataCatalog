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
        "description": col.description,
        "is_primary_key": col.is_primary_key,
        "is_foreign_key": col.is_foreign_key,
        "is_nullable": col.is_nullable,
        "is_pii": col.is_pii,
        "cardinality": col.cardinality,
        "valid_values": col.valid_values,
        "example_value": col.example_value,
        "transformation_logic": col.transformation_logic,
        "downstream_usage": col.downstream_usage
    }

    # Update fields if provided in payload
    if payload.description is not None:
        col.description = payload.description
    if payload.is_primary_key is not None:
        col.is_primary_key = payload.is_primary_key
    if payload.is_foreign_key is not None:
        col.is_foreign_key = payload.is_foreign_key
    if payload.is_nullable is not None:
        col.is_nullable = payload.is_nullable
    if payload.is_pii is not None:
        col.is_pii = payload.is_pii
    if payload.cardinality is not None:
        col.cardinality = payload.cardinality
    if payload.valid_values is not None:
        col.valid_values = payload.valid_values
    if payload.example_value is not None:
        col.example_value = payload.example_value
    if payload.transformation_logic is not None:
        col.transformation_logic = payload.transformation_logic
    if payload.downstream_usage is not None:
        col.downstream_usage = payload.downstream_usage

    col.updated_at = __import__("datetime").datetime.utcnow()
    session.add(col)
    await session.commit()
    await audit.record_audit(
        session, user.id, "edit_column", "column", 
        col.id, before=str(before), after=str(payload.model_dump())
    )
    return {"msg": "updated"}
