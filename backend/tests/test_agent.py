from types import SimpleNamespace

from app.services import agent


class FakeModel:
    """Returns a scripted sequence of responses, one per Gemini call."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def generate_content(self, model, contents, config):
        self.calls += 1
        return self.responses.pop(0)


def text_reply(text):
    return SimpleNamespace(text=text, function_calls=[], candidates=[])


def tool_reply(name, args):
    call = SimpleNamespace(name=name, args=args)
    content = SimpleNamespace(role="model", parts=[])
    return SimpleNamespace(text=None, function_calls=[call], candidates=[SimpleNamespace(content=content)])


def install_fake_model(monkeypatch, responses):
    model = FakeModel(responses)
    fake_client = SimpleNamespace(models=model)
    monkeypatch.setattr(agent, "get_client", lambda: fake_client)
    return model


def test_plain_answer_needs_no_tools(monkeypatch):
    install_fake_model(monkeypatch, [text_reply("Hello there.")])

    result = agent.run_agent("say hello")

    assert result["answer"] == "Hello there."
    assert result["tool_calls"] == []
    assert result["limit_reached"] is False


def test_tool_is_run_and_result_returned_to_model(monkeypatch):
    model = install_fake_model(
        monkeypatch,
        [
            tool_reply("create_task_list", {"request": "plan my first week"}),
            text_reply("Here is your plan."),
        ],
    )
    run_calls = []

    def fake_run_tool(name, arguments):
        run_calls.append((name, arguments))
        return {"tool": name, "status": "ok", "tasks": []}

    monkeypatch.setattr(agent, "run_tool", fake_run_tool)

    result = agent.run_agent("help me plan my first week")

    assert run_calls == [("create_task_list", {"request": "plan my first week"})]
    assert result["answer"] == "Here is your plan."
    assert result["tool_calls"][0]["name"] == "create_task_list"
    assert result["tool_calls"][0]["status"] == "ok"
    assert model.calls == 2


def test_tool_limit_stops_the_loop(monkeypatch):
    # Four different tools are requested. Three run, the fourth would exceed the limit,
    # and the final call (with no tools offered) returns the answer.
    requests = [
        tool_reply("create_task_list", {"request": "plan my week"}),
        tool_reply("search_knowledge_base", {"query": "leave policy"}),
        tool_reply("extract_policy_information", {"policy_topic": "whistleblower policy"}),
        tool_reply("generate_onboarding_checklist", {"role": "engineer"}),
    ]
    install_fake_model(monkeypatch, requests + [text_reply("Stopped here.")])
    monkeypatch.setattr(
        agent,
        "run_tool",
        lambda name, arguments: {"tool": name, "status": "ok", "tasks": []},
    )

    result = agent.run_agent("keep going")

    assert len(result["tool_calls"]) == agent.MAX_TOOL_CALLS
    assert result["limit_reached"] is True
    assert result["answer"] == "Stopped here."


def test_invalid_tool_arguments_are_reported_not_executed(monkeypatch):
    install_fake_model(
        monkeypatch,
        [
            tool_reply("summarize_document", {"document_id": "not-an-id"}),
            text_reply("I could not summarize that document."),
        ],
    )

    result = agent.run_agent("summarize my document")

    assert result["tool_calls"][0]["status"] == "invalid_input"
    assert result["answer"] == "I could not summarize that document."


def test_empty_final_reply_raises_a_clear_error(monkeypatch):
    install_fake_model(monkeypatch, [text_reply("")])

    try:
        agent.run_agent("anything")
    except agent.LLMError as exc:
        assert "empty" in str(exc)
    else:
        raise AssertionError("expected LLMError for an empty reply")

def test_repeated_tool_is_skipped_not_run_again(monkeypatch):
    install_fake_model(
        monkeypatch,
        [
            tool_reply("search_knowledge_base", {"query": "how to report a violation"}),
            tool_reply("search_knowledge_base", {"query": "whistleblower report violation"}),
            text_reply("Here is the answer."),
        ],
    )
    run_calls = []

    def fake_run_tool(name, arguments):
        run_calls.append(name)
        return {"tool": name, "status": "ok", "results": []}

    monkeypatch.setattr(agent, "run_tool", fake_run_tool)

    result = agent.run_agent("how do I report a violation")

    assert run_calls == ["search_knowledge_base"]
    assert len(result["tool_calls"]) == 1
    assert result["answer"] == "Here is the answer."
    assert result["limit_reached"] is False