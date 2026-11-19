from functools import lru_cache

from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"  # small, fast model that produces 384-number vectors


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """Load the model once and reuse it. The first call downloads it."""
    return SentenceTransformer(MODEL_NAME)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Convert a list of texts into a list of embedding vectors."""
    if not texts:
        return []
    model = get_embedding_model()
    vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return vectors.tolist()