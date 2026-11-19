from fastapi.testclient import TestClient

from app.main import app
from app.routers import agent as agent_router


def test_agent_endpoint_returns_answer_and_tool_log(monkeypatch):
    def fake_run_agent(request):
        return {
            "answer": "Here is a plan.",
            "tool_calls": [
                {"name": "create_task_list", "arguments": {"request": request}, "status": "ok"}
            ],
            "limit_reached": False,
        }

    monkeypatch.setattr(agent_router, "run_agent", fake_run_agent)

    with TestClient(app) as client:
        response = client.post("/agent", json={"request": "plan my first week"})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "Here is a plan."
    assert body["tool_calls"][0]["name"] == "create_task_list"
    assert body["limit_reached"] is False


def test_agent_endpoint_rejects_short_requests():
    with TestClient(app) as client:
        response = client.post("/agent", json={"request": "hi"})

    assert response.status_code == 422