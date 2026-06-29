import os
import uuid
import shutil
import random
import string
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.config import settings
from app.database import SessionLocal
from app.models import DocumentType, Product, ComplianceRequest, SupplierDocument, ComplianceStatus, DocValidationStatus
from app.worker import process_document_verification
from app.payments import create_stripe_payment_intent, create_gocardless_billing_request
from app.init_db import init_db

class PaymentRequest(BaseModel):
    amount: int
    email: str

# Determine backend base directory and upload storage path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

# Automatically create local upload storage directory on startup
os.makedirs(UPLOAD_DIR, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database tables
    try:
        init_db()
    except Exception as e:
        print(f"Error during database initialization: {e}")
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files handler to serve uploaded files under /static URL path
app.mount("/static", StaticFiles(directory=UPLOAD_DIR), name="static")

@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "service": "ReguShield AI"
    }

@app.get("/health")
def healthcheck():
    db = SessionLocal()
    try:
        # Simple query to check DB connectivity
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "service": "ReguShield AI",
            "database": "connected"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")
    finally:
        db.close()

@app.post(f"{settings.API_V1_STR}/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    doc_type: Optional[DocumentType] = Form(None)
):
    original_name = file.filename
    if not original_name:
        raise HTTPException(status_code=400, detail="Filename cannot be empty")

    _, ext = os.path.splitext(original_name)
    allowed_extensions = {".pdf", ".png", ".jpg", ".jpeg", ".docx"}

    if ext.lower() not in allowed_extensions:
        raise HTTPException(status_code=400, detail="File extension not allowed")

    # Generate unique, UUID-prefixed filename
    unique_id = uuid.uuid4()
    base_filename = os.path.basename(original_name)
    unique_filename = f"{unique_id}_{base_filename}"

    # Target path on disk
    saved_file_path = os.path.join(UPLOAD_DIR, unique_filename)

    # Save file contents
    try:
        with open(saved_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    db = SessionLocal()
    try:
        # Generate unique SKU
        while True:
            sku_suffix = "".join(random.choices(string.digits, k=5))
            sku = f"SKU-{sku_suffix}"
            if not db.query(Product).filter(Product.sku == sku).first():
                break

        product_name = os.path.splitext(original_name)[0]
        product_name = product_name.replace("_", " ").replace("-", " ").title()

        product = Product(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            sku=sku,
            name=product_name,
            category="Chemical Ingestion",
            destination_market="UK"
        )
        db.add(product)

        compliance_request = ComplianceRequest(
            id=uuid.uuid4(),
            product_id=product.id,
            status=ComplianceStatus.PENDING
        )
        db.add(compliance_request)

        # Default doc_type to SAFETY_CERTIFICATE if not provided
        resolved_doc_type = doc_type or DocumentType.SAFETY_CERTIFICATE

        supplier_document = SupplierDocument(
            id=uuid.uuid4(),
            compliance_request_id=compliance_request.id,
            doc_type=resolved_doc_type,
            status=DocValidationStatus.UPLOADED,
            file_name=original_name,
            file_url=f"/static/{unique_filename}"
        )
        db.add(supplier_document)
        db.commit()

        # Trigger verification task asynchronously using FastAPI BackgroundTasks
        background_tasks.add_task(process_document_verification, str(supplier_document.id))

        return {
            "document_id": str(supplier_document.id),
            "compliance_request_id": str(compliance_request.id),
            "product_id": str(product.id),
            "file_name": original_name,
            "saved_path": f"backend/uploads/{unique_filename}",
            "file_url": f"/static/{unique_filename}",
            "doc_type": resolved_doc_type.value if hasattr(resolved_doc_type, "value") else str(resolved_doc_type)
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database integration failed: {str(e)}")
    finally:
        db.close()

@app.get(f"{settings.API_V1_STR}/compliance/documents/{{document_id}}/status")
def get_document_status(document_id: str):
    db = SessionLocal()
    try:
        try:
            doc_uuid = uuid.UUID(document_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid document_id format")

        doc = db.query(SupplierDocument).filter(SupplierDocument.id == doc_uuid).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        comp_req = doc.compliance_request

        response_data = {
            "document_id": str(doc.id),
            "status": doc.status.value if hasattr(doc.status, "value") else str(doc.status),
            "extracted_metadata": doc.extracted_metadata,
            "raw_ocr_text": doc.raw_ocr_text,
            "error_log": doc.error_log,
            "errors": doc.error_log,
            "compliance_request_status": None,
            "generated_pdf_url": None
        }

        if comp_req:
            response_data["compliance_request_status"] = comp_req.status.value if hasattr(comp_req.status, "value") else str(comp_req.status)
            if comp_req.status == ComplianceStatus.COMPLETED:
                response_data["generated_pdf_url"] = comp_req.generated_pdf_url

        return response_data
    finally:
        db.close()


@app.post(f"{settings.API_V1_STR}/payments/stripe/create-intent")
def stripe_create_intent(payload: PaymentRequest):
    try:
        res = create_stripe_payment_intent(payload.amount, payload.email)
        return {
            "client_secret": res["client_secret"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(f"{settings.API_V1_STR}/payments/gocardless/create-request")
def gocardless_create_request(payload: PaymentRequest):
    try:
        res = create_gocardless_billing_request(payload.amount, payload.email)
        return {
            "billing_request_id": res["billing_request_id"],
            "redirect_url": res["redirect_url"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

