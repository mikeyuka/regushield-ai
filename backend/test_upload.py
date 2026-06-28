import os
import sys
import unittest
import shutil

# Ensure backend directory is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app, UPLOAD_DIR
from app.models import DocumentType

class TestUploadRoute(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        # Clear uploads folder for clean state if needed, but not strictly necessary
        if os.path.exists(UPLOAD_DIR):
            for file in os.listdir(UPLOAD_DIR):
                file_path = os.path.join(UPLOAD_DIR, file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(e)

    def test_upload_valid_pdf_with_doc_type(self):
        # Create a mock PDF file content
        file_content = b"%PDF-1.4 mock content"
        files = {"file": ("test_report.pdf", file_content, "application/pdf")}
        data = {"doc_type": "SAFETY_CERTIFICATE"}

        response = self.client.post("/api/v1/upload", files=files, data=data)
        
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        
        self.assertEqual(json_data["file_name"], "test_report.pdf")
        self.assertTrue(json_data["saved_path"].startswith("backend/uploads/"))
        self.assertTrue(json_data["saved_path"].endswith("_test_report.pdf"))
        self.assertTrue(json_data["file_url"].startswith("/static/"))
        self.assertTrue(json_data["file_url"].endswith("_test_report.pdf"))
        self.assertEqual(json_data["doc_type"], "SAFETY_CERTIFICATE")

        # Verify file is physically saved on disk in UPLOAD_DIR
        saved_filename = os.path.basename(json_data["saved_path"])
        full_saved_path = os.path.join(UPLOAD_DIR, saved_filename)
        self.assertTrue(os.path.exists(full_saved_path))
        with open(full_saved_path, "rb") as f:
            self.assertEqual(f.read(), file_content)

    def test_upload_valid_png_no_doc_type(self):
        file_content = b"\x89PNG\r\n\x1a\n mock content"
        files = {"file": ("image.png", file_content, "image/png")}

        response = self.client.post("/api/v1/upload", files=files)
        
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        
        self.assertEqual(json_data["file_name"], "image.png")
        self.assertTrue(json_data["saved_path"].endswith("_image.png"))
        self.assertIsNone(json_data["doc_type"])

    def test_upload_invalid_extension(self):
        file_content = b"some plain text"
        files = {"file": ("test.txt", file_content, "text/plain")}

        response = self.client.post("/api/v1/upload", files=files)
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "File extension not allowed")

    def test_serve_static_files(self):
        # First, upload a file
        file_content = b"image content"
        files = {"file": ("icon.png", file_content, "image/png")}
        response = self.client.post("/api/v1/upload", files=files)
        file_url = response.json()["file_url"]

        # Request the static file URL
        static_response = self.client.get(file_url)
        self.assertEqual(static_response.status_code, 200)
        self.assertEqual(static_response.content, file_content)

if __name__ == "__main__":
    unittest.main()
