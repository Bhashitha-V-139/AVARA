import pymupdf
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services.vector_store import get_collection


def make_pdf_bytes() -> bytes:
    """Create a one-page PDF in memory with known text."""
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Delete test: employees get 20 days of annual leave.")
    data = doc.tobytes()
    doc.close()
    return data


def test_upload_then_delete_removes_file_record_and_vectors():
    with TestClient(app) as client:
        upload = client.post(
            "/documents/upload",
            files={"file": ("delete_test.pdf", make_pdf_bytes(), "application/pdf")},
        )
        assert upload.status_code == 201
        doc_id = upload.json()["document"]["document_id"]

        pdf_path = settings.upload_dir / f"{doc_id}.pdf"
        assert pdf_path.exists()
        assert len(get_collection().get(where={"document_id": doc_id})["ids"]) > 0

        delete = client.delete(f"/documents/{doc_id}")
        assert delete.status_code == 200

        assert not pdf_path.exists()
        assert get_collection().get(where={"document_id": doc_id})["ids"] == []
        assert client.get(f"/documents/{doc_id}/pages").status_code == 404


def test_delete_unknown_document_returns_404():
    with TestClient(app) as client:
        response = client.delete("/documents/" + "0" * 32)
        assert response.status_code == 404


def test_delete_invalid_id_returns_400():
    with TestClient(app) as client:
        response = client.delete("/documents/not-a-valid-id")
        assert response.status_code == 400