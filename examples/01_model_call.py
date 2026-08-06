from langchain_core.messages import HumanMessage, SystemMessage
from app.model import create_chat_model

def main() -> None:
    model = create_chat_model()

    response = model.invoke(
        [
            SystemMessage(content="You are a concise,helpful assistant."),
            HumanMessage(content="请用一句话解释LangChain是什么。")
        ]
    )

    print(response.content)

if __name__ == '__main__':
    main()