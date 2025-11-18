"""
SQLAlchemy Models for Metadata Management System
"""

from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, ForeignKey,
    Enum, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import enum
import uuid

# Import Base from models.base
from .base import Base


# ============================================
# ENUMS
# ============================================
class Role(enum.Enum):
    viewer = "viewer"
    curator = "curator"
    admin = "admin"


# ============================================
# 1. USER TABLE
# ============================================
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255))
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(Role), nullable=False, default=Role.viewer)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    # (optional: add back_populates if you want)
    # tables = relationship("Table", back_populates="owner")


# ============================================
# 2. TABLE METADATA
# ============================================
class Table(Base):
    __tablename__ = "tables"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    technical_name = Column(String(255), unique=True, index=True, nullable=False)
    display_name = Column(String(255))
    description = Column(Text)
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    business_purpose = Column(Text)
    status = Column(String(50), default="active")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    columns = relationship("ColumnMetadata", back_populates="table", cascade="all, delete-orphan")
    # owner = relationship("User", back_populates="tables")


# ============================================
# 3. COLUMN METADATA
# ============================================
class ColumnMetadata(Base):
    __tablename__ = "columns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    table_id = Column(UUID(as_uuid=True), ForeignKey("tables.id"), index=True, nullable=False)

    name = Column(String(255), nullable=False)
    data_type = Column(String(100))
    is_nullable = Column(Boolean)
    constraints = Column(Text)
    business_description = Column(Text)
    sample_values = Column(Text)

    version = Column(String, default=1)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    table = relationship("Table", back_populates="columns")


# ============================================
# 4. AUDIT LOG TABLE
# ============================================
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    action_type = Column(String(100), nullable=False)
    target_type = Column(String(100), nullable=False)
    target_id = Column(UUID(as_uuid=True), nullable=True)

    before = Column(Text, nullable=True)
    after = Column(Text, nullable=True)

    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # user = relationship("User")

