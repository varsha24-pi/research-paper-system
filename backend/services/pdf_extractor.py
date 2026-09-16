import os
import re
from pathlib import Path
from typing import Dict, Any, List, Union

# Import PyMuPDF (using modern `import pymupdf`) or fallback to pypdf
try:
    import pymupdf
    PYMUPDF_AVAILABLE = True
except ImportError:
    try:
        import fitz as pymupdf
        PYMUPDF_AVAILABLE = True
    except ImportError:
        PYMUPDF_AVAILABLE = False

try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False


class PDFExtractionError(Exception):
    """Custom exception raised when PDF extraction encounters an unrecoverable error."""
    pass


def clean_page_text(raw_text: str) -> str:
    """
    Cleans raw extracted page text by:
    - Normalizing irregular whitespace and line breaks
    - Fixing broken hyphenated line wraps (e.g. 'intelli- \n gence' -> 'intelligence')
    - Removing non-printable control characters
    """
    if not raw_text:
        return ""

    # Replace null bytes and non-printable control characters (except newline, tab, carriage return)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", raw_text)

    # Fix broken hyphenated words at line endings: e.g. "distrib-\nuted" -> "distributed"
    text = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", text)

    # Normalize excessive blank lines to double newlines (paragraphs)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Normalize consecutive spaces/tabs to a single space
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


def extract_with_pymupdf(file_path: Path) -> Dict[str, Any]:
    """
    Extracts text and metadata using PyMuPDF - high speed, accurate page splitting.
    """
    doc = pymupdf.open(str(file_path))
    
    if doc.is_encrypted:
        if not doc.authenticate(""):
            raise PDFExtractionError(f"The PDF file '{file_path.name}' is password-protected/encrypted.")

    total_pages = len(doc)
    pages_data: List[Dict[str, Any]] = []
    combined_text_chunks: List[str] = []
    total_words = 0

    for page_idx in range(total_pages):
        page = doc[page_idx]
        page_number = page_idx + 1
        raw_text = page.get_text("text") or ""
        cleaned_text = clean_page_text(raw_text)

        words = len(cleaned_text.split()) if cleaned_text else 0
        has_text = words > 0
        total_words += words

        pages_data.append({
            "page_number": page_number,
            "text": cleaned_text,
            "word_count": words,
            "has_text": has_text
        })

        if has_text:
            combined_text_chunks.append(cleaned_text)

    # Extract embedded document metadata
    meta = doc.metadata or {}
    metadata = {
        "title": (meta.get("title") or "").strip(),
        "author": (meta.get("author") or "").strip(),
        "subject": (meta.get("subject") or "").strip(),
        "keywords": (meta.get("keywords") or "").strip(),
        "creator": (meta.get("creator") or "").strip(),
        "producer": (meta.get("producer") or "").strip(),
        "creation_date": meta.get("creationDate", "")
    }

    doc.close()

    full_combined_text = "\n\n".join(combined_text_chunks)

    return {
        "status": "success",
        "extractor_engine": "PyMuPDF",
        "file_name": file_path.name,
        "file_path": str(file_path),
        "total_pages": total_pages,
        "total_words": total_words,
        "pages": pages_data,
        "full_text": full_combined_text,
        "metadata": metadata,
        "has_extractable_text": total_words > 0
    }


def extract_with_pypdf(file_path: Path) -> Dict[str, Any]:
    """
    Fallback extraction using pypdf.
    """
    import pypdf

    with file_path.open("rb") as f:
        reader = pypdf.PdfReader(f)

        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception:
                raise PDFExtractionError(f"The PDF file '{file_path.name}' is password-protected/encrypted.")

        total_pages = len(reader.pages)
        pages_data: List[Dict[str, Any]] = []
        combined_text_chunks: List[str] = []
        total_words = 0

        for page_idx, page in enumerate(reader.pages):
            page_number = page_idx + 1
            try:
                raw_text = page.extract_text() or ""
            except Exception:
                raw_text = ""

            cleaned_text = clean_page_text(raw_text)
            words = len(cleaned_text.split()) if cleaned_text else 0
            has_text = words > 0
            total_words += words

            pages_data.append({
                "page_number": page_number,
                "text": cleaned_text,
                "word_count": words,
                "has_text": has_text
            })

            if has_text:
                combined_text_chunks.append(cleaned_text)

        meta = reader.metadata or {}
        metadata = {
            "title": str(meta.get("/Title") or "").strip(),
            "author": str(meta.get("/Author") or "").strip(),
            "subject": str(meta.get("/Subject") or "").strip(),
            "keywords": str(meta.get("/Keywords") or "").strip(),
            "creator": str(meta.get("/Creator") or "").strip(),
            "producer": str(meta.get("/Producer") or "").strip(),
            "creation_date": str(meta.get("/CreationDate") or "")
        }

        full_combined_text = "\n\n".join(combined_text_chunks)

        return {
            "status": "success",
            "extractor_engine": "pypdf",
            "file_name": file_path.name,
            "file_path": str(file_path),
            "total_pages": total_pages,
            "total_words": total_words,
            "pages": pages_data,
            "full_text": full_combined_text,
            "metadata": metadata,
            "has_extractable_text": total_words > 0
        }


def extract_text_from_pdf(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Main entry point for extracting text and metadata from a PDF file.

    Parameters:
        file_path (Union[str, Path]): Path to the PDF file on disk.

    Returns:
        Dict[str, Any]: Dictionary containing total_pages, pages breakdown,
                        full_text, metadata, and word count statistics.

    Raises:
        PDFExtractionError: If the file does not exist, is not a PDF, or extraction fails.
    """
    path_obj = Path(file_path)

    # 1. Verify file exists
    if not path_obj.exists():
        raise PDFExtractionError(f"PDF file not found at path: '{path_obj.resolve()}'")

    if not path_obj.is_file():
        raise PDFExtractionError(f"Specified path is not a file: '{path_obj.resolve()}'")

    if path_obj.suffix.lower() != ".pdf":
        raise PDFExtractionError(f"File '{path_obj.name}' is not a PDF (found extension: '{path_obj.suffix}').")

    # 2. Extract using PyMuPDF if available, else pypdf
    try:
        if PYMUPDF_AVAILABLE:
            return extract_with_pymupdf(path_obj)
        elif PYPDF_AVAILABLE:
            return extract_with_pypdf(path_obj)
        else:
            try:
                import pymupdf
                return extract_with_pymupdf(path_obj)
            except ImportError:
                try:
                    import pypdf
                    return extract_with_pypdf(path_obj)
                except ImportError:
                    raise PDFExtractionError(
                        "No PDF extraction library available. Please install PyMuPDF: `pip install pymupdf`"
                    )

    except PDFExtractionError:
        raise
    except Exception as general_err:
        raise PDFExtractionError(f"Failed to extract text from '{path_obj.name}': {str(general_err)}")
