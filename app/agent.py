from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode
from typing import Any, Annotated
from typing_extensions import NotRequired, TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

from app.documents.store import DocumentStore
from app.skills.registry import SkillRegistry
from app.tools.contract import create_contract_tools
from app.tools.skill import create_skill_tools


BASE_SYSTEM_PROMPT = """你是一个简洁、可靠的助手。

涉及用户上传合同的具体内容时：
1.必须先调用合同工具取得原文，没有工具证据不得编造合同内容。
2.当用户意图命中某个 Skill 时，先用 read_skill_file 读取该 Skill 的 SKILL.md。
3.根据 SKILL.md 的按需加载规则读取必要 reference，不得一次读取所有 reference。
4.工具返回错误时，向用户说明如何恢复，不要掩盖错误。
5.条款工具返回多个可靠候选时，先列出编号和标题请用户确认，不得擅自选一个解释。


{skill_catalog}
"""


AgentState = TypedDict(
    "AgentState",
    {
        "messages": Annotated[list[AnyMessage], add_messages],
        "ag-ui": NotRequired[dict[str, Any]],
    },
)


def build_chat_graph(
        model: BaseChatModel,
        document_store: DocumentStore,
        skill_registry: SkillRegistry,
        checkpointer: BaseCheckpointSaver | None = None,
) -> CompiledStateGraph:
    tools = [
        *create_contract_tools(document_store),
        *create_skill_tools(skill_registry),
    ]
    tool_node = ToolNode(tools)
    model_with_tools = model.bind_tools(tools)
    system_prompt = BASE_SYSTEM_PROMPT.format(
        skill_catalog=skill_registry.catalog_prompt()
    )

    def call_model(state: AgentState) -> dict[str, list]:
        response = model_with_tools.invoke(
            [SystemMessage(content=system_prompt), *state["messages"]]
        )
        return {"messages": [response]}

    def should_continue(state: AgentState) -> str:
        last_message = state["messages"][-1]
        return "tools" if getattr(last_message, "tool_calls", None) else END

    builder = StateGraph(AgentState)
    builder.add_node("model", call_model)
    builder.add_node("tools", tool_node)
    builder.add_edge(START, "model")
    builder.add_conditional_edges("model", should_continue, ["tools", END])
    builder.add_edge("tools", "model")
    return builder.compile(checkpointer=checkpointer or MemorySaver())
