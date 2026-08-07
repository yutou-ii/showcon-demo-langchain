from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph

SYSTEM_PROMPT = "You are a concise, helpful assistant."

def build_chat_graph(
        model: BaseChatModel,
        checkpointer: BaseCheckpointSaver | None = None
) -> CompiledStateGraph:
    def call_model(state: MessagesState) -> dict[str, list]:
        response = model.invoke(
            [
                SystemMessage(content=SYSTEM_PROMPT),
                *state["messages"]
            ]
        )
        return {"messages": [response]}

    builder = StateGraph(MessagesState)
    builder.add_node("model", call_model)
    builder.add_edge(START, "model")
    builder.add_edge("model", END)

    return builder.compile(
        checkpointer=checkpointer or MemorySaver()
    )