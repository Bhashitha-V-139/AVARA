from app.config import settings
from app.database import delete_document_record, get_document
from app.services.vector_store import delete_document_chunks


def delete_document(document_id: str) -> bool:
    """
    Remove a document everywhere it lives: ChromaDB vectors, the PDF file, and the database row.
    Returns False if no such document exists in the database.
    """
    if get_document(document_id) is None:
        return False

    # 1. Vectors first. If this fails, the record and file remain, so a retry is safe.
    delete_document_chunks(document_id)

    # 2. The PDF file. A missing file is fine, since it may have been deleted by hand.
    (settings.upload_dir / f"{document_id}.pdf").unlink(missing_ok=True)

    # 3. The database row last.
    delete_document_record(document_id)
    return True