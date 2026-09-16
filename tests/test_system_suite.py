"""
==============================================================================
AI-Powered Research Paper Intelligence System - Comprehensive Test Suite
==============================================================================
This test suite covers all 12 core requirements for the Minor Project:
  1. Database connection and schema verification
  2. User registration (happy path and duplicate rejection)
  3. User login (credential verification and JWT generation)
  4. PDF upload and automated ingestion pipeline
  5. Invalid file upload validation (MIME and magic-byte checks)
  6. PDF text extraction (PyMuPDF engine, page analysis)
  7. Text preprocessing (cleaning, abstract detection, section segmentation, keywords)
  8. Document storage and relational integrity in MySQL
  9. TF-IDF + Cosine similarity search with valid queries
  10. Search handling when no matching documents exist
  11. Metadata heuristic extraction (Title, Authors, Year, Explicit Keywords)
  12. API error handling (400, 401, 404, 422 edge cases)
==============================================================================
"""

import io
import uuid
from pathlib import Path
import pytest
from sqlalchemy import text
import pymupdf

from backend.database.connection import engine, Base, SessionLocal
from backend.database.models import User, Paper, PaperSection, PaperKeyword
from backend.services.pdf_extractor import extract_text_from_pdf, PDFExtractionError
from backend.services.text_processor import (
    clean_text_content,
    extract_abstract,
    segment_into_sections,
    extract_keywords,
    process_extracted_document,
)
from backend.services.metadata_extractor import MetadataExtractor
from backend.services.search_engine import search_papers_tfidf


# ============================================================================
# 1. Database Connection & Schema Verification
# ============================================================================
def test_01_database_connection(db_session):
    """
    Test 1: Verify direct connectivity to the MySQL database and ensure
    all required relational tables exist and can execute queries.
    """
    # Execute raw SQL query to test round-trip communication
    result = db_session.execute(text("SELECT 1 AS alive;")).scalar()
    assert result == 1, "Database connection failed: SELECT 1 did not return 1"

    # Verify all expected tables are in SQLAlchemy metadata
    inspector = Base.metadata.tables.keys()
    expected_tables = {"users", "papers", "paper_sections", "paper_keywords", "search_logs"}
    for table_name in expected_tables:
        assert table_name in inspector, f"Table '{table_name}' is missing from schema definitions."


# ============================================================================
# 2. User Registration
# ============================================================================
def test_02_user_registration(api_client):
    """
    Test 2: Verify user registration endpoint (POST /auth/register).
    Checks successful registration (HTTP 201) and duplicate rejection (HTTP 400).
    """
    unique_id = uuid.uuid4().hex[:8]
    payload = {
        "username": f"user_{unique_id}",
        "email": f"user_{unique_id}@university.edu",
        "password": "StrongPassword@123",
        "full_name": "Test Researcher",
    }

    # 1. Successful registration
    response = api_client.post("/auth/register", json=payload)
    assert response.status_code == 201, f"Registration failed: {response.text}"
    data = response.json()
    assert data["username"] == payload["username"]
    assert data["email"] == payload["email"]
    assert "password" not in data, "Security violation: Password returned in response"

    # 2. Duplicate registration attempt should be rejected with HTTP 400
    dup_response = api_client.post("/auth/register", json=payload)
    assert dup_response.status_code == 400, "Duplicate user registration was not rejected"
    assert "already taken" in dup_response.json()["detail"].lower() or "already" in dup_response.json()["detail"].lower()


# ============================================================================
# 3. User Login & JWT Generation
# ============================================================================
def test_03_user_login(api_client):
    """
    Test 3: Verify user authentication and JWT token generation (POST /auth/login).
    Tests invalid credentials (HTTP 401) and successful login (HTTP 200 with JWT).
    """
    unique_id = uuid.uuid4().hex[:8]
    username = f"login_user_{unique_id}"
    password = "CorrectPassword!99"

    # Register user first
    reg_payload = {
        "username": username,
        "email": f"{username}@test.org",
        "password": password,
        "full_name": "Auth Tester",
    }
    api_client.post("/auth/register", json=reg_payload)

    # 1. Login with incorrect password -> 401 Unauthorized
    bad_login = api_client.post(
        "/auth/login",
        json={"username": username, "password": "WrongPassword!"},
    )
    assert bad_login.status_code == 401, "Invalid password was not rejected with 401"

    # 2. Login with correct credentials -> 200 OK with Bearer token
    good_login = api_client.post(
        "/auth/login",
        json={"username": username, "password": password},
    )
    assert good_login.status_code == 200, f"Login failed: {good_login.text}"
    token_data = good_login.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    # 3. Use token to access protected endpoint GET /auth/me
    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    me_response = api_client.get("/auth/me", headers=headers)
    assert me_response.status_code == 200
    assert me_response.json()["username"] == username


# ============================================================================
# 4. PDF Upload & Automated Ingestion
# ============================================================================
def test_04_pdf_upload(api_client, sample_pdf_bytes):
    """
    Test 4: Verify end-to-end PDF document upload (POST /documents/upload).
    Checks that the file is received, text is parsed, NLP metadata is extracted,
    and a 201 Created response is returned.
    """
    files = {
        "file": ("sample_paper.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")
    }
    form_data = {
        "title": "Transformer Architectures for Deep Language Intelligence",
        "authors": "Ashish Vaswani, Noam Shazeer",
    }

    response = api_client.post("/documents/upload", files=files, data=form_data)
    assert response.status_code == 201, f"PDF upload failed: {response.text}"

    data = response.json()
    assert data["document_id"] > 0
    assert data["upload_status"] == "completed"
    assert data["total_pages"] == 2
    assert data["total_words"] > 50
    assert len(data["sections"]) >= 2
    assert len(data["keywords"]) >= 2


# ============================================================================
# 5. Invalid File Upload Validation
# ============================================================================
def test_05_invalid_file_upload(api_client):
    """
    Test 5: Verify upload security rejection for non-PDF files and spoofed files.
    """
    # 1. Plain text file upload should be rejected
    text_content = b"This is a plain text file, not a PDF document."
    files = {
        "file": ("malicious.txt", io.BytesIO(text_content), "text/plain")
    }
    response = api_client.post("/documents/upload", files=files)
    assert response.status_code == 400, "Non-PDF file was not rejected"
    assert "only pdf" in response.json()["detail"].lower()

    # 2. File with .pdf extension but invalid magic bytes (spoofed file)
    spoofed_bytes = b"NOT_A_REAL_PDF_HEADER_CONTENT"
    spoofed_files = {
        "file": ("spoofed.pdf", io.BytesIO(spoofed_bytes), "application/pdf")
    }
    spoof_res = api_client.post("/documents/upload", files=spoofed_files)
    assert spoof_res.status_code == 400, "Spoofed non-PDF bytes were not rejected"
    assert "magic bytes" in spoof_res.json()["detail"].lower() or "pdf" in spoof_res.json()["detail"].lower()


# ============================================================================
# 6. PDF Text Extraction Service
# ============================================================================
def test_06_pdf_text_extraction(tmp_path):
    """
    Test 6: Verify direct PDF text extraction using PyMuPDF service.
    Tests page count, per-page text extraction, and empty page handling.
    """
    pdf_path = tmp_path / "extraction_test.pdf"

    # Create test PDF with 2 pages (1 text page, 1 empty page)
    doc = pymupdf.open()
    p1 = doc.new_page()
    p1.insert_textbox(
        pymupdf.Rect(50, 50, 500, 700),
        "Convolutional Neural Networks for Automated Feature Learning in Computer Vision.",
        fontsize=12,
    )
    doc.new_page()  # Blank page 2
    doc.save(str(pdf_path))
    doc.close()

    result = extract_text_from_pdf(pdf_path)
    assert result["status"] == "success"
    assert result["total_pages"] == 2
    assert len(result["pages"]) == 2
    assert result["pages"][0]["has_text"] is True
    assert result["pages"][1]["has_text"] is False
    assert "Convolutional Neural Networks" in result["full_text"]

    # Verify missing file exception
    with pytest.raises(PDFExtractionError):
        extract_text_from_pdf("non_existent_file.pdf")


# ============================================================================
# 7. Text Preprocessing & NLP Pipeline
# ============================================================================
def test_07_text_preprocessing():
    """
    Test 7: Verify text normalization, abstract detection, section segmentation,
    and TF-IDF keyword extraction.
    """
    raw_text = (
        "  12  Transformer Networks for Deep NLP   \n\n\n\n"
        "Abstract\n"
        "This paper introduces an attention-based sequence architecture for neural machine translation.\n\n"
        "1 Introduction\n"
        "Sequence modeling has traditionally relied on recurrent connections.\n\n"
        "2 Methodology\n"
        "We replace recurrence with multi-head self-attention mechanisms.\n\n"
        "3 Conclusion\n"
        "Self-attention achieves superior BLEU scores."
    )

    # 1. Clean text
    cleaned = clean_text_content(raw_text)
    assert "\n\n\n\n" not in cleaned
    assert "Transformer Networks" in cleaned

    # 2. Extract abstract
    abstract = extract_abstract(cleaned)
    assert abstract is not None
    assert "attention-based sequence architecture" in abstract

    # 3. Segment into sections
    sections = segment_into_sections(cleaned)
    assert len(sections) >= 3
    section_names = [s["section_name"].lower() for s in sections]
    assert any("abstract" in s for s in section_names)
    assert any("introduction" in s for s in section_names)
    assert any("methodology" in s for s in section_names)

    # 4. Keyword extraction via TF-IDF
    keywords = extract_keywords(cleaned, top_n=5)
    assert len(keywords) >= 2
    kw_words = [k["keyword"].lower() for k in keywords]
    assert any("attention" in kw or "sequence" in kw or "transformer" in kw for kw in kw_words)


# ============================================================================
# 8. Document Storage & Relational Database Persistence
# ============================================================================
def test_08_document_storage(api_client, db_session, sample_pdf_bytes):
    """
    Test 8: Verify that paper metadata, segmented sections, and extracted
    keywords are correctly stored across relational MySQL tables with valid foreign keys.
    """
    files = {
        "file": ("relational_test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")
    }
    form_data = {
        "title": "Relational Storage Verification Paper",
        "authors": "Database Tester, Storage Analyst",
    }

    upload_res = api_client.post("/documents/upload", files=files, data=form_data)
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["document_id"]

    # Query MySQL database directly
    paper = db_session.query(Paper).filter(Paper.id == doc_id).first()
    assert paper is not None, "Paper record was not persisted in MySQL 'papers' table"
    assert paper.title == "Relational Storage Verification Paper"
    assert paper.processing_status == "completed"

    # Verify sections in 'paper_sections'
    sections = db_session.query(PaperSection).filter(PaperSection.paper_id == doc_id).all()
    assert len(sections) > 0, "No section records found in 'paper_sections'"
    assert all(s.paper_id == doc_id for s in sections)

    # Verify keywords in 'paper_keywords'
    keywords = db_session.query(PaperKeyword).filter(PaperKeyword.paper_id == doc_id).all()
    assert len(keywords) > 0, "No keyword records found in 'paper_keywords'"
    assert all(k.paper_id == doc_id for k in keywords)


# ============================================================================
# 9. Search with Valid Query (TF-IDF & Cosine Similarity)
# ============================================================================
def test_09_search_valid_query(api_client, db_session):
    """
    Test 9: Verify search service and REST endpoint (GET /search/) with a matching query.
    Asserts positive cosine similarity score, proper ranking, and contextual snippet.
    """
    # 1. Direct Service Call
    service_result = search_papers_tfidf("transformer attention language", db_session)
    assert service_result["status"] == "success"
    assert service_result["total_results"] >= 1
    top_hit = service_result["results"][0]
    assert top_hit["score"] > 0.0
    assert "snippet" in top_hit
    assert len(top_hit["snippet"]) > 10

    # 2. REST API Call
    api_res = api_client.get("/search/?q=transformer attention")
    assert api_res.status_code == 200
    api_data = api_res.json()
    assert api_data["status"] == "success"
    assert api_data["total_results"] >= 1
    assert api_data["results"][0]["relevance_percentage"] is not None


# ============================================================================
# 10. Search with No Matching Results
# ============================================================================
def test_10_search_no_results(api_client, db_session):
    """
    Test 10: Verify search behavior when querying terms not present in corpus.
    Asserts graceful empty result handling without crashes or 500 errors.
    """
    obscure_query = "xenon astrophysics plasma thermodynamics nonexisting99"

    # 1. Direct Service Call
    service_result = search_papers_tfidf(obscure_query, db_session)
    assert service_result["status"] == "success"
    assert service_result["total_results"] == 0
    assert "no research papers" in service_result["message"].lower()

    # 2. REST API Call
    api_res = api_client.get(f"/search/?q={obscure_query}")
    assert api_res.status_code == 200
    api_data = api_res.json()
    assert api_data["total_results"] == 0
    assert len(api_data["results"]) == 0


# ============================================================================
# 11. Metadata Heuristic Extraction
# ============================================================================
def test_11_metadata_extraction():
    """
    Test 11: Verify heuristic extraction of Title, Authors, Abstract,
    Publication Year, and Explicit Author Keywords.
    """
    sample_text = (
        "Proceedings of the 2024 International Conference on Machine Learning\n"
        "Scalable Graph Neural Networks for Molecule Generation\n"
        "Alice Johnson, Bob Smith, Clara Davis\n"
        "Department of Chemistry & Computer Science, Stanford University\n"
        "Contact: {ajohnson, bsmith}@stanford.edu\n\n"
        "Abstract—Graph neural networks (GNNs) offer promising capabilities for molecular drug discovery. "
        "We present a scalable architecture achieving linear time complexity on molecular benchmarks.\n\n"
        "Keywords: Graph Neural Networks, Molecular Design, Deep Learning, Drug Discovery.\n\n"
        "1 Introduction\n"
        "Molecular representation learning is a key frontier in computational chemistry."
    )

    fake_extraction_data = {
        "full_text": sample_text,
        "pages": [{"page_number": 1, "text": sample_text, "has_text": True}],
        "metadata": {"title": "", "author": "", "creation_date": "D:20240315100000"},
        "file_name": "scalable_gnn_molecules.pdf",
    }

    meta = MetadataExtractor.extract_all_metadata(fake_extraction_data)

    # Check Title (Filtered conference header line)
    assert "Scalable Graph Neural Networks" in meta["title"]

    # Check Authors (Filtered affiliation line)
    assert "Alice Johnson" in meta["authors"]
    assert "Stanford" not in meta["authors"]

    # Check Abstract
    assert meta["abstract"] is not None
    assert "molecular drug discovery" in meta["abstract"].lower()

    # Check Publication Year
    assert meta["publication_year"] == 2024

    # Check Explicit Keywords
    assert any("graph" in kw.lower() for kw in meta["explicit_keywords"])


# ============================================================================
# 12. API Error Handling & Edge Cases
# ============================================================================
def test_12_api_error_handling(api_client):
    """
    Test 12: Verify proper HTTP error status codes and error responses:
      - 404 Not Found for non-existent document ID
      - 422 Unprocessable Entity for invalid or missing request parameters
      - 401 Unauthorized when accessing protected routes without valid JWT
    """
    # 1. Non-existent document ID -> 404 Not Found
    res_404 = api_client.get("/documents/999999")
    assert res_404.status_code == 404
    assert "not found" in res_404.json()["detail"].lower()

    # 2. Search query with empty string -> 400 Bad Request or handled gracefully
    res_empty_search = api_client.get("/search/?q=")
    assert res_empty_search.status_code == 400 or res_empty_search.status_code == 422

    # 3. Access protected route without authorization header -> 401 Unauthorized
    res_401 = api_client.get("/auth/me")
    assert res_401.status_code == 401

    # 4. Malformed JSON payload to /auth/register -> 422 Unprocessable Entity
    res_422 = api_client.post("/auth/register", json={"username": "incomplete_payload"})
    assert res_422.status_code == 422
