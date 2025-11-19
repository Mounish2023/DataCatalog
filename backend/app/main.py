# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import (
    auth_router,
    table_router,
    column_router,
    data_router
)
import os
from contextlib import asynccontextmanager
from app.config import settings
from app.database import create_tables
from app.utils.logger import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Gold Catalog MVP..")
    await create_tables()
    logger.info("Database initialization completed")
    os.environ["LANGSMITH_API_KEY"] = settings.LANGSMITH_API_KEY
    os.environ["LANGSMITH_PROJECT_NAME"] = settings.LANGSMITH_PROJECT_NAME
    os.environ["LANGSMITH_TRACING"] = settings.LANGSMITH_TRACING
    os.environ["LANGSMITH_ENDPOINT"] =settings.LANGSMITH_ENDPOINT

    yield
    # Shutdown
    logger.info("Shutting down...")


# Initialize FastAPI app
app = FastAPI(title="Gold Catalog MVP", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers

app.include_router(auth_router)
app.include_router(table_router)
app.include_router(column_router)
app.include_router(data_router)

# Export oauth2_scheme for use in other modules
# app.oauth2_scheme = oauth2_scheme
