# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import (
    auth_router,
    table_router,
    column_router,
    data_router,
    database_router
)
from app.routes.ingestion_routes import router as ingestion_router
import os
from contextlib import asynccontextmanager
from app.config import settings
from app.database import create_tables, drop_tables
from app.utils.logger import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Gold Catalog MVP..")
    await create_tables()
    logger.info("Database initialization completed")
    
    # Set environment variables for LangSmith if configured
    if settings.LANGSMITH_API_KEY:
        os.environ["LANGSMITH_API_KEY"] = settings.LANGSMITH_API_KEY
        os.environ["LANGSMITH_PROJECT_NAME"] = settings.LANGSMITH_PROJECT_NAME or "gold-catalog"
        os.environ["LANGSMITH_TRACING"] = settings.LANGSMITH_TRACING or "false"
        os.environ["LANGSMITH_ENDPOINT"] = settings.LANGSMITH_ENDPOINT or "https://api.smith.langchain.com"

    yield
    
    # Shutdown
    logger.info("Shutting down...")
    # Note: Drop tables removed for production safety
    # await drop_tables()


# Initialize FastAPI app
app = FastAPI(
    title="Gold Catalog MVP",
    description="Metadata management system with GPT-powered enrichment",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(database_router)
app.include_router(table_router)
app.include_router(column_router)
app.include_router(data_router)
app.include_router(ingestion_router)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "gold-catalog-mvp",
        "version": "2.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Gold Catalog MVP API",
        "docs": "/docs",
        "health": "/health"
    }