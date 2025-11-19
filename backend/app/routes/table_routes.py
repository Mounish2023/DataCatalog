from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app import schemas, audit
from app.models.models import Table, ColumnMetadata, User
from .auth_routes import get_current_user

router = APIRouter(prefix="/api/tables", tags=["tables"])

@router.get("", response_model=List[dict])
async def list_tables(
    q: str = None, 
    session: AsyncSession = Depends(get_db), 
    user: User = Depends(get_current_user)
):
    stmt = select(Table)
    if q:
        stmt = select(Table).where(
            Table.technical_name.ilike(f"%{q}%") | 
            Table.display_name.ilike(f"%{q}%")
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
    result = await session.execute(select(Table).where(Table.id == table_id))
    t = result.scalars().first()
    if not t:
        raise HTTPException(status_code=404, detail="Table not found")
    cols_result = await session.execute(
        select(ColumnMetadata).where(ColumnMetadata.table_id == t.id)
    )
    cols = cols_result.scalars().all()
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
                "description": c.business_description,
                # "is_primary_key": c.is_primary_key,
                "is_nullable": c.is_nullable,
                "default_value": c.default_value
            } for c in cols
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
        select(Table).where(Table.technical_name == payload.technical_name)
    )
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Table exists")
        
    # Create new table
    t = Table(
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
    result = await session.execute(select(Table).where(Table.id == table_id))
    t = result.scalars().first()
    if not t:
        raise HTTPException(status_code=404, detail="Table not found")
    
    # Log changes
    before = {
        "display_name": t.display_name, 
        "description": t.description,
        "owner_user_id": t.owner_user_id,
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
    if payload.owner_user_id is not None and payload.owner_user_id != t.owner_user_id:
        changes["owner_user_id"] = {"old": t.owner_user_id, "new": payload.owner_user_id}
        t.owner_user_id = payload.owner_user_id
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
    result = await session.execute(select(Table).where(Table.id == table_id))
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
