from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app import schemas, audit
from app.database import get_db
from app.models.models import TableMetadata, ColumnMetadata, DatabaseMetadata, User
from .auth_routes import get_current_user

router = APIRouter(prefix="/api/tables", tags=["tables"])

@router.get("", response_model=List[dict])
async def list_tables(
    q: str = None, 
    session: AsyncSession = Depends(get_db), 
    user: User = Depends(get_current_user)
):
    stmt = select(TableMetadata)
    if q:
        stmt = select(TableMetadata).where(
            TableMetadata.technical_name.ilike(f"%{q}%") | 
            TableMetadata.display_name.ilike(f"%{q}%")
        )
    result = await session.execute(stmt)
    results = result.scalars().all()
    return [
        {
            "id": t.id, 
            "technical_name": t.technical_name, 
            "display_name": t.display_name, 
            "description": t.description
        } for t in results
    ]

@router.get("/{table_id}", response_model=dict)
async def get_table(
    table_id: str, 
    session: AsyncSession = Depends(get_db), 
    user: User = Depends(get_current_user)
):
    # Get table metadata
    result = await session.execute(select(TableMetadata).where(TableMetadata.id == table_id))
    table = result.scalars().first()
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    
    # Get related database info
    db_result = await session.execute(select(DatabaseMetadata).where(DatabaseMetadata.id == table.database_id))
    database = db_result.scalars().first()
    
    # Get columns
    cols_result = await session.execute(
        select(ColumnMetadata).where(ColumnMetadata.table_id == table.id)
    )
    columns = cols_result.scalars().all()
    
    return {
        "id": table.id,
        "technical_name": table.technical_name,
        "display_name": table.display_name,
        "description": table.description,
        "table_type": table.table_type.value if table.table_type else None,
        "business_purpose": table.business_purpose,
        "status": table.status,
        "refresh_frequency": table.refresh_frequency,
        "sla_info": table.sla_info,
        "primary_key": table.primary_key,
        "foreign_keys": table.foreign_keys,
        "cardinality_overview": table.cardinality_overview,
        "owner": table.owner,
        "data_sensitivity": table.data_sensitivity.value if table.data_sensitivity else None,
        "created_at": table.created_at.isoformat() if table.created_at else None,
        "updated_at": table.updated_at.isoformat() if table.updated_at else None,
        "database": {
            "id": database.id if database else None,
            "name": database.database_name if database else None,
            "business_domain": database.business_domain if database else None,
            "sensitivity": database.sensitivity.value if database and database.sensitivity else None
        },
        "columns": [
            {
                "id": col.id,
                "column_name": col.column_name,
                "data_type": col.data_type,
                "description": col.description,
                "is_primary_key": col.is_primary_key,
                "is_foreign_key": col.is_foreign_key,
                "is_nullable": col.is_nullable,
                "is_pii": col.is_pii,
                "cardinality": col.cardinality,
                "valid_values": col.valid_values,
                "example_value": col.example_value,
                "transformation_logic": col.transformation_logic,
                "downstream_usage": col.downstream_usage,
                "created_at": col.created_at.isoformat() if col.created_at else None,
                "updated_at": col.updated_at.isoformat() if col.updated_at else None
            } for col in columns
        ]
    }

@router.post("", response_model=dict)
async def create_table(
    payload: schemas.TableCreate, 
    session: AsyncSession = Depends(get_db), 
    user: User = Depends(get_current_user)
):
    # Check if table exists
    result = await session.execute(
        select(TableMetadata).where(TableMetadata.technical_name == payload.technical_name)
    )
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Table exists")
        
    # Create new table
    t = TableMetadata(
        technical_name=payload.technical_name, 
        display_name=payload.display_name, 
        description=payload.description
    )
    session.add(t)
    await session.commit()
    await session.refresh(t)
    
    # Log the creation
    await audit.log_action(
        session=session,
        action="create",
        model="table",
        model_id=t.id,
        user_id=user.id,
        data={"name": t.technical_name}
    )
    
    return {
        "id": t.id,
        "technical_name": t.technical_name,
        "display_name": t.display_name,
        "description": t.description
    }

@router.put("/{table_id}", response_model=dict)
async def update_table(
    table_id: str, 
    payload: schemas.TableUpdate, 
    session: AsyncSession = Depends(get_db), 
    user: User = Depends(get_current_user)
):
    # Get table
    result = await session.execute(select(TableMetadata).where(TableMetadata.id == table_id))
    t = result.scalars().first()
    if not t:
        raise HTTPException(status_code=404, detail="Table not found")
    
    # Log changes
    before = {
        "display_name": t.display_name, 
        "description": t.description,
        "owner": t.owner,
        "business_purpose": t.business_purpose,
        "status": t.status
    }
    
    # Update fields if provided
    changes = {}
    if payload.display_name is not None and payload.display_name != t.display_name:
        changes["display_name"] = {"old": t.display_name, "new": payload.display_name}
        t.display_name = payload.display_name
    if payload.description is not None and payload.description != t.description:
        changes["description"] = {"old": t.description, "new": payload.description}
        t.description = payload.description
    if payload.owner is not None and payload.owner != t.owner:
        changes["owner"] = {"old": t.owner, "new": payload.owner}
        t.owner = payload.owner
    if payload.business_purpose is not None and payload.business_purpose != t.business_purpose:
        changes["business_purpose"] = {"old": t.business_purpose, "new": payload.business_purpose}
        t.business_purpose = payload.business_purpose
    if payload.status is not None and payload.status != t.status:
        changes["status"] = {"old": t.status, "new": payload.status}
        t.status = payload.status
    
    
    if not changes:
        return {"msg": "No changes detected"}
    
    t.updated_at = __import__("datetime").datetime.utcnow()
    session.add(t)
    await session.commit()
    
    # Log the update
    await audit.log_action(
        session=session,
        action="update",
        model="table",
        model_id=t.id,
        user_id=user.id,
        data={"changes": changes}
    )
    
    return {"msg": "updated"}

@router.delete("/{table_id}")
async def delete_table(
    table_id: str, 
    session: AsyncSession = Depends(get_db), 
    user: User = Depends(get_current_user)
):
    # Get table
    result = await session.execute(select(TableMetadata).where(TableMetadata.id == table_id))
    t = result.scalars().first()
    if not t:
        raise HTTPException(status_code=404, detail="Table not found")
    
    # Delete the table
    await session.delete(t)
    await session.commit()
    
    # Log the deletion
    await audit.log_action(
        session=session,
        action="delete",
        model="table",
        model_id=table_id,
        user_id=user.id,
        data={"table_name": t.technical_name}
    )
    
    return {"msg": "deleted"}
