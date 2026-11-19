import uuid

from app.services.indexing import index_document
from app.services.retrieval import search_chunks
from app.services.vector_store import delete_document_chunks


def test_search_returns_the_page_that_answers_the_question():
    doc_id = uuid.uuid4().hex
    pages = [
        {"page_number": 1, "text": "The office cafeteria serves lunch from noon until two in the afternoon."},
        {"page_number": 2, "text": "Employees receive twenty days of paid annual leave every calendar year."},
    ]

    try:
        index_document(doc_id, "policy_test.pdf", pages)
        results = search_chunks(
            "how many days of annual leave do employees get",
            top_k=2,
            document_id=doc_id,
        )

        assert results, "expected at least one result"
        assert results[0]["page_number"] == 2
        assert results[0]["filename"] == "policy_test.pdf"
        assert 0.0 <= results[0]["score"] <= 1.0
        assert results[0]["score"] > results[-1]["score"]
    finally:
        delete_document_chunks(doc_id)


def test_search_for_unknown_document_returns_empty_list():
    assert search_chunks("any question at all", document_id="0" * 32) == []