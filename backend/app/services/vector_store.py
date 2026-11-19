import chromadb

from app.config import settings
from app.services.chunking import Chunk

COLLECTION_NAME = "avara_chunks"

_client: chromadb.ClientAPI | None = None


def get_collection():
    """Open (or create) the persistent ChromaDB collection that holds all chunks."""
    global _client
    if _client is None:
        settings.ensure_directories()
        _client = chromadb.PersistentClient(path=str(settings.chroma_dir))
    return _client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def add_chunks(
    document_id: str,
    filename: str,
    chunks: list[Chunk],
    embeddings: list[list[float]],
) -> None:
    """Store chunks, their vectors, and their metadata (including page number)."""
    if not chunks:
        return
    get_collection().add(
        ids=[f"{document_id}_{c.chunk_index}" for c in chunks],
        documents=[c.text for c in chunks],
        embeddings=embeddings,
        metadatas=[
            {
                "document_id": document_id,
                "filename": filename,
                "page_number": c.page_number,
                "chunk_index": c.chunk_index,
            }
            for c in chunks
        ],
    )


def delete_document_chunks(document_id: str) -> None:
    """Remove every chunk that belongs to one document. Safe if none exist."""
    get_collection().delete(where={"document_id": document_id})