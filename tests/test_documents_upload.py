import sys
import os
import io
from pathlib import Path

# Add project root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pymupdf
from fastapi.testclient import TestClient
from backend.main import app
from backend.database.connection import engine, Base, SessionLocal
from backend.database.models import Paper, PaperSection, PaperKeyword

# Ensure database tables exist before testing
Base.metadata.create_all(bind=engine)

client = TestClient(app)


def generate_test_pdf_bytes():
    """Generates a valid research paper PDF in memory."""
    doc = pymupdf.open()

    page1 = doc.new_page()
    text_page1 = (
        "Transformer Networks for Natural Language Processing\n\n"
        "Vaswani et al.\n\n"
        "Abstract\n"
        "We introduce an attention-based sequence architecture for neural machine translation "
        "and language understanding. Self-attention layers replace recurrent and convolutional connections.\n\n"
        "1 Introduction\n"
        "Recurrent neural networks have dominated sequence transduction problems for years.\n\n"
        "2 Methodology\n"
        "The model uses multi-head self-attention and positional encodings to capture relationships."
    )
    rect1 = pymupdf.Rect(50, 50, 550, 700)
    page1.insert_textbox(rect1, text_page1, fontsize=11)

    page2 = doc.new_page()
    text_page2 = (
        "3 Results\n\n"
        "On English-to-German translation, the Transformer achieved a state-of-the-art BLEU score of 28.4.\n\n"
        "4 Conclusion\n"
        "Attention mechanisms provide faster training times and superior accuracy."
    )
    rect2 = pymupdf.Rect(50, 50, 550, 700)
    page2.insert_textbox(rect2, text_page2, fontsize=11)

    doc.set_metadata({
        "title": "Transformer Networks for NLP",
        "author": "Vaswani et al."
    })

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_end_to_end_ingestion():
    print("=" * 65)
    print(" Running End-to-End PDF Ingestion Pipeline Test")
    print("=" * 65)

    pdf_bytes = generate_test_pdf_bytes()
    files = {
        "file": ("transformer_nlp.pdf", io.BytesIO(pdf_bytes), "application/pdf")
    }
    data = {
        "title": "Transformer Networks for NLP",
        "authors": "Vaswani et al."
    }

    # 1. Test POST /documents/upload
    response = client.post("/documents/upload", files=files, data=data)
    assert response.status_code == 201, f"Failed: {response.text}"
    
    result = response.json()
    doc_id = result["document_id"]
    print(f"[PASS] Document uploaded and processed. ID: {doc_id}")
    print(f"       Title: '{result['title']}'")
    print(f"       Total Pages: {result['total_pages']}, Total Words: {result['total_words']}")
    print(f"       Sections extracted: {result['sections_count']} ({', '.join(result['sections'])})")
    print(f"       Keywords extracted: {', '.join(result['keywords'][:5])}")
    print(f"       Status: {result['upload_status']}")

    assert result["total_pages"] == 2
    assert result["sections_count"] >= 2
    assert len(result["keywords"]) >= 3
    assert result["upload_status"] == "completed"

    # 2. Verify direct MySQL entries
    db = SessionLocal()
    try:
        paper = db.query(Paper).filter(Paper.id == doc_id).first()
        assert paper is not None
        assert paper.processing_status == "completed"

        sections = db.query(PaperSection).filter(PaperSection.paper_id == doc_id).all()
        assert len(sections) == result["sections_count"]

        keywords = db.query(PaperKeyword).filter(PaperKeyword.paper_id == doc_id).all()
        assert len(keywords) == len(result["keywords"])

        print(f"[PASS] Verified MySQL records: 1 Paper, {len(sections)} Sections, {len(keywords)} Keywords in DB.")

    finally:
        db.close()

    # 3. Test GET /documents/{id} endpoint
    details_res = client.get(f"/documents/{doc_id}")
    assert details_res.status_code == 200
    doc_details = details_res.json()["document"]
    assert len(doc_details["sections"]) == len(sections)
    assert len(doc_details["keywords"]) == len(keywords)
    print(f"[PASS] GET /documents/{doc_id} returned complete structured hierarchy.")

    print("=" * 65)
    print("[OK] End-to-End Ingestion Pipeline Test Passed Successfully!")
    print("=" * 65)


if __name__ == "__main__":
    test_end_to_end_ingestion()
