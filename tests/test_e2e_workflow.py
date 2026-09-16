"""
==============================================================================
AI-Powered Research Paper Intelligence System - Complete End-to-End Workflow Test
==============================================================================
Simulates the complete user-to-database-to-search flow:
1. User registration & authentication -> Receives JWT
2. PDF Creation in memory (PyMuPDF) -> Upload via POST /documents/upload with JWT
3. Ingestion pipeline: Text extraction -> Preprocessing -> Metadata Extraction -> MySQL
4. Document inspection via GET /documents/{id}
5. Intelligent Search retrieval via GET /search/?q=... -> TF-IDF & Cosine Similarity ranking
6. Snippet verification & keyword matching
7. Database persistence & Foreign Key integrity verification
8. Query audit logging in search_logs table
==============================================================================
"""

import sys
import os
import io
import uuid
import pymupdf
from fastapi.testclient import TestClient

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from backend.main import app
from backend.database.connection import SessionLocal, engine, Base
from backend.database.models import User, Paper, PaperSection, PaperKeyword, SearchLog

client = TestClient(app)


def generate_quantum_ml_pdf():
    """Generates an academic research PDF in memory with clear sections."""
    doc = pymupdf.open()

    page1 = doc.new_page()
    p1_text = (
        "Quantum Neural Networks for High-Energy Physics Anomaly Detection\n"
        "Dr. Elena Rostova, Prof. Marcus Vance\n"
        "Department of Applied Physics, CERN & MIT\n"
        "Email: {erostova, mvance}@cern.ch\n\n"
        "Abstract\n"
        "We introduce a parameterized quantum neural network (QNN) framework optimized for detecting "
        "rare subatomic anomalies in particle collisions. By embedding quantum variational circuits "
        "into deep learning architectures, we achieve a 40% speedup in convergence.\n\n"
        "Keywords: Quantum Computing, Neural Networks, High-Energy Physics, Anomaly Detection.\n\n"
        "1 Introduction\n"
        "Modern high-energy particle colliders generate petabytes of sensory data per second."
    )
    page1.insert_textbox(pymupdf.Rect(50, 50, 550, 750), p1_text, fontsize=11)

    page2 = doc.new_page()
    p2_text = (
        "2 Methodology\n"
        "Our variational quantum classifier maps classical feature vectors into a Hilbert space using "
        "entangling quantum gates and parametrized Pauli rotation layers.\n\n"
        "3 Results\n"
        "On synthetic LHC collision datasets, the proposed QNN architecture achieved an AUC-ROC of 0.962.\n\n"
        "4 Conclusion\n"
        "Quantum variational circuits demonstrate immense promise for anomaly detection in experimental physics."
    )
    page2.insert_textbox(pymupdf.Rect(50, 50, 550, 750), p2_text, fontsize=11)

    doc.set_metadata({
        "title": "Quantum Neural Networks for Anomaly Detection",
        "author": "Dr. Elena Rostova et al.",
        "subject": "Quantum Machine Learning"
    })

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def run_e2e_workflow():
    print("=" * 75)
    print("   END-TO-END SYSTEM INTEGRATION WORKFLOW TEST")
    print("=" * 75)

    # -------------------------------------------------------------------------
    # Step 1: User Registration
    # -------------------------------------------------------------------------
    unique_suffix = uuid.uuid4().hex[:6]
    username = f"researcher_{unique_suffix}"
    email = f"researcher_{unique_suffix}@cern.ch"
    password = "QuantumPassword#2026"
    full_name = "Dr. Elena Rostova"

    print(f"\n[Step 1] Registering Researcher Account ({username})...")
    reg_res = client.post("/auth/register", json={
        "username": username,
        "email": email,
        "password": password,
        "full_name": full_name
    })
    assert reg_res.status_code == 201, f"Registration failed: {reg_res.text}"
    user_data = reg_res.json()
    user_id = user_data["id"]
    print(f"  [+] User registered with ID: #{user_id}")

    # -------------------------------------------------------------------------
    # Step 2: User Login & JWT Access Token
    # -------------------------------------------------------------------------
    print("\n[Step 2] Authenticating & Generating JWT Bearer Token...")
    login_res = client.post("/auth/login", json={
        "username": username,
        "password": password
    })
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token_data = login_res.json()
    access_token = token_data["access_token"]
    auth_headers = {"Authorization": f"Bearer {access_token}"}
    print(f"  [+] JWT Token generated: {access_token[:25]}... (Valid for 24h)")

    # -------------------------------------------------------------------------
    # Step 3: PDF Generation & Multipart Ingestion via API
    # -------------------------------------------------------------------------
    print("\n[Step 3] Ingesting PDF Paper via POST /documents/upload...")
    pdf_bytes = generate_quantum_ml_pdf()
    files = {
        "file": ("quantum_anomaly_detection.pdf", io.BytesIO(pdf_bytes), "application/pdf")
    }
    form_data = {
        "title": "Quantum Neural Networks for High-Energy Physics Anomaly Detection",
        "authors": "Dr. Elena Rostova, Prof. Marcus Vance"
    }

    upload_res = client.post("/documents/upload", files=files, data=form_data, headers=auth_headers)
    assert upload_res.status_code == 201, f"Upload failed: {upload_res.text}"
    upload_data = upload_res.json()
    doc_id = upload_data["document_id"]
    print(f"  [+] Document Ingested: ID #{doc_id}")
    print(f"  [+] Extracted Title : '{upload_data['title']}'")
    print(f"  [+] Extracted Authors: '{upload_data['authors']}'")
    print(f"  [+] Pages: {upload_data['total_pages']} | Words: {upload_data['total_words']}")
    print(f"  [+] Sections Parsed ({upload_data['sections_count']}): {', '.join(upload_data['sections'])}")
    print(f"  [+] Keywords ({len(upload_data['keywords'])}): {', '.join(upload_data['keywords'][:5])}")

    # -------------------------------------------------------------------------
    # Step 4: Verify Relational Persistence in MySQL
    # -------------------------------------------------------------------------
    print("\n[Step 4] Verifying MySQL Relational Tables Integrity...")
    db = SessionLocal()
    try:
        db_paper = db.query(Paper).filter(Paper.id == doc_id).first()
        assert db_paper is not None, "Paper record not found in database!"
        assert db_paper.user_id == user_id, "Paper user_id does not match authenticated user!"
        print(f"  [+] MySQL 'papers' record verified: ID={db_paper.id}, UserID={db_paper.user_id}")

        db_sections = db.query(PaperSection).filter(PaperSection.paper_id == doc_id).all()
        assert len(db_sections) >= 3, "Insufficient sections saved in paper_sections table"
        print(f"  [+] MySQL 'paper_sections' records verified: {len(db_sections)} sections stored.")

        db_keywords = db.query(PaperKeyword).filter(PaperKeyword.paper_id == doc_id).all()
        assert len(db_keywords) >= 3, "Insufficient keywords saved in paper_keywords table"
        print(f"  [+] MySQL 'paper_keywords' records verified: {len(db_keywords)} keywords stored.")
    finally:
        db.close()

    # -------------------------------------------------------------------------
    # Step 5: Document Detail Fetch via GET /documents/{id}
    # -------------------------------------------------------------------------
    print(f"\n[Step 5] Fetching Structured Document via GET /documents/{doc_id}...")
    doc_res = client.get(f"/documents/{doc_id}")
    assert doc_res.status_code == 200
    doc_payload = doc_res.json()["document"]
    assert doc_payload["title"] == upload_data["title"]
    assert len(doc_payload["sections"]) == len(db_sections)
    print(f"  [+] Document hierarchy payload verified for frontend viewer.")

    # -------------------------------------------------------------------------
    # Step 6: TF-IDF Search Engine Execution
    # -------------------------------------------------------------------------
    query = "quantum variational anomaly"
    print(f"\n[Step 6] Executing Intelligent Search for Query: '{query}'...")
    search_res = client.get(f"/search/?q={query}&user_id={user_id}")
    assert search_res.status_code == 200, f"Search failed: {search_res.text}"
    search_data = search_res.json()
    assert search_data["total_results"] >= 1, "Expected at least 1 search hit"

    top_result = search_data["results"][0]
    print(f"  [+] Top Match: '{top_result['title']}'")
    print(f"  [+] Cosine Similarity Score: {top_result['score']} ({top_result.get('relevance_percentage', 'N/A')})")
    print(f"  [+] Highlighted Snippet: \"{top_result['snippet']}\"")
    print(f"  [+] Matched Keywords: {top_result['matched_keywords']}")
    assert "quantum" in top_result["title"].lower() or "quantum" in top_result["snippet"].lower()

    # -------------------------------------------------------------------------
    # Step 7: Verify Search Log History in MySQL
    # -------------------------------------------------------------------------
    print("\n[Step 7] Verifying Search Analytics & Query Logging...")
    db = SessionLocal()
    try:
        log = db.query(SearchLog).filter(SearchLog.query_text == query).order_by(SearchLog.searched_at.desc()).first()
        assert log is not None, "Search query was not logged in search_logs table"
        assert log.results_count >= 1
        print(f"  [+] SearchLog verified: Query='{log.query_text}', Results={log.results_count}, LoggedAt={log.searched_at}")
    finally:
        db.close()

    print("\n" + "=" * 75)
    print("   [ALL CHECKS PASSED] END-TO-END WORKFLOW INTEGRATION VERIFIED")
    print("=" * 75)


if __name__ == "__main__":
    run_e2e_workflow()
