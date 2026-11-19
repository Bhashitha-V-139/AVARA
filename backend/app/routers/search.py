from fastapi import APIRouter, HTTPException, Query

from app.schemas import SearchResponse, SearchResult
from app.services.retrieval import DEFAULT_TOP_K, MAX_TOP_K, search_chunks

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=SearchResponse)
def search(
    q: str = Query(..., min_length=3, max_length=1000, description="Your question"),
    top_k: int = Query(DEFAULT_TOP_K, ge=1, le=MAX_TOP_K),
    document_id: str | None = Query(None, pattern=r"^[0-9a-f]{32}$"),
) -> SearchResponse:
    """Return the stored document chunks most relevant to a question."""
    question = q.strip()
    if not question:
        raise HTTPException(status_code=400, detail="The question cannot be blank.")

    hits = search_chunks(question, top_k=top_k, document_id=document_id)

    return SearchResponse(
        question=question,
        results=[SearchResult(**hit) for hit in hits],
    )