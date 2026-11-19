import pytest

from app.config import settings
from app.services.llm import generate_text

needs_key = pytest.mark.skipif(
    not settings.gemini_api_key,
    reason="GEMINI_API_KEY is not set in .env",
)


@needs_key
def test_gemini_responds():
    answer = generate_text("Reply with only the word OK.")
    assert "OK" in answer.upper()