import sys
import os
import io
import pytest
from pathlib import Path

# Add project root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pymupdf
from fastapi.testclient import TestClient
from backend.main import app
from backend.database.connection import engine, Base, SessionLocal


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Ensures database tables exist before any tests run."""
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(scope="function")
def db_session():
    """Provides a transactional database session per test function."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def api_client():
    """FastAPI TestClient fixture for executing API requests."""
    return TestClient(app)


@pytest.fixture(scope="module")
def sample_pdf_bytes():
    """Creates a structured sample research paper in memory (PyMuPDF)."""
    doc = pymupdf.open()

    page1 = doc.new_page()
    text_page1 = (
        "Transformer Architectures for Deep Language Intelligence\n\n"
        "Ashish Vaswani, Noam Shazeer, Niki Parmar\n"
        "Department of Computer Science, Google Research\n"
        "Email: {vaswani, shazeer}@google.com\n\n"
        "Abstract\n"
        "We introduce the Transformer, a novel sequence model architecture relying entirely "
        "on multi-head self-attention mechanisms to eliminate recurrent connections.\n\n"
        "Index Terms—Deep learning, Transformer, Self-Attention, Natural Language Processing.\n\n"
        "1 Introduction\n"
        "Recurrent neural networks have been the foundation of sequence transduction models."
    )
    page1.insert_textbox(pymupdf.Rect(50, 50, 550, 700), text_page1, fontsize=11)

    page2 = doc.new_page()
    text_page2 = (
        "2 Methodology\n"
        "The model architecture uses stacked self-attention and point-wise fully connected layers.\n\n"
        "3 Results\n"
        "On the WMT 2014 English-to-German task, the model establishes a new state-of-the-art BLEU score of 28.4.\n\n"
        "4 Conclusion\n"
        "Self-attention provides significantly faster training times and superior contextual representations."
    )
    page2.insert_textbox(pymupdf.Rect(50, 50, 550, 700), text_page2, fontsize=11)

    doc.set_metadata({
        "title": "Transformer Architectures for Deep Language Intelligence",
        "author": "Ashish Vaswani et al.",
        "creationDate": "D:20230510120000"
    })

    pdf_data = doc.tobytes()
    doc.close()
    return pdf_data
