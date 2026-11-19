import json

from app.services import rag


def make_hit(score: float = 0.8, page: int = 79) -> dict:
    return {
        "text": "Takako worked at the shop in exchange for room and board.",
        "document_id": "a" * 32,
        "filename": "novel.pdf",
        "page_number": page,
        "chunk_index": 0,
        "score": score,
    }


def json_reply(answer: str = "Answer [1].") -> str:
    return json.dumps({"answered": True, "answer": answer, "cited_sources": [1]})


def test_no_history_skips_the_rewrite_step(monkeypatch):
    monkeypatch.setattr(rag, "search_chunks", lambda *a, **k: [make_hit()])
    calls = []

    def fake_llm(prompt, system_instruction=None, json_output=False):
        calls.append(system_instruction)
        return json_reply("Because of room and board [1].")

    result = rag.answer_question("Why does Takako stay?", history=[], llm=fake_llm)

    assert result["standalone_question"] == "Why does Takako stay?"
    assert calls == [rag.SYSTEM_INSTRUCTION]  # only the answer call, no rewrite


def test_follow_up_is_rewritten_before_searching(monkeypatch):
    searched = {}

    def fake_search(query, **kwargs):
        searched["query"] = query
        return [make_hit()]

    monkeypatch.setattr(rag, "search_chunks", fake_search)

    def fake_llm(prompt, system_instruction=None, json_output=False):
        if system_instruction == rag.REWRITE_INSTRUCTION:
            return "Satoru after baby died"
        return json_reply("He comforted her [1].")

    history = [
        {"role": "user", "content": "Tell me about Satoru's family."},
        {"role": "assistant", "content": "Satoru and Takako had a child that died."},
    ]
    result = rag.answer_question("what happened to him after that?", history=history, llm=fake_llm)

    assert searched["query"] == "Satoru after baby died"
    assert result["standalone_question"] == "Satoru after baby died"
    assert result["grounded"] is True


def test_history_is_included_in_the_answer_prompt(monkeypatch):
    monkeypatch.setattr(rag, "search_chunks", lambda *a, **k: [make_hit()])
    seen = {}

    def fake_llm(prompt, system_instruction=None, json_output=False):
        if system_instruction == rag.SYSTEM_INSTRUCTION:
            seen["prompt"] = prompt
        return json_reply()

    history = [{"role": "user", "content": "Earlier question"}]
    rag.answer_question("Follow-up question", history=history, llm=fake_llm)

    assert "Conversation so far:" in seen["prompt"]
    assert "Earlier question" in seen["prompt"]


def test_empty_rewrite_falls_back_to_original_question(monkeypatch):
    monkeypatch.setattr(rag, "search_chunks", lambda *a, **k: [make_hit()])

    def fake_llm(prompt, system_instruction=None, json_output=False):
        if system_instruction == rag.REWRITE_INSTRUCTION:
            return "   "
        return json_reply()

    history = [{"role": "user", "content": "Earlier"}]
    result = rag.answer_question("what about that?", history=history, llm=fake_llm)

    assert result["standalone_question"] == "what about that?"


def test_overlong_rewrite_falls_back_to_original_question(monkeypatch):
    monkeypatch.setattr(rag, "search_chunks", lambda *a, **k: [make_hit()])

    def fake_llm(prompt, system_instruction=None, json_output=False):
        if system_instruction == rag.REWRITE_INSTRUCTION:
            return "word " * 100  # far longer than the limit
        return json_reply()

    history = [{"role": "user", "content": "Earlier"}]
    result = rag.answer_question("what about that?", history=history, llm=fake_llm)

    assert result["standalone_question"] == "what about that?"