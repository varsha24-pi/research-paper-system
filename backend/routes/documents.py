import os
import shutil
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.database.models import User, Paper
from backend.utils.helpers import validate_pdf_file, generate_unique_filename

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
    user_id: Optional[int] = Form(None, description="Optional user ID (defaults to demo researcher)"),
    db: Session = Depends(get_db)
):
    """
    Upload a research paper in PDF format.
    
    Validates the file, stores it safely on disk with a unique filename,
    and records initial metadata in the MySQL database.
    """
    # 1. Validate PDF extension, MIME type, magic bytes, and file size
    file_size = await validate_pdf_file(file)

    # 2. Generate a secure, unique filename to prevent overwriting
    unique_name = generate_unique_filename(file.filename)
    destination_path = UPLOAD_DIR / unique_name

    # 3. Determine paper title (use provided title or fall back to original filename)
    clean_title = title.strip() if title and title.strip() else os.path.splitext(file.filename)[0].replace("_", " ").title()

    # 4. Determine user association (use provided user_id or demo user)
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found."
            )
        assigned_user_id = user.id
    else:
        demo_user = get_or_create_default_user(db)
        assigned_user_id = demo_user.id

    # 5. Save the file to disk
    try:
        with destination_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to write file to disk: {str(e)}"
        )

    # 6. Record metadata in the MySQL database
    try:
        new_paper = Paper(
            user_id=assigned_user_id,
            title=clean_title,
            file_name=file.filename,
            file_path=str(destination_path),
            file_size_bytes=file_size,
            total_pages=0,  # Will be populated during PDF extraction
            processing_status="uploaded"
        )
        db.add(new_paper)
        db.commit()
        db.refresh(new_paper)

        # ---------------------------------------------------------------------
        # Modular Hook: PDF Extraction and NLP Preprocessing can be triggered here
        # e.g., trigger_pdf_extraction(new_paper.id, destination_path)
        # ---------------------------------------------------------------------

        return {
            "status": "success",
            "message": "Research paper uploaded successfully.",
            "document_id": new_paper.id,
            "filename": new_paper.file_name,
            "saved_filename": unique_name,
            "title": new_paper.title,
            "file_size_bytes": new_paper.file_size_bytes,
            "upload_status": new_paper.processing_status,
            "uploaded_at": new_paper.uploaded_at.isoformat()
        }

    except Exception as db_error:
        db.rollback()
        # Clean up the saved file on disk if the database transaction fails
        if destination_path.exists():
            destination_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while saving document: {str(db_error)}"
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
                "uploaded_at": p.uploaded_at.isoformat()
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
    Retrieve details of a specific uploaded paper by its ID.
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
            "uploaded_at": paper.uploaded_at.isoformat()
        }
    }
