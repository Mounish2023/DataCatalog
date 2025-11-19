"""
SQLAlchemy Models for Metadata Management System
"""

from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, ForeignKey,
    Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import enum
import uuid
from .base import Base


# ============================================
# ENUMS
# ============================================
class Role(enum.Enum):
    viewer = "viewer"
    curator = "curator"
    admin = "admin"


class Sensitivity(enum.Enum):
    public = "public"
    internal = "internal"
    confidential = "confidential"
    pii = "pii"


class TableType(enum.Enum):
    fact = "fact"
    dimension = "dimension"
    reference = "reference"
    staging = "staging"
    raw = "raw"
    view = "view"


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

# ==========================================================
# 1. DATABASE METADATA
# ==========================================================

class DatabaseMetadata(Base):
    __tablename__ = "database_metadata"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    database_name = Column(String(255), nullable=False, unique=True, index=True)
    business_domain = Column(String(255))     # e.g., Sales, Finance, HR
    description = Column(Text)
    sensitivity = Column(Enum(Sensitivity), default=Sensitivity.internal)

    owner = Column(String(255))               # business owner/steward
    refresh_frequency = Column(String(100))   # daily, hourly, real-time
    source_systems = Column(Text)             # list of upstream systems

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tables = relationship(
        "TableMetadata",
        back_populates="database",
        cascade="all, delete-orphan"
    )


# ==========================================================
# 2. TABLE METADATA
# ==========================================================

class TableMetadata(Base):
    __tablename__ = "table_metadata"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    database_id = Column(UUID(as_uuid=True), ForeignKey("database_metadata.id"), nullable=False)

    technical_name = Column(String(255), unique=True, index=True, nullable=False)
    display_name = Column(String(255))
    description = Column(Text)

    table_type = Column(Enum(TableType), nullable=False, default=TableType.raw)
    business_purpose = Column(Text)
    status = Column(String(50), default="active")

    refresh_frequency = Column(String(100))
    sla_info = Column(Text)

    primary_key = Column(String(255))         # optional PK info
    foreign_keys = Column(Text)               # optional FK list as text
    cardinality_overview = Column(Text)       # e.g., 1:M relations

    owner = Column(String(255))               # table-level data owner/steward
    data_sensitivity = Column(Enum(Sensitivity), default=Sensitivity.internal)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    database = relationship("DatabaseMetadata", back_populates="tables")
    columns = relationship(
        "ColumnMetadata",
        back_populates="table",
        cascade="all, delete-orphan"
    )


# ==========================================================
# 3. COLUMN METADATA
# ==========================================================

class ColumnMetadata(Base):
    __tablename__ = "column_metadata"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    table_id = Column(UUID(as_uuid=True), ForeignKey("table_metadata.id"), nullable=False)

    column_name = Column(String(255), nullable=False)
    data_type = Column(String(255))
    description = Column(Text)

    is_primary_key = Column(Boolean, default=False)
    is_foreign_key = Column(Boolean, default=False)
    is_nullable = Column(Boolean, default=True)
    is_pii = Column(Boolean, default=False)

    cardinality = Column(String(100))        # unique, low-card, high-card
    valid_values = Column(Text)
    example_value = Column(String(255))

    transformation_logic = Column(Text)      # if derived
    downstream_usage = Column(Text)          # how analytics use this column

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    table = relationship("TableMetadata", back_populates="columns")

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

