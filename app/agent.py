import hashlib

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode

SYSTEM_PROMPT = "You are a concise, helpful assistant."

# 模拟天气的候选项
_CONDITIONS = ["晴", "多云", "阴", "小雨", "雷阵雨", "大雪"]


@tool
def get_weather(city: str) -> str:
    """获取指定城市的天气信息。

    任意城市均可查询，返回基于城市名确定性生成的模拟天气。
    """
    seed = int(hashlib.md5(city.encode()).hexdigest(), 16)
    cond = _CONDITIONS[seed % len(_CONDITIONS)]
    temp = 10 + seed % 30          # 10~39°C
    humidity = 30 + seed % 60      # 30~89%
    wind = seed % 8 + 1            # 1~8 级
    return f"{city}：{cond}，气温 {temp}°C，湿度 {humidity}%，风力 {wind} 级"


def build_chat_graph(
        model: BaseChatModel,
        checkpointer: BaseCheckpointSaver | None = None
) -> CompiledStateGraph:
    tools = [get_weather]
    tool_node = ToolNode(tools)
    model_with_tools = model.bind_tools(tools)

    def call_model(state: MessagesState) -> dict[str, list]:
        response = model_with_tools.invoke(
            [
                SystemMessage(content=SYSTEM_PROMPT),
                *state["messages"]
            ]
        )
        return {"messages": [response]}

    def should_continue(state: MessagesState) -> str:
        last_message = state["messages"][-1]
        if getattr(last_message, "tool_calls", None):
            return "tools"
        return END

    builder = StateGraph(MessagesState)
    builder.add_node("model", call_model)
    builder.add_node("tools", tool_node)
    builder.add_edge(START, "model")
    builder.add_conditional_edges("model", should_continue, ["tools", END])
    builder.add_edge("tools", "model")

    return builder.compile(
        checkpointer=checkpointer or MemorySaver()
    )
