from typing import List

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.model import create_chat_model

def main() -> None:
    model = create_chat_model()

    history:List[BaseMessage] = [
        SystemMessage(content="You are a concise,helpful assistant.")
    ]

    while True:
        user_text = input("User:").strip()

        if user_text.lower() in {"quit", "exit"}:
            break

        if not user_text:
            continue

        history.append(HumanMessage(content=user_text))

        answer_parts: List[str] = []
        print("Assistant:", end="", flush=True)

        for chunk in model.stream(history):
            if isinstance(chunk.content, str):
                print(chunk.content, end="", flush=True)
                answer_parts.append(chunk.content)

        print()

        history.append(
            AIMessage(content="".join(answer_parts))
        )


if __name__ == "__main__":
    main()