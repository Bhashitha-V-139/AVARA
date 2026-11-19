import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.config import settings

PDF_MAGIC_BYTES = b"%PDF-"
CHUNK_SIZE = 1024 * 1024  # read uploads in 1 MB pieces


def validate_pdf_upload(file: UploadFile) -> None:
    """Reject anything that isn't a PDF by name or content type."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files are accepted.")

    if file.content_type not in ("application/pdf", "application/x-pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Invalid content type. Expected a PDF file.")


def save_pdf_upload(file: UploadFile) -> tuple[str, Path, int, datetime]:
    """
    Stream the upload to disk with a size limit and a PDF signature check.

    Returns (document_id, saved_path, size_bytes, uploaded_at).
    """
    settings.ensure_directories()

    max_bytes = settings.max_upload_mb * 1024 * 1024
    document_id = uuid.uuid4().hex
    target_path = settings.upload_dir / f"{document_id}.pdf"

    size = 0
    first_chunk = True

    try:
        with open(target_path, "wb") as out:
            while True:
                chunk = file.file.read(CHUNK_SIZE)
                if not chunk:
                    break

                if first_chunk:
                    if not chunk.startswith(PDF_MAGIC_BYTES):
                        raise HTTPException(
                            status_code=400,
                            detail="File content is not a valid PDF.",
                        )
                    first_chunk = False

                size += len(chunk)
                if size > max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File is too large. Maximum size is {settings.max_upload_mb} MB.",
                    )

                out.write(chunk)

        if size == 0:
            raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    except HTTPException:
        # Remove the partial file so rejected uploads don't pile up on disk.
        target_path.unlink(missing_ok=True)
        raise

    return document_id, target_path, size, datetime.now(timezone.utc)