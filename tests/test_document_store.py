import pytest

from app.documents.models import ParsedDocument
from app.documents.store import DocumentNotFoundError, InMemoryDocumentStore


def make_document() -> ParsedDocument:
    return ParsedDocument(
        filename="示例合同.docx",
        title="示例合同",
        sections=(),
        blocks=(),
        table_count=0,
    )


def test_store_returns_document_by_random_id() -> None:
    store = InMemoryDocumentStore()
    document_id = store.put(make_document())

    assert document_id != "示例合同.docx"
    assert store.get(document_id).filename == "示例合同.docx"


def test_store_raises_for_unknown_document() -> None:
    store = InMemoryDocumentStore()

    with pytest.raises(DocumentNotFoundError):
        store.get("missing")