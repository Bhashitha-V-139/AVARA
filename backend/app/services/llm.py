import time
from functools import lru_cache

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from app.config import settings

MAX_ATTEMPTS = 3          # total tries for a temporary error
RETRY_DELAYS = (2, 5)     # seconds to wait before the 2nd and 3rd tries


class LLMError(Exception):
    """Raised when the language model cannot produce an answer."""


@lru_cache(maxsize=1)
def get_client() -> genai.Client:
    """Create the Gemini client once, using the key from .env."""
    if not settings.gemini_api_key:
        raise LLMError("GEMINI_API_KEY is not set. Add it to the .env file.")
    return genai.Client(api_key=settings.gemini_api_key)


def call_with_retry(make_call):
    """
    Run make_call() and retry temporary errors (503 and 429) with a short wait.
    Permanent errors, such as a retired model or a bad key, fail immediately.
    make_call is a function with no arguments that returns the Gemini response.
    """
    last_error: Exception | None = None

    for attempt in range(MAX_ATTEMPTS):
        try:
            return make_call()
        except genai_errors.ServerError as exc:
            # 5xx: the service is busy or failing. Worth retrying.
            last_error = exc
        except genai_errors.ClientError as exc:
            # 429 means rate limited, which is also worth retrying.
            if exc.code == 429:
                last_error = exc
            else:
                # 4xx such as 404 or 403 won't fix themselves, so fail now.
                raise LLMError(f"Gemini request failed: {exc}") from exc
        except Exception as exc:
            raise LLMError(f"Gemini request failed: {exc}") from exc

        if attempt < MAX_ATTEMPTS - 1:
            time.sleep(RETRY_DELAYS[attempt])

    raise LLMError(
        "Gemini is busy right now. Please try again in a minute. "
        f"Details: {last_error}"
    )


def generate_text(
    prompt: str,
    system_instruction: str | None = None,
    json_output: bool = False,
) -> str:
    """
    Send a prompt to Gemini and return the reply text.
    system_instruction holds trusted rules; the prompt holds user input and document text.
    temperature=0 makes factual answers more consistent.
    json_output asks Gemini to return only valid JSON.
    """
    client = get_client()

    config = types.GenerateContentConfig(
        temperature=0.0,
        system_instruction=system_instruction,
        response_mime_type="application/json" if json_output else None,
    )

    response = call_with_retry(
        lambda: client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=config,
        )
    )

    text = (response.text or "").strip()
    if not text:
        raise LLMError("Gemini returned an empty response.")
    return text