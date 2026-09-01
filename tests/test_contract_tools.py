import json
from types import SimpleNamespace

import pytest

from app.documents.models import ContractSection, ParsedDocument
from app.documents.store import InMemoryDocumentStore
from app.tools.context import (
    MissingDocumentContextError,
    extract_current_document_id,
)
from app.tools.contract import create_contract_tools
from app.skills.registry import SkillRegistry
from app.tools.skill import create_skill_tools


def uploaded_document() -> ParsedDocument:
    return ParsedDocument(
        filename="示例采购合同.docx",
        title="示例采购合同",
        sections=(
            ContractSection(
                section_id="section-1",
                number="第一条",
                heading="付款方式",
                content="甲方应当于验收后十日内付款。",
            ),
            ContractSection(
                section_id="section-2",
                number="第二条",
                heading="违约责任",
                content="保证人承担连带责任。",
            ),
        ),
        blocks=(),
        table_count=0,
    )


def runtime_for(document_id: str):
    return SimpleNamespace(
        state={
            "ag-ui": {
                "context": [
                    {
                        "description": "当前对话中用户已上传的合同",
                        "value": json.dumps(
                            {
                                "document_id": document_id,
                                "filename": "示例采购合同.docx",
                            },
                            ensure_ascii=False,
                        ),
                    }
                ]
            }
        }
    )


def test_extract_document_id_rejects_missing_context() -> None:
    with pytest.raises(MissingDocumentContextError):
        extract_current_document_id(
            {"ag-ui": {"context": []}}
        )


def test_outline_and_clause_tools_use_context_document_id() -> None:
    store = InMemoryDocumentStore()
    document_id = store.put(uploaded_document())
    outline_tool, clause_tool = create_contract_tools(store)
    runtime = runtime_for(document_id)

    outline = outline_tool.func(runtime=runtime)
    matches = clause_tool.func(
        query="连带责任",
        runtime=runtime,
    )

    assert outline["filename"] == "示例采购合同.docx"
    assert outline["sections"][1]["heading"] == "违约责任"
    assert matches["matches"][0]["section_id"] == "section-2"
    assert "连带责任" in matches["matches"][0]["content"]


def test_clause_tool_prioritizes_exact_article_number() -> None:
    store = InMemoryDocumentStore()
    document_id = store.put(uploaded_document())
    _, clause_tool = create_contract_tools(store)

    result = clause_tool.func(
        query="第二条",
        runtime=runtime_for(document_id),
    )

    assert result["matches"][0]["section_id"] == "section-2"
    assert result["matches"][0]["match_reason"] == "条款编号精确匹配"


def test_clause_tool_does_not_invent_missing_clause() -> None:
    store = InMemoryDocumentStore()
    document_id = store.put(uploaded_document())
    _, clause_tool = create_contract_tools(store)

    result = clause_tool.func(
        query="自动续约",
        runtime=runtime_for(document_id),
    )

    assert result["error"] == "clause_not_found"
    assert "matches" not in result


def test_read_skill_file_tool_delegates_to_registry(tmp_path) -> None:
    skill = tmp_path / "legal-plain-explanation"
    skill.mkdir()
    (skill / "SKILL.md").write_text(
        "---\n"
        "name: legal-plain-explanation\n"
        "description: 通俗解释合同条款。\n"
        "---\n\n"
        "严格三段式。\n",
        encoding="utf-8",
    )
    registry = SkillRegistry(tmp_path)
    (read_skill_file,) = create_skill_tools(registry)

    result = read_skill_file.func(
        skill_name="legal-plain-explanation",
        relative_path="SKILL.md",
    )

    assert "严格三段式" in result