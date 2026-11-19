import pytest
from google.genai import errors as genai_errors

from app.services import llm


def make_server_error():
    return genai_errors.ServerError(503, {"error": {"message": "busy"}}, None)


def make_client_error(code):
    return genai_errors.ClientError(code, {"error": {"message": "nope"}}, None)


def test_temporary_error_is_retried_then_succeeds(monkeypatch):
    monkeypatch.setattr(llm.time, "sleep", lambda s: None)
    attempts = {"count": 0}

    def flaky():
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise make_server_error()
        return "ok"

    assert llm.call_with_retry(flaky) == "ok"
    assert attempts["count"] == 3


def test_permanent_error_is_not_retried(monkeypatch):
    monkeypatch.setattr(llm.time, "sleep", lambda s: None)
    attempts = {"count": 0}

    def retired_model():
        attempts["count"] += 1
        raise make_client_error(404)

    with pytest.raises(llm.LLMError):
        llm.call_with_retry(retired_model)
    assert attempts["count"] == 1


def test_gives_up_after_max_attempts(monkeypatch):
    monkeypatch.setattr(llm.time, "sleep", lambda s: None)
    attempts = {"count": 0}

    def always_busy():
        attempts["count"] += 1
        raise make_server_error()

    with pytest.raises(llm.LLMError, match="busy"):
        llm.call_with_retry(always_busy)
    assert attempts["count"] == llm.MAX_ATTEMPTS