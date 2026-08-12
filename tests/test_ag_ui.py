from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from app.main import create_app

def test_agent_endpoint_streams_ag_ui_events() -> None:
    app=create_app(FakeListChatModel(responses=["hello"]))
    payload = {
        "threadId": "thread-test",
        "runId": "run-test",
        "state": {},
        "messages": [{"id": "user-1", "role": "user", "content": "hi"}],
        "tools": [],
        "context": [],
        "forwardedProps": {}
    }

    with TestClient(app).stream("POST", "/agent", json=payload) as response:
        body = "".join(response.iter_text())

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert '"type":"RUN_STARTED"' in body
    assert '"type":"TEXT_MESSAGE_CONTENT"' in body
    assert '"type":"RUN_FINISHED"' in body
    assert "hello" in body
