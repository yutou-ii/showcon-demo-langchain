from pathlib import Path
import pytest

from pydantic import SecretStr, ValidationError

from app.config import Settings, get_settings

REQUIRED_ENV = {
    "OPENAI_API_KEY": "test-key",
    "OPENAI_BASE_URL": "https://models.example.test/v1",
    "OPENAI_MODEL": "test-model",
}


def test_settings_read_required_environment(
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name, value in REQUIRED_ENV.items():
        monkeypatch.setenv(name, value)

    settings = Settings(_env_file=None)

    assert settings.openai_api_key.get_secret_value() == "test-key"
    assert settings.openai_base_url == "https://models.example.test/v1"
    assert settings.openai_model == "test-model"


@pytest.mark.parametrize("missing_name", REQUIRED_ENV)
def test_settings_names_each_missing_variable(
        monkeypatch: pytest.MonkeyPatch,
        missing_name: str,
) -> None:
    for name, value in REQUIRED_ENV.items():
        monkeypatch.setenv(name, value)
    monkeypatch.delenv(missing_name, raising=False)

    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None)

    assert missing_name in str(error.value)


def test_get_settings_reuses_same_instance(
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name, value in REQUIRED_ENV.items():
        monkeypatch.setenv(name, value)

    get_settings.cache_clear()

    first_settings = get_settings()
    second_settings = get_settings()

    assert first_settings is second_settings

    get_settings.cache_clear()


def test_settings_accepts_external_skills_root() -> None:
    settings = Settings(
        OPENAI_API_KEY=SecretStr("test-key"),
        OPENAI_BASE_URL="https://models.example.test/v1",
        OPENAI_MODEL="test-model",
        SKILLS_ROOT="D:/company/skills",
    )

    assert settings.skills_root == Path("D:/company/skills")
