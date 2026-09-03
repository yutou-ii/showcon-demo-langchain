import json
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.agent import build_chat_graph
from app.documents.models import ContractSection, ParsedDocument
from app.documents.store import InMemoryDocumentStore
from app.skills.registry import SkillRegistry
from tests.fakes import BindableFakeMessagesListChatModel


def test_graph_executes_clause_and_skill_tools(tmp_path) -> None:
    skill_root = tmp_path / "legal-plain-explanation"
    references = skill_root / "references"
    references.mkdir(parents=True)
    (skill_root / "SKILL.md").write_text(
        "---\n"
        "name: legal-plain-explanation\n"
        "description: 将合同条款翻译成大白话。\n"
        "---\n\n"
        "严格输出原文、白话解释、实际案例。\n",
        encoding="utf-8",
    )
    (references / "contract-terms.md").write_text(
        "连带责任：可以向其中任何一方要求承担全部责任。\n",
        encoding="utf-8",
    )

    store = InMemoryDocumentStore()
    document_id = store.put(
        ParsedDocument(
            filename="示例合同.docx",
            title="示例合同",
            sections=(
                ContractSection(
                    section_id="section-1",
                    number="第八条",
                    heading="保证责任",
                    content="保证人承担连带责任。",
                ),
            ),
            blocks=(),
            table_count=0,
        )
    )
    model = BindableFakeMessagesListChatModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "id": "call-clause",
                        "name": "find_contract_clause",
                        "args": {"query": "连带责任"}
                    }
                ],
            ),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "id": "call-skill",
                        "name": "read_skill_file",
                        "args": {
                            "skill_name": "legal-plain-explanation",
                            "relative_path": "SKILL.md",
                        },
                    }
                ],
            ),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "id": "call-reference",
                        "name": "read_skill_file",
                        "args": {
                            "skill_name": "legal-plain-explanation",
                            "relative_path": "references/contract-terms.md",
                        },
                    }
                ],
            ),
            AIMessage(content="最终三段式解释")
        ]
    )
    graph = build_chat_graph(model, store, SkillRegistry(tmp_path))

    result = graph.invoke(
        {
            "messages": [HumanMessage(content="连带责任是什么意思？")],
            "ag-ui": {
                "context": [
                    {
                        "description": "当前对话中用户已上传的合同",
                        "value": json.dumps({"document_id": document_id}),
                    }
                ]
            },
        },
        {
            "configurable": {"thread_id": "tool-thread"},
            "recursion_limit": 12,
        },
    )

    tool_messages = [
        message for message in result["messages"] if isinstance(message, ToolMessage)
    ]
    assert len(tool_messages) == 3
    assert "保证人承担连带责任" in tool_messages[0].content
    assert "严格输出原文" in tool_messages[1].content
    assert "可以向其中任何一方" in tool_messages[2].content
    assert result["messages"][-1].content == "最终三段式解释"
