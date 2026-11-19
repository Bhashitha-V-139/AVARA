from app.services.chunking import chunk_pages
from app.services.embeddings import embed_texts
from app.services.vector_store import add_chunks


def index_document(document_id: str, filename: str, pages: list[dict]) -> int:
    """
    Chunk a document's pages, embed each chunk, and store everything in ChromaDB.
    Returns the number of chunks stored.
    """
    chunks = chunk_pages(pages)
    if not chunks:
        return 0

    embeddings = embed_texts([c.text for c in chunks])
    add_chunks(document_id, filename, chunks, embeddings)
    return len(chunks)