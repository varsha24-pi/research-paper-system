import os
import shutil
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.database.models import User, Paper, PaperSection, PaperKeyword
from backend.utils.helpers import validate_pdf_file, generate_unique_filename
from backend.services.pdf_extractor import extract_text_from_pdf, PDFExtractionError
from backend.services.text_processor import process_extracted_document

router = APIRouter(prefix="/documents", tags=["Documents"])

# Directory where uploaded PDF documents are stored
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def get_or_create_default_user(db: Session) -> User:
    """
    Retrieves or creates a default demo user to satisfy the foreign key constraint
    during development before the authentication module is hooked up.
    """
    user = db.query(User).filter(User.username == "demo_researcher").first()
    if not user:
        user = User(
            username="demo_researcher",
            email="researcher@example.com",
            password_hash="demo_hashed_password",
            full_name="Demo Researcher"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(..., description="The PDF research paper to upload"),
    title: Optional[str] = Form(None, description="Optional custom paper title"),
    authors: Optional[str] = Form(None, description="Optional authors (comma-separated)"),
    user_id: Optional[int] = Form(None, description="Optional user ID (defaults to demo researcher)"),
    db: Session = Depends(get_db)
):
    """
    Complete End-to-End Pipeline:
    1. Upload & Validate PDF
    2. Save PDF to disk
    3. Extract text & metadata (PyMuPDF)
    4. Clean text, segment sections & extract keywords (NLP/TF-IDF)
    5. Save Paper, PaperSection, and PaperKeyword records to MySQL
    6. Return structured response with extracted intelligence
    """
    # -------------------------------------------------------------------------
    # Step 1: Validate PDF format (extension, MIME, magic bytes, size)
    # -------------------------------------------------------------------------
    file_size = await validate_pdf_file(file)

    # -------------------------------------------------------------------------
    # Step 2: Save PDF to Disk with Unique Filename
    # -------------------------------------------------------------------------
    unique_name = generate_unique_filename(file.filename)
    destination_path = UPLOAD_DIR / unique_name

    try:
        with destination_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to write file to disk: {str(e)}"
        )

    # -------------------------------------------------------------------------
    # Step 3: Extract Text & Embedded Metadata from PDF
    # -------------------------------------------------------------------------
    try:
        extraction_data = extract_text_from_pdf(destination_path)
    except PDFExtractionError as pe:
        # Clean up saved file on disk if extraction fails
        if destination_path.exists():
            destination_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"PDF extraction error: {str(pe)}"
        )

    # -------------------------------------------------------------------------
    # Step 4: Text Preprocessing, Sectioning & Keyword Extraction
    # -------------------------------------------------------------------------
    processed_data = process_extracted_document(extraction_data)

    # Resolve Title and Authors (prefer user inputs, then PDF metadata, then filename)
    pdf_meta = extraction_data.get("metadata", {})
    resolved_title = (
        title.strip() if title and title.strip()
        else pdf_meta.get("title") or os.path.splitext(file.filename)[0].replace("_", " ").title()
    )
    resolved_authors = (
        authors.strip() if authors and authors.strip()
        else pdf_meta.get("author") or None
    )

    # Determine user association
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found."
            )
        assigned_user_id = user.id
    else:
        assigned_user_id = get_or_create_default_user(db).id

    # -------------------------------------------------------------------------
    # Step 5: Store in MySQL (Paper, Sections, Keywords) in a Single Transaction
    # -------------------------------------------------------------------------
    try:
        # 5a. Create Paper entry
        new_paper = Paper(
            user_id=assigned_user_id,
            title=resolved_title,
            authors=resolved_authors,
            file_name=file.filename,
            file_path=str(destination_path),
            file_size_bytes=file_size,
            total_pages=extraction_data.get("total_pages", 0),
            abstract=processed_data.get("abstract"),
            processing_status="completed"
        )
        db.add(new_paper)
        db.flush()  # Flush to generate new_paper.id for foreign keys

        # 5b. Create PaperSection entries
        for sec in processed_data.get("sections", []):
            section_entry = PaperSection(
                paper_id=new_paper.id,
                section_name=sec["section_name"],
                section_order=sec["section_order"],
                page_number=sec.get("page_number"),
                content=sec["content"]
            )
            db.add(section_entry)

        # 5c. Create PaperKeyword entries
        for kw in processed_data.get("keywords", []):
            keyword_entry = PaperKeyword(
                paper_id=new_paper.id,
                keyword=kw["keyword"],
                relevance_score=kw["relevance_score"]
            )
            db.add(keyword_entry)

        db.commit()
        db.refresh(new_paper)

        # ---------------------------------------------------------------------
        # Step 6: Return Structured Response
        # ---------------------------------------------------------------------
        return {
            "status": "success",
            "message": "Research paper uploaded, extracted, preprocessed, and stored successfully.",
            "document_id": new_paper.id,
            "filename": new_paper.file_name,
            "saved_filename": unique_name,
            "title": new_paper.title,
            "authors": new_paper.authors,
            "total_pages": new_paper.total_pages,
            "total_words": extraction_data.get("total_words", 0),
            "abstract": new_paper.abstract[:200] + "..." if new_paper.abstract else None,
            "sections_count": len(processed_data.get("sections", [])),
            "sections": [s["section_name"] for s in processed_data.get("sections", [])],
            "keywords": [k["keyword"] for k in processed_data.get("keywords", [])],
            "upload_status": new_paper.processing_status,
            "uploaded_at": new_paper.uploaded_at.isoformat()
        }

    except Exception as db_err:
        db.rollback()
        # Clean up disk file on database failure
        if destination_path.exists():
            destination_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while saving document: {str(db_err)}"
        )


@router.get("/", status_code=status.HTTP_200_OK)
def list_documents(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    List all uploaded research papers with pagination.
    """
    papers = db.query(Paper).order_by(Paper.uploaded_at.desc()).offset(skip).limit(limit).all()
    total = db.query(Paper).count()

    return {
        "status": "success",
        "total_documents": total,
        "returned": len(papers),
        "documents": [
            {
                "id": p.id,
                "title": p.title,
                "authors": p.authors,
                "filename": p.file_name,
                "file_size_bytes": p.file_size_bytes,
                "total_pages": p.total_pages,
                "processing_status": p.processing_status,
                "uploaded_at": p.uploaded_at.isoformat(),
                "keywords": [k.keyword for k in p.keywords[:5]]
            }
            for p in papers
        ]
    }


@router.get("/{document_id}", status_code=status.HTTP_200_OK)
def get_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve full structured details of a specific paper (metadata, sections, keywords).
    """
    paper = db.query(Paper).filter(Paper.id == document_id).first()
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found."
        )

    return {
        "status": "success",
        "document": {
            "id": paper.id,
            "title": paper.title,
            "authors": paper.authors,
            "publication_year": paper.publication_year,
            "journal_conference": paper.journal_conference,
            "doi": paper.doi,
            "filename": paper.file_name,
            "file_size_bytes": paper.file_size_bytes,
            "total_pages": paper.total_pages,
            "abstract": paper.abstract,
            "processing_status": paper.processing_status,
            "uploaded_at": paper.uploaded_at.isoformat(),
            "keywords": [
                {"keyword": k.keyword, "relevance_score": k.relevance_score}
                for k in paper.keywords
            ],
            "sections": [
                {
                    "id": s.id,
                    "section_name": s.section_name,
                    "section_order": s.section_order,
                    "page_number": s.page_number,
                    "preview": s.content[:150] + "..." if len(s.content) > 150 else s.content
                }
                for s in sorted(paper.sections, key=lambda x: x.section_order)
            ]
        }
    }
