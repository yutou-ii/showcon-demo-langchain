from pydantic import SecretStr

from app.config import Settings
from app.model import create_chat_model


def test_create_chat_model_uses_company_endpoint_settings() -> None:
    settings = Settings(
        OPENAI_API_KEY=SecretStr("test-key"),
        OPENAI_BASE_URL="https://models.example.test/v1",
        OPENAI_MODEL="test-model",
    )

    model = create_chat_model(settings)

    assert model.model_name == "test-model"
    assert model.openai_api_base == "https://models.example.test/v1"
    assert model.openai_api_key.get_secret_value() == "test-key"
    assert model.streaming is True