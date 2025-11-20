from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/catalogdb"
    
    LANGSMITH_API_KEY: Optional[str] = None
    LANGSMITH_PROJECT_NAME: Optional[str] = None
    LANGSMITH_TRACING: Optional[str] = None
    LANGSMITH_ENDPOINT: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # CORS
    ALLOWED_ORIGINS: list = ["http://localhost:3001", "http://localhost:5173","http://localhost:3002", "http://localhost:3000"]
    DEBUG: bool = True


    class Config:
        env_file = ".env"

settings = Settings()
