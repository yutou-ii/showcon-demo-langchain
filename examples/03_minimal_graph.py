from langchain_core.messages import AIMessageChunk, HumanMessage
from app.agent import build_chat_graph
from app.model import create_chat_model

def main() -> None:
    graph = build_chat_graph(create_chat_model())
    config = {"configurable": {"thread_id": "terminal-demo"}}

    while True:
        user_text = input("You:").strip()
        if user_text.lower() in {"exit", "quit"}:
            break
        if not user_text:
            continue

        print("Assistant:", end="", flush=True)
        for message, _metadata in graph.stream(
            {"messages": [HumanMessage(content=user_text)]},
            config,
            stream_mode="messages",
        ):
            if isinstance(message, AIMessageChunk) and isinstance(message.content, str):
                print(message.content, end="", flush=True)
        print()


if __name__ == "__main__":
    main()