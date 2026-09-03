from tests.fakes import BindableFakeListChatModel
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from app.agent import build_chat_graph
from app.documents.store import InMemoryDocumentStore
from app.skills.registry import SkillRegistry

def test_same_thread_keeps_previous_messages(tmp_path) -> None:
    model = BindableFakeListChatModel(
        responses=["first answer","second answer"]
    )

    document_store = InMemoryDocumentStore()
    skill_registry = SkillRegistry(tmp_path)

    graph = build_chat_graph(
        model,
        document_store,
        skill_registry,
        MemorySaver(),
    )
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

def test_different_threads_do_not_share_messages(tmp_path) -> None:
    model = BindableFakeListChatModel(
        responses=["answer a", "answer b"]
    )
    document_store = InMemoryDocumentStore()
    skill_registry = SkillRegistry(tmp_path)

    graph = build_chat_graph(
        model,
        document_store,
        skill_registry,
        MemorySaver(),
    )

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
