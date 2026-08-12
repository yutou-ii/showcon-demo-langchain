from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from app.main import create_app

def test_health_does_not_call_the_model() -> None:
    app = create_app(FakeListChatModel(responses=[]))

    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_local_frontend_origin_is_allowed() -> None:
    app = create_app(FakeListChatModel(responses=[]))

    response = TestClient(app).options(
        "/agent",
        headers={
            "Origin":"http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"