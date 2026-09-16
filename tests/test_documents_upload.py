import sys
import os
import io

# Add project root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.main import app
from backend.database.connection import engine, Base

# Ensure database tables exist before testing
Base.metadata.create_all(bind=engine)

client = TestClient(app)

def create_sample_pdf_bytes():
    """Generates a minimal valid PDF byte sequence."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n"
        b"xref\n0 4\n0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n0000000117 00000 n \n"
        b"trailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n190\n%%EOF\n"
    )

def test_upload_valid_pdf():
    """Test uploading a valid PDF document."""
    pdf_content = create_sample_pdf_bytes()
    files = {
        "file": ("attention_is_all_you_need.pdf", io.BytesIO(pdf_content), "application/pdf")
    }
    data = {
        "title": "Attention Is All You Need"
    }

    response = client.post("/documents/upload", files=files, data=data)
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    
    result = response.json()
    assert result["status"] == "success"
    assert "document_id" in result
    assert result["filename"] == "attention_is_all_you_need.pdf"
    assert result["title"] == "Attention Is All You Need"
    assert result["upload_status"] == "uploaded"
    print(f"[PASS] Valid PDF upload test passed. Document ID: {result['document_id']}")
    return result["document_id"]

def test_reject_non_pdf():
    """Test that non-PDF files are rejected with HTTP 400."""
    text_content = b"This is just a plain text file, not a PDF."
    files = {
        "file": ("notes.txt", io.BytesIO(text_content), "text/plain")
    }

    response = client.post("/documents/upload", files=files)
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    assert "Only PDF files" in response.json()["detail"]
    print("[PASS] Non-PDF file rejection test passed.")

def test_reject_corrupt_pdf():
    """Test that files with .pdf extension but invalid header are rejected."""
    corrupt_content = b"INVALID_HEADER_NOT_A_REAL_PDF"
    files = {
        "file": ("fake.pdf", io.BytesIO(corrupt_content), "application/pdf")
    }

    response = client.post("/documents/upload", files=files)
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    assert "Corrupt or invalid PDF" in response.json()["detail"]
    print("[PASS] Corrupt PDF rejection test passed.")

def test_list_and_get_document(doc_id: int):
    """Test listing documents and fetching by ID."""
    # List documents
    list_res = client.get("/documents/")
    assert list_res.status_code == 200
    assert list_res.json()["total_documents"] >= 1

    # Get single document
    get_res = client.get(f"/documents/{doc_id}")
    assert get_res.status_code == 200
    assert get_res.json()["document"]["id"] == doc_id
    print(f"[PASS] List and Get document details test passed for ID: {doc_id}")

if __name__ == "__main__":
    print("=" * 60)
    print(" Running Document Upload Tests")
    print("=" * 60)
    uploaded_id = test_upload_valid_pdf()
    test_reject_non_pdf()
    test_reject_corrupt_pdf()
    test_list_and_get_document(uploaded_id)
    print("=" * 60)
    print("[OK] All Document Upload Tests Passed Successfully!")
    print("=" * 60)
