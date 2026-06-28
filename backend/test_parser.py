import os
import sys
import uuid
import unittest
import tempfile
from datetime import datetime
from unittest.mock import patch

# Ensure backend directory is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.config import settings
from app.models import Product, ComplianceRequest, SupplierDocument, DocumentType, DocValidationStatus
from app.parser import parse_compliance_document, extract_text, extract_expiration_date
from app.worker import process_document_verification

# Set up in-memory database for testing
engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class TestParserModule(unittest.TestCase):
    def setUp(self):
        # Create all tables in the in-memory database
        Base.metadata.create_all(bind=engine)
        self.db = TestingSessionLocal()

        # Create temporary dummy files
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Valid document content
        self.valid_doc_path = os.path.join(self.temp_dir.name, "valid_cert.txt")
        with open(self.valid_doc_path, "w", encoding="utf-8") as f:
            f.write(
                "Certificate No: CERT-SGS-777\n"
                "Testing Laboratory: SGS United Kingdom Ltd\n"
                "This certifies compliance of product with toy safety regulations.\n"
                "Standards Cited: EN 71-1:2014+A1:2018, EN 71-3, REACH\n"
                "Expiration Date: 2028-12-31\n"
                "Result: PASS / COMPLIANT\n"
            )

        # Invalid/Rejected document content
        self.invalid_doc_path = os.path.join(self.temp_dir.name, "invalid_cert.txt")
        with open(self.invalid_doc_path, "w", encoding="utf-8") as f:
            f.write(
                "Certificate No: CERT-FAIL-001\n"
                "Testing Laboratory: Unknown Lab\n"
                "This document is non-compliant.\n"
                "Standards Cited: REACH\n"
                "Detected hazardous chemicals: lead, phthalates.\n"
                "Expiration Date: 2020-01-01\n"
                "Result: FAIL\n"
            )

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=engine)
        self.temp_dir.cleanup()

    def create_test_document(self, file_path, doc_type=DocumentType.SAFETY_CERTIFICATE):
        product = Product(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            sku="SKU-玩具-789",
            name="Test Toy",
            category="Toys",
            destination_market="UK"
        )
        self.db.add(product)
        self.db.commit()

        req = ComplianceRequest(
            id=uuid.uuid4(),
            product_id=product.id,
            status="PENDING"
        )
        self.db.add(req)
        self.db.commit()

        doc = SupplierDocument(
            id=uuid.uuid4(),
            compliance_request_id=req.id,
            doc_type=doc_type,
            status=DocValidationStatus.UPLOADED,
            file_name=os.path.basename(file_path),
            file_url=file_path
        )
        self.db.add(doc)
        self.db.commit()
        return doc

    def test_text_extraction(self):
        text = extract_text(self.valid_doc_path)
        self.assertIn("CERT-SGS-777", text)
        self.assertIn("SGS United Kingdom Ltd", text)

    def test_expiration_date_extraction(self):
        text = extract_text(self.valid_doc_path)
        exp_date = extract_expiration_date(text)
        self.assertEqual(exp_date, "2028-12-31")

        text_invalid = extract_text(self.invalid_doc_path)
        exp_date_invalid = extract_expiration_date(text_invalid)
        self.assertEqual(exp_date_invalid, "2020-01-01")

    def test_parse_compliance_document_valid(self):
        parsed = parse_compliance_document(self.valid_doc_path, "SAFETY_CERTIFICATE")
        self.assertEqual(parsed["document_id"], "CERT-SGS-777")
        self.assertEqual(parsed["testing_laboratory"], "SGS United Kingdom Ltd")
        self.assertTrue(parsed["is_accredited"])
        self.assertIn("EN 71-1:2014+A1:2018", parsed["standards_cited"])
        self.assertIn("EN 71-3", parsed["standards_cited"])
        self.assertEqual(parsed["declaration_of_conformity_status"], "VALID")
        self.assertEqual(parsed["expiration_date"], "2028-12-31")
        self.assertEqual(parsed["hazards_identified"], [])
        self.assertTrue(parsed["matches_product_sku"])

    def test_parse_compliance_document_invalid(self):
        parsed = parse_compliance_document(self.invalid_doc_path, "SAFETY_CERTIFICATE")
        self.assertEqual(parsed["document_id"], "CERT-FAIL-001")
        self.assertEqual(parsed["testing_laboratory"], "UNKNOWN")
        self.assertFalse(parsed["is_accredited"])
        self.assertEqual(parsed["declaration_of_conformity_status"], "INVALID")
        self.assertEqual(parsed["expiration_date"], "2020-01-01")
        self.assertIn("lead", parsed["hazards_identified"])
        self.assertIn("phthalates", parsed["hazards_identified"])

    @patch("app.database.SessionLocal")
    def test_celery_task_successful_validation(self, mock_session_local):
        mock_session_local.return_value = self.db
        
        doc = self.create_test_document(self.valid_doc_path)
        
        # Run process_document_verification
        result = process_document_verification(str(doc.id))
        
        self.assertEqual(result["status"], "VALIDATED")
        
        # Reload doc from db
        self.db.expire_all()
        updated_doc = self.db.query(SupplierDocument).filter(SupplierDocument.id == doc.id).first()
        
        self.assertEqual(updated_doc.status, DocValidationStatus.VALIDATED)
        self.assertIsNotNone(updated_doc.raw_ocr_text)
        self.assertIn("CERT-SGS-777", updated_doc.raw_ocr_text)
        self.assertIsNotNone(updated_doc.extracted_metadata)
        self.assertEqual(updated_doc.extracted_metadata["document_id"], "CERT-SGS-777")
        self.assertEqual(updated_doc.extracted_metadata["declaration_of_conformity_status"], "VALID")

    @patch("app.database.SessionLocal")
    def test_celery_task_rejection_due_to_hazards_and_expiry(self, mock_session_local):
        mock_session_local.return_value = self.db
        
        doc = self.create_test_document(self.invalid_doc_path)
        
        # Run process_document_verification
        result = process_document_verification(str(doc.id))
        
        self.assertEqual(result["status"], "REJECTED")
        
        # Reload doc from db
        self.db.expire_all()
        updated_doc = self.db.query(SupplierDocument).filter(SupplierDocument.id == doc.id).first()
        
        self.assertEqual(updated_doc.status, DocValidationStatus.REJECTED)
        self.assertIsNotNone(updated_doc.extracted_metadata)
        self.assertEqual(updated_doc.extracted_metadata["declaration_of_conformity_status"], "INVALID")
        self.assertIn("lead", updated_doc.extracted_metadata["hazards_identified"])

    @patch("app.database.SessionLocal")
    def test_celery_task_document_not_found(self, mock_session_local):
        mock_session_local.return_value = self.db
        
        non_existent_id = str(uuid.uuid4())
        result = process_document_verification(non_existent_id)
        
        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(result["error"], "Document not found")

if __name__ == "__main__":
    unittest.main()
