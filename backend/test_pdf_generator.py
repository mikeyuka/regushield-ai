import os
import sys
import uuid
import unittest
import tempfile
from datetime import datetime
from unittest.mock import patch, MagicMock

# Ensure backend directory is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Product, ComplianceRequest, SupplierDocument, DocumentType, DocValidationStatus, ComplianceStatus
from app.pdf_generator import compile_pdf_blueprint
from app.worker import process_document_verification

# Set up in-memory database for testing
engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class TestPDFGeneratorModule(unittest.TestCase):
    def setUp(self):
        # Create all tables in the in-memory database
        Base.metadata.create_all(bind=engine)
        self.db = TestingSessionLocal()

        self.product_data = {
            "sku": "SKU-TOY-123",
            "name": "Super Safe Toy Block",
            "category": "Baby Toys",
            "destination_market": "EU"
        }

        self.validation_results = [
            {
                "file_name": "toy_safety_cert.pdf",
                "doc_type": "SAFETY_CERTIFICATE",
                "status": "VALIDATED",
                "extracted_metadata": {
                    "document_id": "CERT-SGS-007",
                    "testing_laboratory": "SGS UK Ltd",
                    "is_accredited": True,
                    "standards_cited": ["EN 71-1:2014+A1:2018", "EN 71-3"],
                    "declaration_of_conformity_status": "VALID",
                    "expiration_date": "2030-01-01",
                    "hazards_identified": []
                }
            },
            {
                "file_name": "msds_report.pdf",
                "doc_type": "MSDS",
                "status": "VALIDATED",
                "extracted_metadata": {
                    "document_id": "MSDS-999",
                    "testing_laboratory": "Intertek Services",
                    "is_accredited": True,
                    "standards_cited": ["REACH"],
                    "declaration_of_conformity_status": "VALID",
                    "expiration_date": "2029-05-15",
                    "hazards_identified": []
                }
            }
        ]

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=engine)

    @patch("app.pdf_generator.UPLOAD_DIR")
    @patch.dict("sys.modules", {"weasyprint": None})
    def test_compile_pdf_blueprint_fallback(self, mock_upload_dir):
        # Create a temporary directory for test outputs
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_upload_dir.__str__.return_value = temp_dir
            # Force UPLOAD_DIR to be our temp directory
            with patch("app.pdf_generator.UPLOAD_DIR", temp_dir):
                output_filename = "test_blueprint_fallback.pdf"
                
                # Call compile
                static_url = compile_pdf_blueprint(
                    product_data=self.product_data,
                    validation_results=self.validation_results,
                    output_filename=output_filename
                )
                
                # Fallback should produce a .html file
                self.assertTrue(static_url.endswith(".html"))
                self.assertIn("/static/test_blueprint_fallback.html", static_url)
                
                # Verify file is written
                html_path = os.path.join(temp_dir, "test_blueprint_fallback.html")
                self.assertTrue(os.path.exists(html_path))
                
                # Read content and verify
                with open(html_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.assertIn("SKU-TOY-123", content)
                    self.assertIn("Super Safe Toy Block", content)
                    self.assertIn("SGS UK Ltd", content)
                    self.assertIn("EN 71-1:2014+A1:2018", content)
                    self.assertIn("toy_safety_cert.pdf", content)

    @patch("app.pdf_generator.UPLOAD_DIR")
    @patch.dict("sys.modules", {"weasyprint": MagicMock()})
    def test_compile_pdf_blueprint_success_mock(self, mock_upload_dir):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("app.pdf_generator.UPLOAD_DIR", temp_dir):
                # Mock weasyprint HTML class
                mock_html_class = MagicMock()
                mock_html_instance = MagicMock()
                mock_html_class.return_value = mock_html_instance
                
                with patch("weasyprint.HTML", mock_html_class):
                    output_filename = "test_blueprint_success.pdf"
                    
                    static_url = compile_pdf_blueprint(
                        product_data=self.product_data,
                        validation_results=self.validation_results,
                        output_filename=output_filename
                    )
                    
                    # Should return .pdf url
                    self.assertTrue(static_url.endswith(".pdf"))
                    self.assertIn("/static/test_blueprint_success.pdf", static_url)
                    
                    # Verify write_pdf was called
                    mock_html_class.assert_called_once()
                    mock_html_instance.write_pdf.assert_called_once_with(os.path.join(temp_dir, output_filename))

    @patch("app.database.SessionLocal")
    @patch("app.pdf_generator.UPLOAD_DIR")
    def test_worker_compilation_integration(self, mock_upload_dir, mock_session_local):
        mock_session_local.return_value = self.db
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("app.pdf_generator.UPLOAD_DIR", temp_dir):
                # Setup product
                product = Product(
                    id=uuid.uuid4(),
                    user_id=uuid.uuid4(),
                    sku="SKU-TEST-INTEGRATION",
                    name="Integrated Compliance Product",
                    category="Toys",
                    destination_market="UK"
                )
                self.db.add(product)
                self.db.commit()
                
                # Setup compliance request
                comp_req = ComplianceRequest(
                    id=uuid.uuid4(),
                    product_id=product.id,
                    status=ComplianceStatus.PENDING
                )
                self.db.add(comp_req)
                self.db.commit()
                comp_req_id = comp_req.id
                
                # Create a temporary physical file to avoid file-not-found errors during parsing
                dummy_file_path = os.path.join(temp_dir, "test_doc.txt")
                with open(dummy_file_path, "w", encoding="utf-8") as f:
                    f.write(
                        "Certificate No: CERT-INTEG-001\n"
                        "Testing Laboratory: SGS United Kingdom Ltd\n"
                        "Standards Cited: EN 71-1, REACH\n"
                        "Expiration Date: 2030-01-01\n"
                        "Result: PASS\n"
                    )
                
                # Setup supplier document
                doc = SupplierDocument(
                    id=uuid.uuid4(),
                    compliance_request_id=comp_req_id,
                    doc_type=DocumentType.SAFETY_CERTIFICATE,
                    status=DocValidationStatus.UPLOADED,
                    file_name="test_doc.txt",
                    file_url=dummy_file_path
                )
                self.db.add(doc)
                self.db.commit()
                
                # Process document
                result = process_document_verification(str(doc.id))
                
                self.assertEqual(result["status"], "VALIDATED")
                
                # Query updated compliance request
                self.db.expire_all()
                updated_req = self.db.query(ComplianceRequest).filter(ComplianceRequest.id == comp_req_id).first()
                
                self.assertEqual(updated_req.status, ComplianceStatus.COMPLETED)
                self.assertIsNotNone(updated_req.generated_pdf_url)
                self.assertTrue(updated_req.generated_pdf_url.endswith(".html")) # Falls back to HTML because weasyprint is not installed
                self.assertIn(f"blueprint_{comp_req_id}.html", updated_req.generated_pdf_url)
                
                # Verify that the actual file was created on disk
                html_path = os.path.join(temp_dir, f"blueprint_{comp_req_id}.html")
                self.assertTrue(os.path.exists(html_path))

if __name__ == "__main__":
    unittest.main()
