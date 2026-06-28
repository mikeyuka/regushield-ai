from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.types import UUID
from datetime import datetime
import uuid
import enum
from app.database import Base

class AuditLogPlaceholder(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, index=True)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class ComplianceStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPILING = "COMPILING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class DocumentType(str, enum.Enum):
    SAFETY_CERTIFICATE = "SAFETY_CERTIFICATE"
    MSDS = "MSDS"
    ISO_9001 = "ISO_9001"
    TEST_REPORT = "TEST_REPORT"
    DECLARATION_OF_CONFORMITY = "DECLARATION_OF_CONFORMITY"

class DocValidationStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    OCR_COMPLETED = "OCR_COMPLETED"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"

class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    sku = Column(String(100), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    destination_market = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    compliance_requests = relationship(
        "ComplianceRequest",
        back_populates="product",
        cascade="all, delete-orphan"
    )

class ComplianceRequest(Base):
    __tablename__ = "compliance_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(SQLEnum(ComplianceStatus), nullable=False, default=ComplianceStatus.PENDING, index=True)
    generated_pdf_url = Column(Text, nullable=True)
    cost_summary_json = Column(JSON, nullable=True)
    failed_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="compliance_requests")
    supplier_documents = relationship(
        "SupplierDocument",
        back_populates="compliance_request",
        cascade="all, delete-orphan"
    )

class SupplierDocument(Base):
    __tablename__ = "supplier_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    compliance_request_id = Column(UUID(as_uuid=True), ForeignKey("compliance_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    doc_type = Column(SQLEnum(DocumentType), nullable=False)
    status = Column(SQLEnum(DocValidationStatus), nullable=False, default=DocValidationStatus.UPLOADED, index=True)
    file_name = Column(String(255), nullable=False)
    file_url = Column(Text, nullable=False)
    raw_ocr_text = Column(Text, nullable=True)
    extracted_metadata = Column(JSON, nullable=True)
    error_log = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    compliance_request = relationship("ComplianceRequest", back_populates="supplier_documents")

