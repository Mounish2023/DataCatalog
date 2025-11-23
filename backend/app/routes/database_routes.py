from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List, Optional
from pydantic import BaseModel
from app.database import get_db
from app.models.models import DatabaseMetadata, TableMetadata, User
from .auth_routes import get_current_user
from app import audit

router = APIRouter(prefix="/api/databases", tags=["databases"])

# --- Schemas ---
class DatabaseUpdate(BaseModel):
    description: Optional[str] = None
    business_domain: Optional[str] = None
    owner: Optional[str] = None
    sensitivity: Optional[str] = None

# --- Routes ---

@router.get("", response_model=List[dict])
async def list_databases(
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """List all databases"""
    # Eagerly load tables to avoid lazy loading in async context
    result = await session.execute(
        select(DatabaseMetadata).options(selectinload(DatabaseMetadata.tables))
    )
    databases = result.scalars().all()
    
    return [
        {
            "id": db.id,
            "name": db.database_name,
            "description": db.description,
            "business_domain": db.business_domain,
            "table_count": len(db.tables) if db.tables else 0
        }
        for db in databases
    ]

@router.get("/{db_id}", response_model=dict)
async def get_database(
    db_id: str,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get database details"""
    # Eagerly load tables to avoid lazy loading in async context
    result = await session.execute(
        select(DatabaseMetadata)
        .options(selectinload(DatabaseMetadata.tables))
        .where(DatabaseMetadata.id == db_id)
    )
    db = result.scalars().first()
    
    if not db:
        raise HTTPException(status_code=404, detail="Database not found")
        
    return {
        "id": db.id,
        "name": db.database_name,
        "description": db.description,
        "business_domain": db.business_domain,
        "owner": db.owner,
        "sensitivity": db.sensitivity.value if db.sensitivity else None,
        "source_systems": db.source_systems,
        "refresh_frequency": db.refresh_frequency,
        "created_at": db.created_at.isoformat() if db.created_at else None,
        "updated_at": db.updated_at.isoformat() if db.updated_at else None,
        "tables": [
            {
                "id": t.id,
                "technical_name": t.technical_name,
                "display_name": t.display_name,
                "type": t.table_type.value if t.table_type else "raw"
            }
            for t in db.tables
        ]
    }

@router.put("/{db_id}", response_model=dict)
async def update_database(
    db_id: str,
    payload: DatabaseUpdate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Update database metadata"""
    result = await session.execute(select(DatabaseMetadata).where(DatabaseMetadata.id == db_id))
    db = result.scalars().first()
    
    if not db:
        raise HTTPException(status_code=404, detail="Database not found")
        
    # Log changes
    changes = {}
    if payload.description is not None and payload.description != db.description:
        changes["description"] = {"old": db.description, "new": payload.description}
        db.description = payload.description
        
    if payload.business_domain is not None and payload.business_domain != db.business_domain:
        changes["business_domain"] = {"old": db.business_domain, "new": payload.business_domain}
        db.business_domain = payload.business_domain
        
    if payload.owner is not None and payload.owner != db.owner:
        changes["owner"] = {"old": db.owner, "new": payload.owner}
        db.owner = payload.owner
        
    if payload.sensitivity is not None:
        # Simple string update for now, ideally validate against Enum
        # Assuming frontend sends valid enum string
        pass 

    if not changes:
        return {"msg": "No changes detected"}
        
    db.updated_at = __import__("datetime").datetime.utcnow()
    session.add(db)
    await session.commit()
    
    # Log audit
    await audit.log_action(
        session=session,
        action="update",
        model="database",
        model_id=db.id,
        user_id=user.id,
        data={"changes": changes}
    )
    
    return {"msg": "updated"}

@router.get("/{db_id}/tables", response_model=List[dict])
async def list_database_tables(
    db_id: str,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """List tables for a specific database"""
    stmt = select(TableMetadata).where(TableMetadata.database_id == db_id)
    result = await session.execute(stmt)
    tables = result.scalars().all()
    
    return [
        {
            "id": t.id,
            "technical_name": t.technical_name,
            "display_name": t.display_name,
            "description": t.description,
            "type": t.table_type.value if t.table_type else "raw",
            "row_count": 0 # Placeholder, would need to fetch or store this
        }
        for t in tables
    ]

@router.delete("/{db_id}")
async def delete_database(
    db_id: str,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Delete a database and all its tables/columns (cascade)"""
    # Get database
    result = await session.execute(select(DatabaseMetadata).where(DatabaseMetadata.id == db_id))
    db = result.scalars().first()
    
    if not db:
        raise HTTPException(status_code=404, detail="Database not found")
    
    # Delete the database (cascade will handle tables and columns)
    await session.delete(db)
    await session.commit()
    
    return {"msg": "deleted"}

