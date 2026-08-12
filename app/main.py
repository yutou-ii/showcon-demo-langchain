from ag_ui_langgraph import LangGraphAgent, add_langgraph_fastapi_endpoint
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.language_models.chat_models import BaseChatModel

from app.agent import build_chat_graph
from app.model import create_chat_model

AGENT_ID = "local_chat"

def create_app(model: BaseChatModel | None = None) -> FastAPI:
    resolved_model = model or create_chat_model()
    graph = build_chat_graph(resolved_model)
    agent = LangGraphAgent(
        name=AGENT_ID,
        description="A local streaming chat agent.",
        graph=graph,
    )

    fastapi_app = FastAPI(title="Local Chat Agent")
    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    @fastapi_app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    add_langgraph_fastapi_endpoint(fastapi_app, agent, path="/agent")

    return fastapi_app

app = create_app()

# 需要断点调试直接用pycharm的debugger模式
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)