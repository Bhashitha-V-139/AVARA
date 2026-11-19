from app.services.embeddings import embed_texts
from app.services.vector_store import get_collection

DEFAULT_TOP_K = 5
MAX_TOP_K = 10


def search_chunks(
    question: str,
    top_k: int = DEFAULT_TOP_K,
    document_id: str | None = None,
) -> list[dict]:
    """
    Find the stored chunks whose meaning is closest to the question.

    Each result contains the chunk text, its source document and page, and a
    score from 0 to 1, where higher means more related to the question.
    If document_id is given, only that document is searched.
    """
    top_k = max(1, min(top_k, MAX_TOP_K))
    collection = get_collection()

    where = {"document_id": document_id} if document_id else None
    available = len(collection.get(where=where)["ids"])
    if available == 0:
        return []

    query_vector = embed_texts([question])[0]
    result = collection.query(
        query_embeddings=[query_vector],
        n_results=min(top_k, available),
        where=where,
    )

    hits = []
    for text, meta, distance in zip(
        result["documents"][0],
        result["metadatas"][0],
        result["distances"][0],
    ):
        hits.append(
            {
                "text": text,
                "document_id": meta["document_id"],
                "filename": meta["filename"],
                "page_number": meta["page_number"],
                "chunk_index": meta["chunk_index"],
                # ChromaDB returns cosine distance; similarity = 1 - distance.
                "score": round(1.0 - distance, 4),
            }
        )
    return hits