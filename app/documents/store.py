from typing import Protocol
from uuid import uuid4

from app.documents.models import ParsedDocument


class DocumentNotFoundError(KeyError):
    pass


class DocumentStore(Protocol):
    def put(self, document: ParsedDocument) -> str: ...

    def get(self, document_id: str) -> ParsedDocument: ...


class InMemoryDocumentStore:
    def __init__(self) -> None:
        self._document: dict[str, ParsedDocument] = {}

    def put(self, document: ParsedDocument) -> str:
        document_id = str(uuid4())
        self._document[document_id] = document
        return document_id

    def get(self, document_id) -> ParsedDocument:
        try:
            return self._document[document_id]
        except KeyError as error:
            raise DocumentNotFoundError(document_id) from error
