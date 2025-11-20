# backend/app/routes/ingestion_routes.py
"""
API routes for metadata ingestion pipeline
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.models import User
from app.services.metadata_ingestion import run_metadata_ingestion
from app.utils.logger import logger
from .auth_routes import get_current_user

router = APIRouter(prefix="/api/ingestion", tags=["ingestion"])


class IngestionRequest(BaseModel):
    """Request model for metadata ingestion"""
    target_connection_string: str = Field(
        ..., 
        description="Connection string to target database (postgresql://...)"
    )
    schema: str = Field(
        default="public",
        description="Database schema to ingest"
    )
    table_pattern: str = Field(
        default="%",
        description="SQL LIKE pattern for table names (e.g., 'gold_%' or '%')"
    )
    enrich_with_gpt: bool = Field(
        default=True,
        description="Whether to enrich metadata with GPT-4o"
    )


class IngestionResponse(BaseModel):
    """Response model for ingestion status"""
    status: str
    message: str
    job_id: Optional[str] = None
    stats: Optional[dict] = None


class IngestionStats(BaseModel):
    """Statistics from completed ingestion"""
    databases_processed: int
    tables_processed: int
    columns_processed: int
    duration_seconds: float
    errors: list[str]
    completed_at: datetime


# In-memory job tracking (in production, use Redis or database)
ingestion_jobs = {}


@router.post("/run", response_model=IngestionResponse)
async def trigger_ingestion(
    request: IngestionRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Trigger metadata ingestion pipeline (runs in background)
    
    This endpoint initiates the ingestion process and returns immediately.
    Use the /status/{job_id} endpoint to check progress.
    """
    import uuid
    job_id = str(uuid.uuid4())
    
    # Validate connection string format
    if not request.target_connection_string.startswith(("postgresql://", "postgresql+asyncpg://")):
        raise HTTPException(
            status_code=400,
            detail="Invalid connection string. Must start with 'postgresql://' or 'postgresql+asyncpg://'"
        )
    
    # Initialize job tracking
    ingestion_jobs[job_id] = {
        "status": "running",
        "started_at": datetime.utcnow(),
        "user_id": str(user.id),
        "stats": None,
        "error": None
    }
    
    # Add background task
    background_tasks.add_task(
        _run_ingestion_background,
        job_id=job_id,
        catalog_session=session,
        target_connection_string=request.target_connection_string,
        schema=request.schema,
        table_pattern=request.table_pattern,
        enrich=request.enrich_with_gpt
    )
    
    logger.info(f"Ingestion job {job_id} started by user {user.email}")
    
    return IngestionResponse(
        status="accepted",
        message="Ingestion job started",
        job_id=job_id
    )


@router.post("/run-sync", response_model=IngestionResponse)
async def trigger_ingestion_sync(
    request: IngestionRequest,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Run metadata ingestion synchronously (waits for completion)
    
    Use this for smaller databases or when you need immediate results.
    For large databases, use the async /run endpoint instead.
    """
    logger.info(f"Starting synchronous ingestion for user {user.email}")
    
    try:
        # Validate connection string
        if not request.target_connection_string.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise HTTPException(
                status_code=400,
                detail="Invalid connection string format"
            )
        
        # Run ingestion
        stats = await run_metadata_ingestion(
            catalog_session=session,
            target_connection_string=request.target_connection_string,
            schema=request.schema,
            table_pattern=request.table_pattern,
            enrich=request.enrich_with_gpt
        )
        
        return IngestionResponse(
            status="completed",
            message=f"Successfully processed {stats['tables_processed']} tables",
            stats=stats
        )
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {str(e)}"
        )


@router.get("/status/{job_id}")
async def get_ingestion_status(
    job_id: str,
    user: User = Depends(get_current_user)
):
    """Get status of a background ingestion job"""
    if job_id not in ingestion_jobs:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )
    
    job = ingestion_jobs[job_id]
    
    # Check authorization
    if job["user_id"] != str(user.id):
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view this job"
        )
    
    return {
        "job_id": job_id,
        "status": job["status"],
        "started_at": job["started_at"],
        "stats": job["stats"],
        "error": job["error"]
    }


@router.get("/jobs")
async def list_ingestion_jobs(
    user: User = Depends(get_current_user)
):
    """List all ingestion jobs for current user"""
    user_jobs = {
        job_id: {
            "job_id": job_id,
            "status": job["status"],
            "started_at": job["started_at"],
            "has_stats": job["stats"] is not None
        }
        for job_id, job in ingestion_jobs.items()
        if job["user_id"] == str(user.id)
    }
    
    return {"jobs": list(user_jobs.values())}


@router.post("/test-connection")
async def test_connection(
    connection_string: str,
    user: User = Depends(get_current_user)
):
    """
    Test database connection without running ingestion
    
    This validates the connection string and checks database accessibility.
    """
    from sqlalchemy import create_engine, text
    
    try:
        # Convert async URL to sync for testing
        sync_url = connection_string.replace("postgresql+asyncpg://", "postgresql://")
        
        # Create engine and test connection
        engine = create_engine(sync_url, pool_pre_ping=True)
        
        with engine.connect() as conn:
            # Test query
            result = conn.execute(text("SELECT current_database(), version()"))
            row = result.fetchone()
            
            db_name = row[0]
            version = row[1].split(',')[0]  # Get PostgreSQL version
            
            # Count tables
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """))
            table_count = result.scalar()
            
        engine.dispose()
        
        return {
            "status": "success",
            "database": db_name,
            "version": version,
            "table_count": table_count,
            "message": "Connection successful"
        }
        
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Connection failed: {str(e)}"
        )


async def _run_ingestion_background(
    job_id: str,
    catalog_session: AsyncSession,
    target_connection_string: str,
    schema: str,
    table_pattern: str,
    enrich: bool
):
    """Background task for running ingestion"""
    try:
        logger.info(f"Starting background ingestion job {job_id}")
        
        stats = await run_metadata_ingestion(
            catalog_session=catalog_session,
            target_connection_string=target_connection_string,
            schema=schema,
            table_pattern=table_pattern,
            enrich=enrich
        )
        
        # Update job status
        ingestion_jobs[job_id]["status"] = "completed"
        ingestion_jobs[job_id]["stats"] = stats
        ingestion_jobs[job_id]["completed_at"] = datetime.utcnow()
        
        logger.info(f"Ingestion job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Background ingestion job {job_id} failed: {e}")
        ingestion_jobs[job_id]["status"] = "failed"
        ingestion_jobs[job_id]["error"] = str(e)
        ingestion_jobs[job_id]["completed_at"] = datetime.utcnow()
