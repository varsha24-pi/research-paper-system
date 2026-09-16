import sys
import os
from pathlib import Path

# Add project root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pymupdf
from backend.services.pdf_extractor import extract_text_from_pdf, PDFExtractionError


def generate_sample_research_pdf(file_path: Path) -> Path:
    """Creates a sample 3-page research paper PDF for automated testing."""
    doc = pymupdf.open()

    # Page 1: Title, Abstract, and Introduction
    page1 = doc.new_page()
    text_page1 = (
        "Attention Is All You Need\n\n"
        "Ashish Vaswani, Noam Shazeer, Niki Parmar\n"
        "Google Brain, Google Research\n\n"
        "Abstract\n"
        "The dominant sequence transduction models are based on complex recurrent or "
        "convolutional neural networks. We propose the Transformer, a model architecture "
        "eschewing recurrence and instead relying entirely on an attention mechanism to draw "
        "global dependencies between input and output.\n\n"
        "1 Introduction\n"
        "Recurrent neural networks, especially LSTM and GRU, have been established as state of the art."
    )
    rect1 = pymupdf.Rect(50, 50, 550, 700)
    page1.insert_textbox(rect1, text_page1, fontsize=11)

    # Page 2: Model Architecture
    page2 = doc.new_page()
    text_page2 = (
        "2 Model Architecture\n\n"
        "Most competitive neural sequence transduction models have an encoder-decoder structure. "
        "Here, the encoder maps an input sequence of symbol representations to a sequence of continuous "
        "representations. The Transformer follows this overall architecture using stacked self-attention and "
        "point-wise, fully connected layers."
    )
    rect2 = pymupdf.Rect(50, 50, 550, 700)
    page2.insert_textbox(rect2, text_page2, fontsize=11)

    # Page 3: Blank page (e.g. diagrams or notes) to test empty page handling
    page3 = doc.new_page()  # Intentionally no text inserted

    # Set metadata
    doc.set_metadata({
        "title": "Attention Is All You Need",
        "author": "Ashish Vaswani et al.",
        "subject": "Deep Learning / Natural Language Processing"
    })

    file_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(file_path))
    doc.close()
    return file_path


def run_tests():
    print("=" * 60)
    print(" Running PDF Extractor Service Tests")
    print("=" * 60)

    test_pdf_path = Path("tests/sample_transformer_paper.pdf")
    generate_sample_research_pdf(test_pdf_path)

    try:
        # Test 1: Extract from valid multi-page PDF
        result = extract_text_from_pdf(test_pdf_path)
        assert result["status"] == "success"
        assert result["total_pages"] == 3
        assert len(result["pages"]) == 3
        assert result["pages"][0]["has_text"] is True
        assert result["pages"][1]["has_text"] is True
        assert result["pages"][2]["has_text"] is False  # Blank page correctly detected!
        assert "Transformer" in result["full_text"], "Expected 'Transformer' in extracted text"
        assert "Attention Is All You Need" in result["full_text"], "Expected title in text"
        assert result["metadata"]["title"] == "Attention Is All You Need"
        print(f"[PASS] Successfully extracted text from 3-page PDF (Engine: {result['extractor_engine']})")
        print(f"       Total words extracted: {result['total_words']}")
        print(f"       Page 1 words: {result['pages'][0]['word_count']}")
        print(f"       Page 2 words: {result['pages'][1]['word_count']}")
        print(f"       Page 3 (blank) has_text: {result['pages'][2]['has_text']}")

        # Test 2: Error handling for non-existent file
        try:
            extract_text_from_pdf("non_existent_file.pdf")
            assert False, "Should have raised PDFExtractionError for missing file"
        except PDFExtractionError as e:
            print(f"[PASS] Missing file error correctly caught: {e}")

        # Test 3: Error handling for non-PDF file
        try:
            extract_text_from_pdf("requirements.txt")
            assert False, "Should have raised PDFExtractionError for non-PDF"
        except PDFExtractionError as e:
            print(f"[PASS] Invalid extension error correctly caught: {e}")

        print("=" * 60)
        print("[OK] All PDF Extractor tests passed successfully!")
        print("=" * 60)

    finally:
        # Clean up temporary test PDF
        if test_pdf_path.exists():
            test_pdf_path.unlink()


if __name__ == "__main__":
    run_tests()
