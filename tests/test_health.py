from fastapi.testclient import TestClient
from tests.fakes import BindableFakeListChatModel

from app.main import create_app
from app.documents.store import InMemoryDocumentStore
from app.skills.registry import SkillRegistry

def test_health_does_not_call_the_model(tmp_path) -> None:
    app = create_app(
        model=BindableFakeListChatModel(responses=["hello"]),
        document_store=InMemoryDocumentStore(),
        skill_registry=SkillRegistry(tmp_path),
    )

    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_local_frontend_origin_is_allowed(tmp_path) -> None:
    app = create_app(
        model=BindableFakeListChatModel(responses=["hello"]),
        document_store=InMemoryDocumentStore(),
        skill_registry=SkillRegistry(tmp_path),
    )

    response = TestClient(app).options(
        "/agent",
        headers={
            "Origin":"http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"