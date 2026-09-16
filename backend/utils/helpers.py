import os
import re
import uuid
from datetime import datetime
from fastapi import UploadFile, HTTPException, status

ALLOWED_EXTENSIONS = {".pdf"}
ALLOWED_MIME_TYPES = {"application/pdf", "application/x-pdf", "application/acrobat", "applications/vnd.pdf", "text/pdf"}
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB limit for research papers


def sanitize_filename(filename: str) -> str:
    """
    Strips dangerous characters and path traversal sequences from a filename.
    """
    clean_name = os.path.basename(filename)
    # Replace spaces and special characters with underscores, keeping alphanumeric, dots, and hyphens
    clean_name = re.sub(r"[^\w\.-]", "_", clean_name)
    return clean_name or "document.pdf"


def generate_unique_filename(original_filename: str) -> str:
    """
    Generates a secure, unique filename using timestamp and UUID to prevent collisions.
    Example: 20260916_143000_a1b2c3d4_my_paper.pdf
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    short_uuid = uuid.uuid4().hex[:8]
    clean_original = sanitize_filename(original_filename)
    return f"{timestamp}_{short_uuid}_{clean_original}"


async def validate_pdf_file(file: UploadFile) -> int:
    """
    Validates that the uploaded file is a valid PDF:
    1. Checks file extension (.pdf)
    2. Checks MIME content-type
    3. Verifies PDF magic bytes (%PDF)
    4. Checks file size does not exceed MAX_FILE_SIZE_BYTES

    Returns:
        int: File size in bytes.
    Raises:
        HTTPException: If any validation rule fails.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided in upload."
        )

    # 1. Validate extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file extension '{ext}'. Only PDF files (.pdf) are supported."
        )

    # 2. Validate MIME type
    if file.content_type and file.content_type.lower() not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid MIME type '{file.content_type}'. Expected 'application/pdf'."
        )

    # 3. Read header to verify PDF magic bytes (%PDF)
    header = await file.read(5)
    await file.seek(0)  # Reset pointer to start for subsequent writing

    if not header.startswith(b"%PDF"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Corrupt or invalid PDF file format (missing PDF magic header)."
        )

    # 4. Check file size
    content = await file.read()
    file_size = len(content)
    await file.seek(0)  # Reset pointer to start

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded PDF file is empty (0 bytes)."
        )

    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum limit of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB."
        )

    return file_size
