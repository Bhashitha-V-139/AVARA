from app.services import tools

DOC_ID = "a" * 32


def fake_llm(reply: str):
    """Stands in for Gemini: always returns the same reply."""
    def _fake(prompt, system_instruction=None, json_output=False):
        return reply
    return _fake


def hit(score=0.8, page=5, text="Employees receive 20 days of annual leave.", filename="handbook.pdf"):
    return {
        "text": text,
        "document_id": DOC_ID,
        "filename": filename,
        "page_number": page,
        "chunk_index": 0,
        "score": score,
    }


class FakeCollection:
    """Stands in for ChromaDB: returns the chunks given to it."""

    def __init__(self, chunks):
        self.chunks = chunks

    def get(self, where=None):
        return {
            "documents": [c["text"] for c in self.chunks],
            "metadatas": [
                {
                    "chunk_index": c["chunk_index"],
                    "filename": "handbook.pdf",
                    "page_number": c["page_number"],
                    "document_id": DOC_ID,
                }
                for c in self.chunks
            ],
        }


# ----- Input validation -----

def test_unknown_tool_is_rejected():
    result = tools.run_tool("delete_everything", {})
    assert result["status"] == "invalid_input"


def test_bad_document_id_is_rejected():
    result = tools.run_tool("summarize_document", {"document_id": "not-an-id"})
    assert result["status"] == "invalid_input"


def test_extra_arguments_are_rejected():
    result = tools.run_tool("search_knowledge_base", {"query": "annual leave", "delete_all": True})
    assert result["status"] == "invalid_input"


def test_non_object_arguments_are_rejected():
    result = tools.run_tool("create_task_list", "plan my week")
    assert result["status"] == "invalid_input"


# ----- Search -----

def test_search_respects_relevance_threshold(monkeypatch):
    monkeypatch.setattr(tools, "search_chunks", lambda *a, **k: [hit(score=0.10)])
    result = tools.run_tool("search_knowledge_base", {"query": "refund policy"})
    assert result["status"] == "not_found"


def test_search_returns_page_numbers(monkeypatch):
    monkeypatch.setattr(tools, "search_chunks", lambda *a, **k: [hit(score=0.8, page=5)])
    result = tools.run_tool("search_knowledge_base", {"query": "annual leave"})
    assert result["status"] == "ok"
    assert result["results"][0]["page_number"] == 5


# ----- Policy information -----

def test_policy_fields_without_citations_are_marked_not_stated(monkeypatch):
    monkeypatch.setattr(tools, "search_chunks", lambda *a, **k: [hit()])
    reply = (
        '{"purpose": {"value": "Protects whistleblowers.", "sources": [1]},'
        ' "consequences": {"value": null, "sources": []}}'
    )
    monkeypatch.setattr(tools, "generate_text", fake_llm(reply))

    result = tools.run_tool("extract_policy_information", {"policy_topic": "whistleblower policy"})

    assert result["status"] == "ok"
    assert result["fields"]["purpose"]["citations"] == [{"document": "handbook.pdf", "page_number": 5}]
    assert result["fields"]["consequences"]["value"] == tools.NOT_STATED
    assert result["fields"]["scope"]["value"] == tools.NOT_STATED


# ----- Onboarding checklist -----

def test_checklist_drops_items_with_invalid_sources(monkeypatch):
    monkeypatch.setattr(tools, "search_chunks", lambda *a, **k: [hit()])
    reply = (
        '{"items": [{"task": "Set up laptop", "sources": [1]},'
        ' {"task": "Invented task", "sources": [9]}]}'
    )
    monkeypatch.setattr(tools, "generate_text", fake_llm(reply))

    result = tools.run_tool("generate_onboarding_checklist", {"role": "software engineer"})

    assert result["status"] == "ok"
    assert [item["task"] for item in result["items"]] == ["Set up laptop"]


# ----- Document summary -----

def test_summary_discloses_pages_read(monkeypatch):
    chunks = [
        {"chunk_index": 0, "page_number": 1, "text": "Introduction to the policy."},
        {"chunk_index": 1, "page_number": 2, "text": "Employees must report concerns."},
        {"chunk_index": 2, "page_number": 3, "text": "Contact HR for questions."},
    ]
    monkeypatch.setattr(tools, "get_document", lambda doc_id: {"filename": "handbook.pdf"})
    monkeypatch.setattr(tools, "get_collection", lambda: FakeCollection(chunks))
    reply = '{"sections": [{"title": "Reporting", "summary": "Concerns must be reported.", "sources": [2]}]}'
    monkeypatch.setattr(tools, "generate_text", fake_llm(reply))

    result = tools.run_tool("summarize_document", {"document_id": DOC_ID})

    assert result["status"] == "ok"
    assert result["coverage"]["chunks_read"] == 3
    assert result["coverage"]["chunks_total"] == 3
    assert result["coverage"]["pages_read"] == [1, 2, 3]
    assert result["sections"][0]["citations"] == [{"document": "handbook.pdf", "page_number": 2}]


def test_summary_includes_keyword_sections_beyond_first_40_chunks(monkeypatch):
    chunks = [{"chunk_index": i, "page_number": i + 1, "text": "Routine text."} for i in range(45)]
    chunks[44]["text"] = "The scope of this policy covers all employees."
    monkeypatch.setattr(tools, "get_document", lambda doc_id: {"filename": "handbook.pdf"})
    monkeypatch.setattr(tools, "get_collection", lambda: FakeCollection(chunks))
    reply = '{"sections": [{"title": "Scope", "summary": "Covers all employees.", "sources": [1]}]}'
    monkeypatch.setattr(tools, "generate_text", fake_llm(reply))

    result = tools.run_tool("summarize_document", {"document_id": DOC_ID})

    assert result["coverage"]["chunks_read"] == 41
    assert 45 in result["coverage"]["pages_read"]


# ----- Task list and error handling -----

def test_task_list_can_come_from_request_alone(monkeypatch):
    monkeypatch.setattr(tools, "search_chunks", lambda *a, **k: [])
    reply = '{"tasks": [{"task": "Book a review meeting", "sources": []}]}'
    monkeypatch.setattr(tools, "generate_text", fake_llm(reply))

    result = tools.run_tool("create_task_list", {"request": "plan my review meeting"})

    assert result["status"] == "ok"
    assert result["tasks"][0]["from"] == "request"


def test_malformed_model_output_is_an_error(monkeypatch):
    monkeypatch.setattr(tools, "search_chunks", lambda *a, **k: [hit()])
    monkeypatch.setattr(tools, "generate_text", fake_llm("this is not json"))

    result = tools.run_tool("create_task_list", {"request": "prepare for my first week"})

    assert result["status"] == "error"