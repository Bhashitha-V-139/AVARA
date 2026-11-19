import uuid

from app.services.embeddings import embed_texts
from app.services.indexing import index_document
from app.services.vector_store import delete_document_chunks, get_collection


def test_embeddings_have_384_dimensions():
    vectors = embed_texts(["hello world", "second text"])
    assert len(vectors) == 2
    assert len(vectors[0]) == 384


def test_index_stores_chunks_and_delete_removes_them():
    doc_id = uuid.uuid4().hex
    pages = [
        {"page_number": 1, "text": "Employees receive 20 days of annual leave each year."},
        {"page_number": 2, "text": "Leave requests must be submitted through the HR portal."},
    ]

    try:
        count = index_document(doc_id, "test.pdf", pages)
        assert count == 2

        stored = get_collection().get(where={"document_id": doc_id})
        assert len(stored["ids"]) == 2
        assert sorted(m["page_number"] for m in stored["metadatas"]) == [1, 2]
    finally:
        delete_document_chunks(doc_id)

    remaining = get_collection().get(where={"document_id": doc_id})
    assert remaining["ids"] == []