"""
Database models for Bank Statement Distribution System.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, 
    Text, BigInteger, Enum as SQLEnum, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class ProcessingStatus(enum.Enum):
    """Processing status enumeration."""
    UNPROCESSED = "unprocessed"
    DELIVERED = "delivered"
    PENDING = "pending"


class ActiveStatus(enum.Enum):
    """Active status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"


class OperationType(enum.Enum):
    """Operation type enumeration for audit log."""
    DISCOVERY = "discovery"
    GROUPING = "grouping"
    PACKAGING = "packaging"
    DELIVERY = "delivery"
    ERROR = "error"
    SUMMARY_REPORT = "summary_report"


class OperationOutcome(enum.Enum):
    """Operation outcome enumeration for audit log."""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"


class ConnectivityStatus(enum.Enum):
    """Connectivity status enumeration."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class Financier(Base):
    """Financier table model."""
    __tablename__ = 'financiers'
    
    financier_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email_address = Column(String(320), nullable=False, unique=True)
    active_status = Column(SQLEnum(ActiveStatus), nullable=False, default=ActiveStatus.ACTIVE)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    entity_mappings = relationship("EntityMapping", back_populates="financier", cascade="all, delete-orphan")
    deliveries = relationship("DeliveryStatus", back_populates="financier", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Financier(id={self.financier_id}, name='{self.name}', email='{self.email_address}')>"


class EntityMapping(Base):
    """Entity mapping table model."""
    __tablename__ = 'entity_mappings'
    
    mapping_id = Column(Integer, primary_key=True, autoincrement=True)
    financier_id = Column(Integer, ForeignKey('financiers.financier_id'), nullable=False)
    entity_name = Column(String(255), nullable=False)
    authorized_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    financier = relationship("Financier", back_populates="entity_mappings")
    
    # Indexes
    __table_args__ = (
        Index('idx_entity_mappings_financier', 'financier_id'),
        Index('idx_entity_mappings_entity', 'entity_name'),
    )
    
    def __repr__(self):
        return f"<EntityMapping(financier_id={self.financier_id}, entity='{self.entity_name}')>"


class StatementFile(Base):
    """Statement file tracking table model."""
    __tablename__ = 'statement_files'
    
    file_id = Column(Integer, primary_key=True, autoincrement=True)
    file_path = Column(Text, nullable=False, unique=True)
    bank_name = Column(String(255), nullable=False)
    entity_name = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    last_modified = Column(DateTime, nullable=False)
    checksum = Column(String(64), nullable=False)  # SHA-256
    status = Column(SQLEnum(ProcessingStatus), nullable=False, default=ProcessingStatus.UNPROCESSED)
    discovered_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    deliveries = relationship("DeliveryStatus", back_populates="statement_file", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_statement_files_status', 'status'),
        Index('idx_statement_files_entity', 'entity_name'),
        Index('idx_statement_files_checksum', 'checksum'),
    )
    
    def __repr__(self):
        return f"<StatementFile(id={self.file_id}, entity='{self.entity_name}', status='{self.status.value}')>"


class DeliveryStatus(Base):
    """Delivery status tracking table model."""
    __tablename__ = 'delivery_status'
    
    delivery_id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(Integer, ForeignKey('statement_files.file_id'), nullable=False)
    financier_id = Column(Integer, ForeignKey('financiers.financier_id'), nullable=False)
    status = Column(SQLEnum(ProcessingStatus), nullable=False, default=ProcessingStatus.UNPROCESSED)
    delivery_timestamp = Column(DateTime, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    statement_file = relationship("StatementFile", back_populates="deliveries")
    financier = relationship("Financier", back_populates="deliveries")
    
    # Indexes
    __table_args__ = (
        Index('idx_delivery_status_file', 'file_id'),
        Index('idx_delivery_status_financier', 'financier_id'),
        Index('idx_delivery_status_status', 'status'),
        Index('idx_delivery_status_composite', 'file_id', 'financier_id'),
    )
    
    def __repr__(self):
        return f"<DeliveryStatus(file_id={self.file_id}, financier_id={self.financier_id}, status='{self.status.value}')>"


class AuditLog(Base):
    """Audit log table model."""
    __tablename__ = 'audit_logs'
    
    log_id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    operation_type = Column(SQLEnum(OperationType), nullable=False, index=True)
    outcome = Column(SQLEnum(OperationOutcome), nullable=False)
    component_name = Column(String(100), nullable=True)
    entity_name = Column(String(255), nullable=True, index=True)
    financier_email = Column(String(320), nullable=True, index=True)
    file_path = Column(Text, nullable=True)
    attachment_names = Column(Text, nullable=True)  # JSON array
    attachment_sizes = Column(Text, nullable=True)  # JSON array
    checksum = Column(String(64), nullable=True)
    error_type = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    context_info = Column(Text, nullable=True)  # JSON object
    
    # Indexes
    __table_args__ = (
        Index('idx_audit_logs_timestamp', 'timestamp'),
        Index('idx_audit_logs_operation', 'operation_type'),
        Index('idx_audit_logs_entity', 'entity_name'),
        Index('idx_audit_logs_financier', 'financier_email'),
    )
    
    def __repr__(self):
        return f"<AuditLog(id={self.log_id}, type='{self.operation_type.value}', outcome='{self.outcome.value}')>"


class ProcessingState(Base):
    """Processing state table for fault tolerance."""
    __tablename__ = 'processing_state'
    
    state_id = Column(Integer, primary_key=True, autoincrement=True)
    execution_id = Column(String(36), nullable=False, unique=True)  # UUID
    file_id = Column(Integer, ForeignKey('statement_files.file_id'), nullable=False)
    processing_status = Column(SQLEnum(ProcessingStatus), nullable=False)
    target_financiers = Column(Text, nullable=True)  # JSON array of financier IDs
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_processing_state_execution', 'execution_id'),
        Index('idx_processing_state_file', 'file_id'),
    )
    
    def __repr__(self):
        return f"<ProcessingState(execution_id='{self.execution_id}', file_id={self.file_id})>"


class SystemHealth(Base):
    """System health tracking table."""
    __tablename__ = 'system_health'
    
    health_id = Column(Integer, primary_key=True, autoincrement=True)
    last_execution_timestamp = Column(DateTime, nullable=True)
    last_execution_status = Column(String(50), nullable=True)
    gdrive_connectivity = Column(SQLEnum(ConnectivityStatus), nullable=True)
    email_connectivity = Column(SQLEnum(ConnectivityStatus), nullable=True)
    db_connectivity = Column(SQLEnum(ConnectivityStatus), nullable=True)
    pending_deliveries_count = Column(Integer, nullable=False, default=0)
    failed_deliveries_count = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<SystemHealth(last_execution={self.last_execution_timestamp})>"


class ExecutionSummary(Base):
    """Execution summary table."""
    __tablename__ = 'execution_summaries'
    
    summary_id = Column(Integer, primary_key=True, autoincrement=True)
    execution_id = Column(String(36), nullable=False, unique=True)  # UUID
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    duration_seconds = Column(Integer, nullable=False)
    files_discovered = Column(Integer, nullable=False, default=0)
    files_processed = Column(Integer, nullable=False, default=0)
    emails_sent = Column(Integer, nullable=False, default=0)
    delivery_failures = Column(Integer, nullable=False, default=0)
    failure_details = Column(Text, nullable=True)  # JSON array
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_execution_summaries_execution', 'execution_id'),
        Index('idx_execution_summaries_start_time', 'start_time'),
    )
    
    def __repr__(self):
        return f"<ExecutionSummary(execution_id='{self.execution_id}', files_processed={self.files_processed})>"
