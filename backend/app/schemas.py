# backend/app/schemas.py
from pydantic import BaseModel
from typing import Optional, List

class UserCreate(BaseModel):
    email: str
    name: Optional[str]
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TableCreate(BaseModel):
    technical_name: str
    display_name: Optional[str]
    description: Optional[str]

class TableUpdate(BaseModel):
    display_name: Optional[str]
    description: Optional[str]
    owner_user_id: Optional[str]
    business_purpose: Optional[str]
    status: Optional[str]

class ColumnUpdate(BaseModel):
    business_description: Optional[str] = None
    constraints: Optional[str] = None
    sample_values: Optional[str] = None

class IngestRequest(BaseModel):
    target_db_url: str
    schema: Optional[str] = "public"
    name_like: Optional[str] = "gold%"
