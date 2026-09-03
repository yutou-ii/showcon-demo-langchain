from fastapi.testclient import TestClient
from tests.fakes import BindableFakeListChatModel

from app.main import create_app
from app.documents.store import InMemoryDocumentStore
from app.skills.registry import SkillRegistry

def test_agent_endpoint_streams_ag_ui_events(tmp_path) -> None:
    app=create_app(
        model=BindableFakeListChatModel(responses=["hello"]),
        document_store=InMemoryDocumentStore(),
        skill_registry=SkillRegistry(tmp_path),
    )
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
