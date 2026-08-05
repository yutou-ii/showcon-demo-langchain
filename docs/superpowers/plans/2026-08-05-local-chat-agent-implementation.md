# Local Chat Agent Phase One Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local, streaming, multi-turn chat agent with a CopilotKit/Next.js frontend and a Python FastAPI/LangChain/LangGraph backend connected to the company's OpenAI-compatible endpoint.

**Architecture:** `CopilotChat` calls a same-origin CopilotKit Runtime route in Next.js. The runtime registers an AG-UI `HttpAgent` that forwards runs to the Python FastAPI endpoint; `ag-ui-langgraph` adapts those runs to a one-node LangGraph backed by LangChain `ChatOpenAI` and an in-memory checkpointer.

**Tech Stack:** Next.js 16.3.0, React, TypeScript, CopilotKit 1.66.2 with its v2 APIs, AG-UI client 0.0.57, Python 3.12, FastAPI, LangChain 1.3.14, LangGraph 1.2.10, langchain-openai 1.4.1, ag-ui-langgraph 0.0.42, pytest.

## Global Constraints

- Backend repository: `D:\code\aiagent\0824_langchain\backend`; develop it in PyCharm with `backend\.venv\Scripts\python.exe`.
- Frontend repository: `D:\code\aiagent\0824_langchain\frontend`; develop it in VS Code with Node.js 20+ and npm.
- On Windows PowerShell, use `npm.cmd` and `npx.cmd` if script execution policy blocks `npm.ps1` or `npx.ps1`.
- Pin scaffolding to `create-next-app@16.3.0`, `@copilotkit/react-core@1.66.2`, `@copilotkit/runtime@1.66.2`, `@ag-ui/client@0.0.57`, and `lucide-react@1.28.0`; commit `package-lock.json`.
- Agent ID is exactly `local_chat` in Python, the Next.js runtime, and `CopilotChat`.
- Python AG-UI endpoint is `http://127.0.0.1:8000/agent`; health endpoint is `http://127.0.0.1:8000/health`.
- Next.js runtime base path is `/api/copilotkit`; use the v2 catch-all route `src/app/api/copilotkit/[...path]/route.ts`.
- The model API key exists only in `backend/.env`; never place it in frontend files or commit it.
- First phase includes streaming, process-local multi-turn context, new-chat reset, loading/error feedback, `/health`, tests, and documentation.
- First phase excludes skills/tools, RAG, databases, authentication, persistent history, multi-agent flows, and production deployment.
- Keep the GitHub-generated initial README commits in history; replace README contents through ordinary commits and do not force-push.

---

### Task 1: Run the Official Starter as a Disposable Smoke Test

**Files:**
- Create outside Git: `D:\code\aiagent\0824_langchain\scratch\official-smoke\`
- Do not modify either formal repository.

**Interfaces:**
- Consumes: Company `OPENAI_API_KEY`, `OPENAI_BASE_URL`, and `OPENAI_MODEL` values.
- Produces: Proof that Node, Python, the browser, and the company model endpoint can complete one CopilotKit chat run.

- [ ] **Step 1: Generate the official starter**

Run from `D:\code\aiagent\0824_langchain\scratch`:

```powershell
npx.cmd copilotkit@latest create
```

Choose these answers:

```text
Project name: official-smoke
Enterprise Intelligence Platform: No
Framework: LangGraph (Python)
Package manager: npm
```

- [ ] **Step 2: Locate the generated model configuration**

Run:

```powershell
Set-Location D:\code\aiagent\0824_langchain\scratch\official-smoke
rg -n "create_agent|ChatOpenAI|OPENAI_API_KEY|gpt-" .
```

Expected: at least one Python agent file and one environment example are listed. Record their paths in a temporary note outside Git; the CLI layout may change between releases.

- [ ] **Step 3: Configure the disposable agent for the company endpoint**

In the generated Python agent file, instantiate the model explicitly and pass it to the generated graph or `create_agent` call:

```python
import os

from langchain_openai import ChatOpenAI

model = ChatOpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    base_url=os.environ["OPENAI_BASE_URL"],
    model=os.environ["OPENAI_MODEL"],
    streaming=True,
)
```

Set the three real values only in the generated local `.env` file. Do not paste them into source files or terminal output.

- [ ] **Step 4: Start the starter and verify one answer**

Run:

```powershell
npm.cmd install
npm.cmd run dev
```

Expected: both UI and agent services start. Open the printed local URL, send `你好，请只回复“连接成功”`, and confirm the answer arrives.

- [ ] **Step 5: Stop and preserve the smoke test only as local reference**

Press `Ctrl+C`. Do not initialize Git or copy generated files into the formal repositories. If the smoke test fails, stop here and diagnose the failing layer before starting Task 2.

---

### Task 2: Establish Backend Dependencies and Validated Settings

**Files:**
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `.env.example`
- Create: `app/__init__.py`
- Create: `app/config.py`
- Create: `tests/test_config.py`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: Environment variables `OPENAI_API_KEY`, `OPENAI_BASE_URL`, and `OPENAI_MODEL`.
- Produces: `Settings`, `get_settings() -> Settings`, and a reproducible Python dependency set.

- [ ] **Step 1: Declare runtime and test dependencies**

Create `requirements.txt`:

```text
ag-ui-langgraph==0.0.42
fastapi==0.141.1
langchain==1.3.14
langchain-openai==1.4.1
langgraph==1.2.10
pydantic-settings>=2.0,<3.0
uvicorn[standard]==0.52.1
```

Create `requirements-dev.txt`:

```text
-r requirements.txt
httpx>=0.28,<0.29
pytest>=8.0,<9.0
pytest-asyncio>=0.25,<2.0
```

Run:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

- [ ] **Step 2: Write failing settings tests**

Create `tests/test_config.py`:

```python
import pytest
from pydantic import ValidationError

from app.config import Settings


REQUIRED_ENV = {
    "OPENAI_API_KEY": "test-key",
    "OPENAI_BASE_URL": "https://models.example.test/v1",
    "OPENAI_MODEL": "test-model",
}


def test_settings_read_required_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name, value in REQUIRED_ENV.items():
        monkeypatch.setenv(name, value)

    settings = Settings(_env_file=None)

    assert settings.openai_api_key.get_secret_value() == "test-key"
    assert settings.openai_base_url == "https://models.example.test/v1"
    assert settings.openai_model == "test-model"


@pytest.mark.parametrize("missing_name", REQUIRED_ENV)
def test_settings_name_each_missing_variable(
    monkeypatch: pytest.MonkeyPatch,
    missing_name: str,
) -> None:
    for name, value in REQUIRED_ENV.items():
        monkeypatch.setenv(name, value)
    monkeypatch.delenv(missing_name, raising=False)

    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None)

    assert missing_name in str(error.value)
```

- [ ] **Step 3: Run the tests and confirm they fail**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_config.py -v
```

Expected: collection fails because `app.config` does not exist.

- [ ] **Step 4: Implement validated settings**

Create an empty `app/__init__.py`, then create `app/config.py`:

```python
from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: SecretStr = Field(validation_alias="OPENAI_API_KEY")
    openai_base_url: str = Field(validation_alias="OPENAI_BASE_URL")
    openai_model: str = Field(validation_alias="OPENAI_MODEL")


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

Create `.env.example`:

```dotenv
OPENAI_API_KEY=change-me
OPENAI_BASE_URL=https://company-endpoint.example/v1
OPENAI_MODEL=company-model-name
```

Confirm `.gitignore` contains these rules:

```gitignore
.env
.env.*
!.env.example
```

- [ ] **Step 5: Run the focused and full backend tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_config.py -v
.\.venv\Scripts\python.exe -m pytest -q
```

Expected: all tests pass.

- [ ] **Step 6: Commit the backend foundation**

```powershell
git add requirements.txt requirements-dev.txt .env.example .gitignore app tests
git commit -m "build: add backend settings and dependencies"
```

---

### Task 3: Add the LangChain Model Factory and Learning Examples

**Files:**
- Create: `app/model.py`
- Create: `examples/01_model_call.py`
- Create: `examples/02_stream_chat.py`
- Create: `tests/test_model.py`

**Interfaces:**
- Consumes: `Settings` from Task 2.
- Produces: `create_chat_model(settings: Settings | None = None) -> ChatOpenAI` and two terminal learning programs.

- [ ] **Step 1: Write the failing model factory test**

Create `tests/test_model.py`:

```python
from pydantic import SecretStr

from app.config import Settings
from app.model import create_chat_model


def test_create_chat_model_uses_company_endpoint_settings() -> None:
    settings = Settings(
        OPENAI_API_KEY=SecretStr("test-key"),
        OPENAI_BASE_URL="https://models.example.test/v1",
        OPENAI_MODEL="test-model",
    )

    model = create_chat_model(settings)

    assert model.model_name == "test-model"
    assert model.openai_api_base == "https://models.example.test/v1"
    assert model.openai_api_key.get_secret_value() == "test-key"
    assert model.streaming is True
```

- [ ] **Step 2: Run the test and confirm it fails**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_model.py -v
```

Expected: FAIL because `app.model` does not exist.

- [ ] **Step 3: Implement the model factory**

Create `app/model.py`:

```python
from langchain_openai import ChatOpenAI

from app.config import Settings, get_settings


def create_chat_model(settings: Settings | None = None) -> ChatOpenAI:
    resolved = settings or get_settings()
    return ChatOpenAI(
        api_key=resolved.openai_api_key,
        base_url=resolved.openai_base_url,
        model=resolved.openai_model,
        streaming=True,
        timeout=60,
        max_retries=2,
    )
```

- [ ] **Step 4: Run the test and confirm it passes**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_model.py -v
```

- [ ] **Step 5: Add the single-turn learning example**

Create `examples/01_model_call.py`:

```python
from langchain_core.messages import HumanMessage, SystemMessage

from app.model import create_chat_model


def main() -> None:
    model = create_chat_model()
    response = model.invoke(
        [
            SystemMessage(content="You are a concise, helpful assistant."),
            HumanMessage(content="用一句话解释 LangChain 是什么。"),
        ]
    )
    print(response.content)


if __name__ == "__main__":
    main()
```

Run with a real local `.env`:

```powershell
.\.venv\Scripts\python.exe examples\01_model_call.py
```

Expected: one complete model answer is printed.

- [ ] **Step 6: Add the streaming multi-turn learning example**

Create `examples/02_stream_chat.py`:

```python
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.model import create_chat_model


def main() -> None:
    model = create_chat_model()
    history: list[BaseMessage] = [
        SystemMessage(content="You are a concise, helpful assistant."),
    ]

    while True:
        user_text = input("You: ").strip()
        if user_text.lower() in {"exit", "quit"}:
            break
        if not user_text:
            continue

        history.append(HumanMessage(content=user_text))
        answer_parts: list[str] = []
        print("Assistant: ", end="", flush=True)
        for chunk in model.stream(history):
            if isinstance(chunk.content, str):
                print(chunk.content, end="", flush=True)
                answer_parts.append(chunk.content)
        print()
        history.append(AIMessage(content="".join(answer_parts)))


if __name__ == "__main__":
    main()
```

Run:

```powershell
.\.venv\Scripts\python.exe examples\02_stream_chat.py
```

Send `记住我的名字叫小羽` and then `我的名字是什么？`. Expected: text appears incrementally and the second answer uses the first turn.

- [ ] **Step 7: Run all tests and commit**

```powershell
.\.venv\Scripts\python.exe -m pytest -q
git add app\model.py examples tests\test_model.py
git commit -m "feat: add LangChain model and chat examples"
```

---

### Task 4: Build the Minimal Stateful LangGraph

**Files:**
- Create: `app/agent.py`
- Create: `examples/03_minimal_graph.py`
- Create: `tests/test_agent.py`

**Interfaces:**
- Consumes: any `BaseChatModel` and optional LangGraph checkpointer.
- Produces: `build_chat_graph(model, checkpointer=None) -> CompiledStateGraph` with a single `model` node and process-local thread isolation.

- [ ] **Step 1: Write failing graph memory tests**

Create `tests/test_agent.py`:

```python
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from app.agent import build_chat_graph


def test_same_thread_keeps_previous_messages() -> None:
    model = FakeListChatModel(responses=["first answer", "second answer"])
    graph = build_chat_graph(model, MemorySaver())
    config = {"configurable": {"thread_id": "thread-a"}}

    graph.invoke({"messages": [HumanMessage(content="first")]}, config)
    result = graph.invoke({"messages": [HumanMessage(content="second")]}, config)

    assert [message.content for message in result["messages"]] == [
        "first",
        "first answer",
        "second",
        "second answer",
    ]


def test_different_threads_do_not_share_messages() -> None:
    model = FakeListChatModel(responses=["answer a", "answer b"])
    graph = build_chat_graph(model, MemorySaver())

    graph.invoke(
        {"messages": [HumanMessage(content="message a")]},
        {"configurable": {"thread_id": "thread-a"}},
    )
    result = graph.invoke(
        {"messages": [HumanMessage(content="message b")]},
        {"configurable": {"thread_id": "thread-b"}},
    )

    assert [message.content for message in result["messages"]] == [
        "message b",
        "answer b",
    ]
```

- [ ] **Step 2: Run the tests and confirm they fail**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_agent.py -v
```

Expected: FAIL because `build_chat_graph` does not exist.

- [ ] **Step 3: Implement the one-node graph**

Create `app/agent.py`:

```python
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph


SYSTEM_PROMPT = "You are a concise, helpful assistant."


def build_chat_graph(
    model: BaseChatModel,
    checkpointer: BaseCheckpointSaver | None = None,
) -> CompiledStateGraph:
    def call_model(state: MessagesState) -> dict[str, list]:
        response = model.invoke(
            [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
        )
        return {"messages": [response]}

    builder = StateGraph(MessagesState)
    builder.add_node("model", call_model)
    builder.add_edge(START, "model")
    builder.add_edge("model", END)
    return builder.compile(checkpointer=checkpointer or MemorySaver())
```

- [ ] **Step 4: Run the graph tests**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_agent.py -v
```

Expected: both tests pass.

- [ ] **Step 5: Add the educational graph streaming example**

Create `examples/03_minimal_graph.py`:

```python
from langchain_core.messages import AIMessageChunk, HumanMessage

from app.agent import build_chat_graph
from app.model import create_chat_model


def main() -> None:
    graph = build_chat_graph(create_chat_model())
    config = {"configurable": {"thread_id": "terminal-demo"}}

    while True:
        user_text = input("You: ").strip()
        if user_text.lower() in {"exit", "quit"}:
            break
        if not user_text:
            continue

        print("Assistant: ", end="", flush=True)
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
```

Run it and repeat the two-turn name check from Task 3.

- [ ] **Step 6: Run all tests and commit**

```powershell
.\.venv\Scripts\python.exe -m pytest -q
git add app\agent.py examples\03_minimal_graph.py tests\test_agent.py
git commit -m "feat: add minimal stateful LangGraph agent"
```

---

### Task 5: Expose the Graph through FastAPI and AG-UI

**Files:**
- Create: `app/main.py`
- Create: `tests/conftest.py`
- Create: `tests/test_health.py`
- Create: `tests/test_ag_ui.py`

**Interfaces:**
- Consumes: `build_chat_graph()` and `create_chat_model()`.
- Produces: `create_app(model=None) -> FastAPI`, module-level `app`, `GET /health`, `POST /agent`, and `GET /agent/health`.

- [ ] **Step 1: Supply non-secret test environment defaults**

Create `tests/conftest.py`:

```python
import os


os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("OPENAI_BASE_URL", "https://models.example.test/v1")
os.environ.setdefault("OPENAI_MODEL", "test-model")
```

- [ ] **Step 2: Write failing health and CORS tests**

Create `tests/test_health.py`:

```python
from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from app.main import create_app


def test_health_does_not_call_the_model() -> None:
    app = create_app(FakeListChatModel(responses=[]))

    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_local_frontend_origin_is_allowed() -> None:
    app = create_app(FakeListChatModel(responses=[]))

    response = TestClient(app).options(
        "/agent",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
```

- [ ] **Step 3: Write the failing AG-UI stream test**

Create `tests/test_ag_ui.py`:

```python
from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from app.main import create_app


def test_agent_endpoint_streams_ag_ui_events() -> None:
    app = create_app(FakeListChatModel(responses=["hello"]))
    payload = {
        "threadId": "thread-test",
        "runId": "run-test",
        "state": {},
        "messages": [{"id": "user-1", "role": "user", "content": "hi"}],
        "tools": [],
        "context": [],
        "forwardedProps": {},
    }

    with TestClient(app).stream("POST", "/agent", json=payload) as response:
        body = "".join(response.iter_text())

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert '"type":"RUN_STARTED"' in body
    assert '"type":"TEXT_MESSAGE_CONTENT"' in body
    assert '"type":"RUN_FINISHED"' in body
    assert "hello" in body
```

- [ ] **Step 4: Run the tests and confirm they fail**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_health.py tests\test_ag_ui.py -v
```

Expected: FAIL because `app.main` does not exist.

- [ ] **Step 5: Implement the FastAPI application**

Create `app/main.py`:

```python
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
        allow_origins=["http://localhost:3000"],
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
```

- [ ] **Step 6: Run focused and full tests**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_health.py tests\test_ag_ui.py -v
.\.venv\Scripts\python.exe -m pytest -q
```

Expected: all tests pass without calling a real model.

- [ ] **Step 7: Start the backend in PyCharm and probe it**

Create a PyCharm Python run configuration with:

```text
Module name: uvicorn
Parameters: app.main:app --host 127.0.0.1 --port 8000 --reload
Working directory: D:\code\aiagent\0824_langchain\backend
Interpreter: D:\code\aiagent\0824_langchain\backend\.venv\Scripts\python.exe
```

With the real `backend/.env` present, start it and run:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/agent/health
```

Expected: both return `status: ok`; the second response also names `local_chat`.

- [ ] **Step 8: Commit the backend service**

```powershell
git add app\main.py tests\conftest.py tests\test_health.py tests\test_ag_ui.py
git commit -m "feat: expose chat agent over FastAPI and AG-UI"
```

---

### Task 6: Clone and Scaffold the Formal Next.js Frontend

**Files:**
- Clone: `D:\code\aiagent\0824_langchain\frontend\.git`
- Replace: `README.md`
- Create through scaffolding: `package.json`, `package-lock.json`, `tsconfig.json`, `next.config.ts`, `eslint.config.mjs`, `src/app/*`
- Create: `.env.local.example`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: GitHub repository `https://github.com/yutou-ii/showcon-demo-web.git`.
- Produces: A clean Next.js App Router TypeScript repository with CopilotKit v2 and AG-UI client dependencies.

- [ ] **Step 1: Clone the existing frontend repository**

The current local `frontend` directory is empty. Run from `D:\code\aiagent\0824_langchain`:

```powershell
git clone https://github.com/yutou-ii/showcon-demo-web.git frontend
Set-Location frontend
git status --short --branch
```

Expected: branch `main` tracks `origin/main` and contains only the GitHub-generated README.

- [ ] **Step 2: Replace the tracked README through normal working-tree changes**

```powershell
Remove-Item -LiteralPath README.md
npx.cmd create-next-app@16.3.0 . --typescript --eslint --app --src-dir --use-npm --no-tailwind --no-agents-md --import-alias "@/*" --yes
```

Expected: create-next-app ignores the existing `.git` directory when checking for conflicting files, preserves it, and writes a new README plus the application scaffold. `--no-agents-md` prevents unrelated generated agent instructions. Do not run `git init` and do not force-push.

- [ ] **Step 3: Install the frontend agent dependencies**

```powershell
npm.cmd install @copilotkit/react-core@1.66.2 @copilotkit/runtime@1.66.2 @ag-ui/client@0.0.57 lucide-react@1.28.0
```

Commit the generated `package-lock.json`; it is the exact dependency lock for the project.

- [ ] **Step 4: Add the server-side agent URL example**

Create `.env.local.example`:

```dotenv
AGENT_URL=http://127.0.0.1:8000/agent
```

Ensure `.gitignore` contains:

```gitignore
.env*
!.env.local.example
```

Copy the example to `.env.local` for local use; `.env.local` remains ignored.

- [ ] **Step 5: Verify and commit the untouched scaffold**

```powershell
npm.cmd run lint
npm.cmd run build
git add .
git commit -m "build: scaffold CopilotKit frontend"
```

Expected: lint and production build pass before CopilotKit code is added.

---

### Task 7: Add the v2 CopilotKit Runtime Proxy

**Files:**
- Create: `src/app/api/copilotkit/[...path]/route.ts`
- Use: `.env.local`

**Interfaces:**
- Consumes: `AGENT_URL`, defaulting to `http://127.0.0.1:8000/agent`.
- Produces: `GET` and `POST` handlers under `/api/copilotkit/*`, registering `local_chat` as an AG-UI `HttpAgent`.

- [ ] **Step 1: Create the catch-all Runtime route**

Create `src/app/api/copilotkit/[...path]/route.ts`:

```typescript
import { HttpAgent } from "@ag-ui/client";
import {
  CopilotRuntime,
  createCopilotRuntimeHandler,
} from "@copilotkit/runtime/v2";

const agentUrl = process.env.AGENT_URL ?? "http://127.0.0.1:8000/agent";

const runtime = new CopilotRuntime({
  agents: {
    local_chat: new HttpAgent({ url: agentUrl }),
  },
});

const handler = createCopilotRuntimeHandler({
  runtime,
  basePath: "/api/copilotkit",
});

export { handler as GET, handler as POST };
```

- [ ] **Step 2: Run static verification**

```powershell
npm.cmd run lint
npm.cmd run build
```

Expected: no TypeScript, ESLint, or route build errors.

- [ ] **Step 3: Probe agent discovery with both servers running**

Keep the Python service from Task 5 running. In the VS Code terminal run:

```powershell
npm.cmd run dev
```

In another terminal run:

```powershell
Invoke-RestMethod http://localhost:3000/api/copilotkit/info
```

Expected: the response lists an agent with ID `local_chat`. If it does not, compare the installed runtime's `/info` response with the official v2 Runtime HTTP endpoints documentation before changing any other layer.

- [ ] **Step 4: Commit the Runtime route**

```powershell
git add src\app\api\copilotkit .env.local.example .gitignore package.json package-lock.json
git commit -m "feat: connect runtime to Python chat agent"
```

---

### Task 8: Build the CopilotChat Page and New-Chat Control

**Files:**
- Modify: `src/app/layout.tsx`
- Replace: `src/app/page.tsx`
- Replace: `src/app/globals.css`

**Interfaces:**
- Consumes: Runtime `/api/copilotkit` and agent ID `local_chat`.
- Produces: A responsive full-page chat UI; `startNewThread()` clears visible history and causes the next run to use a new LangGraph thread ID.

- [ ] **Step 1: Replace the page with the CopilotKit provider and chat**

Create `src/app/page.tsx`:

```tsx
"use client";

import { RotateCcw } from "lucide-react";
import {
  CopilotChat,
  CopilotKit,
  useCopilotChatConfiguration,
} from "@copilotkit/react-core/v2";
import "@copilotkit/react-core/v2/styles.css";


function ChatWorkspace() {
  const chatConfiguration = useCopilotChatConfiguration();

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="app-kicker">LangChain + CopilotKit</p>
          <h1>本地对话智能体</h1>
        </div>
        <button
          className="icon-button"
          type="button"
          aria-label="清空对话"
          title="清空对话"
          onClick={() => chatConfiguration?.startNewThread()}
          disabled={!chatConfiguration}
        >
          <RotateCcw aria-hidden="true" size={18} />
        </button>
      </header>

      <main className="chat-region">
        <CopilotChat
          agentId="local_chat"
          className="chat"
          labels={{
            modalHeaderTitle: "本地对话智能体",
            welcomeMessageText: "你好，我可以和你进行多轮对话。",
          }}
        />
      </main>
    </div>
  );
}


export default function Home() {
  return (
    <CopilotKit runtimeUrl="/api/copilotkit" agent="local_chat">
      <ChatWorkspace />
    </CopilotKit>
  );
}
```

- [ ] **Step 2: Set page metadata and language**

Replace `src/app/layout.tsx` with:

```tsx
import type { Metadata } from "next";
import "./globals.css";


export const metadata: Metadata = {
  title: "本地对话智能体",
  description: "基于 LangChain、LangGraph 和 CopilotKit 的本地聊天智能体",
};


export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
```

- [ ] **Step 3: Add a restrained responsive layout**

Replace `src/app/globals.css` with:

```css
:root {
  color-scheme: light;
  --page: #f4f6f8;
  --surface: #ffffff;
  --text: #182026;
  --muted: #5f6b75;
  --border: #d8dee4;
  --accent: #0f766e;
}

* {
  box-sizing: border-box;
}

html,
body {
  margin: 0;
  min-height: 100%;
}

body {
  background: var(--page);
  color: var(--text);
  font-family: Arial, "Microsoft YaHei", sans-serif;
}

button,
textarea,
input {
  font: inherit;
}

.app-shell {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  width: min(1120px, 100%);
  min-height: 100vh;
  margin: 0 auto;
  background: var(--surface);
  border-inline: 1px solid var(--border);
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 72px;
  padding: 12px 20px;
  border-bottom: 1px solid var(--border);
}

.app-header h1,
.app-kicker {
  margin: 0;
  letter-spacing: 0;
}

.app-header h1 {
  margin-top: 3px;
  font-size: 20px;
  line-height: 1.3;
}

.app-kicker {
  color: var(--muted);
  font-size: 12px;
}

.icon-button {
  display: inline-grid;
  place-items: center;
  width: 40px;
  height: 40px;
  padding: 0;
  color: var(--accent);
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 6px;
  cursor: pointer;
}

.icon-button:hover:not(:disabled) {
  background: #edf7f5;
}

.icon-button:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.chat-region,
.chat {
  min-width: 0;
  min-height: 0;
  height: 100%;
}

@media (max-width: 640px) {
  .app-shell {
    border-inline: 0;
  }

  .app-header {
    min-height: 64px;
    padding-inline: 14px;
  }

  .app-header h1 {
    font-size: 18px;
  }
}
```

- [ ] **Step 4: Verify the frontend statically**

```powershell
npm.cmd run lint
npm.cmd run build
```

Expected: both commands pass. CopilotKit's prebuilt component supplies the sending/loading/error states; the custom button only starts a new thread.

- [ ] **Step 5: Verify the page manually on desktop and mobile widths**

With both dev servers running, open `http://localhost:3000` and check:

```text
Desktop 1440x900: header and chat fit without overlap or horizontal scrolling.
Mobile 390x844: title, reset icon, messages, and composer remain visible and usable.
```

- [ ] **Step 6: Commit the chat page**

```powershell
git add src\app\layout.tsx src\app\page.tsx src\app\globals.css
git commit -m "feat: add streaming CopilotKit chat page"
```

---

### Task 9: Complete End-to-End Acceptance and Repository Documentation

**Files:**
- Replace in backend: `README.md`
- Replace in frontend: `README.md`

**Interfaces:**
- Consumes: Completed backend and frontend services.
- Produces: Reproducible setup instructions and evidence for every phase-one acceptance criterion.

- [ ] **Step 1: Run all automated backend checks**

From `backend`:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Expected: configuration, model factory, graph memory, health, CORS, and AG-UI stream tests all pass without real API usage.

- [ ] **Step 2: Run all automated frontend checks**

From `frontend`:

```powershell
npm.cmd run lint
npm.cmd run build
```

Expected: both pass.

- [ ] **Step 3: Perform the real-model conversation acceptance test**

Start the backend in PyCharm and frontend in VS Code, then perform exactly this sequence:

```text
1. Send: 你好，请记住我的名字叫小羽。
2. Confirm the answer appears incrementally rather than all at once.
3. Send: 我的名字是什么？
4. Confirm the answer says 小羽.
5. Click the reset icon.
6. Send: 我的名字是什么？
7. Confirm the new conversation does not know the old name.
```

- [ ] **Step 4: Perform failure and recovery acceptance**

Stop the Python server while keeping the page open. Send a message and confirm CopilotChat ends the loading state and shows a comprehensible run/connection error. Restart Python and confirm a new message succeeds without reloading the entire development environment.

- [ ] **Step 5: Write the backend README**

The backend README must contain these sections with exact commands:

~~~~markdown
# showcon-demo-langchain

Python backend for the phase-one local chat agent.

## Requirements

- Python 3.12
- A company OpenAI-compatible API key, base URL, and model name

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Set the three real company values in `.env`, then start:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Health: `http://127.0.0.1:8000/health`

## Learning Examples

Run the examples in learning order:

```powershell
.\.venv\Scripts\python.exe examples\01_model_call.py
.\.venv\Scripts\python.exe examples\02_stream_chat.py
.\.venv\Scripts\python.exe examples\03_minimal_graph.py
```

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Architecture

See `docs/superpowers/specs/2026-08-05-local-chat-agent-design.md`.
~~~~

- [ ] **Step 6: Write the frontend README**

The frontend README must contain:

~~~~markdown
# showcon-demo-web

Next.js and CopilotKit frontend for the phase-one local chat agent.

## Requirements

- Node.js 20+
- The Python backend running on port 8000

## Setup

```powershell
npm.cmd install
Copy-Item .env.local.example .env.local
npm.cmd run dev
```

Open `http://localhost:3000`.

## Checks

```powershell
npm.cmd run lint
npm.cmd run build
```

## Architecture

The browser calls `/api/copilotkit`; the server-side Runtime forwards `local_chat` runs to the Python AG-UI endpoint configured by `AGENT_URL`. No model API key belongs in this repository.

See the [phase-one design](https://github.com/yutou-ii/showcon-demo-langchain/blob/main/docs/superpowers/specs/2026-08-05-local-chat-agent-design.md) in the backend repository.
~~~~

- [ ] **Step 7: Check both repositories for ignored secrets and IDE files**

Run in each repository:

```powershell
git status --short
git ls-files | rg "(^|/)(\.env|\.idea|\.vscode|\.venv)(/|$)"
```

Expected: `.env`, `.env.local`, `.idea/`, `.vscode/`, and `.venv/` do not appear. Only `.env.example` and `.env.local.example` may be tracked.

- [ ] **Step 8: Commit documentation separately in each repository**

Backend:

```powershell
git add README.md
git commit -m "docs: add backend setup and verification guide"
```

Frontend:

```powershell
git add README.md
git commit -m "docs: add frontend setup and verification guide"
```

- [ ] **Step 9: Record final local status without pushing**

Run in both repositories:

```powershell
git status --short --branch
git log --oneline -8
```

Expected: both worktrees are clean. Review commits and test results with the mentor before pushing either `main` branch.
