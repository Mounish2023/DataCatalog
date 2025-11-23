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
    description: Optional[str] = None
    is_primary_key: Optional[bool] = None
    is_foreign_key: Optional[bool] = None
    is_nullable: Optional[bool] = None
    is_pii: Optional[bool] = None
    cardinality: Optional[str] = None
    valid_values: Optional[str] = None
    example_value: Optional[str] = None
    transformation_logic: Optional[str] = None
    downstream_usage: Optional[str] = None

class IngestRequest(BaseModel):
    target_db_url: str
    schema: Optional[str] = "public"
    name_like: Optional[str] = "gold%"
