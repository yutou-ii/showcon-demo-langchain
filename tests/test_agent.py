from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from app.agent import build_chat_graph

def test_same_thread_keeps_previous_messages() -> None:
    model = FakeListChatModel(
        responses=["first answer","second answer"]
    )
    graph = build_chat_graph(model,MemorySaver())
    config = {"configurable" : {"thread_id":"thread-a"}}

    graph.invoke(
        {"messages" : [HumanMessage(content="first")]},
        config
    )
    result = graph.invoke(
        {"messages" : [HumanMessage(content="second")]},
        config
    )

    assert [message.content for message in result["messages"]] == [
        "first",
        "first answer",
        "second",
        "second answer"
    ]

def test_different_threads_do_not_share_messages() -> None:
    model = FakeListChatModel(
        responses=["answer a", "answer b"]
    )
    graph = build_chat_graph(model, MemorySaver())

    graph.invoke(
        {"messages" : [HumanMessage(content="message a")]},
        {"configurable" : {"thread_id" : "thread-a"}}
    )
    result = graph.invoke(
        {"messages" : [HumanMessage(content="message b")]},
        {"configurable" : {"thread_id" : "thread-b"}}
    )

    assert [message.content for message in result["messages"]] == [
        "message b",
        "answer b"
    ]
