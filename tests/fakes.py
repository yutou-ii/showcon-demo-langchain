from collections.abc import Sequence
from typing import Any

from langchain_core.language_models.fake_chat_models import (
    FakeListChatModel,
    FakeMessagesListChatModel,
)


class BindableFakeListChatModel(FakeListChatModel):
    def bind_tools(self, tools: Sequence[Any], **kwargs: Any):
        return self


class BindableFakeMessagesListChatModel(FakeMessagesListChatModel):
    def bind_tools(self, tools: Sequence[Any], **kwargs: Any):
        return self
