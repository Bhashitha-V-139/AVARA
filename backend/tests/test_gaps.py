import json

from app.services import rag


def make_hit(score=0.8, page=99):
    return {
        "text": "The Whistleblowing Investigation Committee addresses reported violations.",
        "document_id": "b" * 32,
        "filename": "policy.pdf",
        "page_number": page,
        "chunk_index": 0,
        "score": score,
    }


def test_missing_parts_are_returned_and_answer_stays_grounded(monkeypatch):
    monkeypatch.setattr(rag, "search_chunks", lambda *a, **k: [make_hit()])

    def fake_llm(prompt, system_instruction=None, json_output=False):
        return json.dumps({
            "answered": True,
            "answer": "Violations are addressed by the Whistleblowing Investigation Committee [1].",
            "cited_sources": [1],
            "missing": ["disciplinary consequences"],
        })

    result = rag.answer_question("What happens when an employee violates the Code of Conduct?", llm=fake_llm)

    assert result["grounded"] is True
    assert result["missing"] == ["disciplinary consequences"]


def test_missing_key_defaults_to_empty_list(monkeypatch):
    monkeypatch.setattr(rag, "search_chunks", lambda *a, **k: [make_hit()])

    def fake_llm(prompt, system_instruction=None, json_output=False):
        return json.dumps({"answered": True, "answer": "Answer [1].", "cited_sources": [1]})

    result = rag.answer_question("any question", llm=fake_llm)

    assert result["missing"] == []


def test_invalid_missing_items_are_ignored(monkeypatch):
    monkeypatch.setattr(rag, "search_chunks", lambda *a, **k: [make_hit()])

    def fake_llm(prompt, system_instruction=None, json_output=False):
        return json.dumps({
            "answered": True,
            "answer": "Answer [1].",
            "cited_sources": [1],
            "missing": ["valid gap", "", 42, None, "   "],
        })

    result = rag.answer_question("any question", llm=fake_llm)

    assert result["missing"] == ["valid gap"]