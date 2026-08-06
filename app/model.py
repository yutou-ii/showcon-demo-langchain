from langchain_openai import ChatOpenAI

from app.config import Settings, get_settings


def create_chat_model(settings: Settings | None = None) -> ChatOpenAI:
    if settings is None:
        settings = get_settings()

    return ChatOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        model=settings.openai_model,
        streaming=True,
        timeout=60,
        max_retries=2,
    )