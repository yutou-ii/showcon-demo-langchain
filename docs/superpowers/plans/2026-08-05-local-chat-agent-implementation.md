# 本地对话智能体第一阶段实施计划

> **给执行本计划的 Agent：** 必须使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans`，按任务逐项实施。每个步骤使用复选框（`- [ ]`）跟踪进度。

**目标：** 构建一个可在本地运行、支持流式输出和多轮对话的简单智能体。前端使用 CopilotKit/Next.js，后端使用 Python FastAPI/LangChain/LangGraph，并连接公司的 OpenAI 兼容接口。

**架构：** 浏览器中的 `CopilotChat` 调用 Next.js 提供的同源 CopilotKit Runtime 路由。Runtime 注册一个遵循 AG-UI 协议的 `HttpAgent`，把每次对话请求转发给 Python FastAPI；`ag-ui-langgraph` 再把请求适配到只有一个模型节点的 LangGraph。模型由 LangChain 的 `ChatOpenAI` 调用，短期对话记录由内存检查点（in-memory checkpointer）保存。

**技术栈：** Next.js 16.3.0、React、TypeScript、CopilotKit 1.66.2（使用 v2 API）、AG-UI client 0.0.57、Python 3.12、FastAPI、LangChain 1.3.14、LangGraph 1.2.10、langchain-openai 1.4.1、ag-ui-langgraph 0.0.42、pytest。

## 全局约束

- 后端仓库：`D:\code\aiagent\0824_langchain\backend`；在 PyCharm 中开发，并使用解释器 `backend\.venv\Scripts\python.exe`。
- 前端仓库：`D:\code\aiagent\0824_langchain\frontend`；在 VS Code 中开发，使用 Node.js 20+ 和 npm。
- 在 Windows PowerShell 中，如果执行策略阻止运行 `npm.ps1` 或 `npx.ps1`，改用 `npm.cmd` 和 `npx.cmd`。
- 固定脚手架和依赖版本：`create-next-app@16.3.0`、`@copilotkit/react-core@1.66.2`、`@copilotkit/runtime@1.66.2`、`@ag-ui/client@0.0.57`、`lucide-react@1.28.0`；必须提交 `package-lock.json`。
- Python、Next.js Runtime 和 `CopilotChat` 中的 Agent ID 必须完全一致，统一为 `local_chat`。
- Python AG-UI 地址固定为 `http://127.0.0.1:8000/agent`；健康检查地址固定为 `http://127.0.0.1:8000/health`。
- Next.js Runtime 的基础路径为 `/api/copilotkit`；使用 v2 通配路由 `src/app/api/copilotkit/[...path]/route.ts`。
- 模型 API Key 只能保存在 `backend/.env`，严禁写入前端文件或提交到 Git。
- 第一阶段包含：流式输出、进程内多轮上下文、新建对话、加载和错误反馈、`/health`、测试及文档。
- 第一阶段不包含：skills/tools、RAG、数据库、鉴权、历史记录持久化、多智能体流程及生产部署。
- 保留 GitHub 自动生成 README 的初始提交历史；通过普通提交覆盖 README 内容，不得强制推送。

## 新手执行说明

这份计划不是要求你一次写完全部代码，而是按下面的学习顺序逐层增加能力：

1. **任务 1：先确认环境可用。** 官方模板只做冒烟测试，目的是先证明公司模型接口和本机环境能够跑通。
2. **任务 2-3：只学习 LangChain。** 先理解环境变量、`ChatOpenAI`、单轮调用、流式输出和手动维护消息历史。
3. **任务 4：再引入 LangGraph。** 把任务 3 已经理解的模型调用放进一个最小图中，只增加 `thread_id` 和上下文保存能力。
4. **任务 5：把 Python 能力变成 HTTP 服务。** FastAPI 提供服务入口，AG-UI 负责统一前后端之间的 Agent 事件格式。
5. **任务 6-8：接入前端。** 先生成干净的 Next.js 项目，再依次加入 Runtime 代理和 `CopilotChat` 页面。
6. **任务 9：统一验收。** 最后才使用真实模型检查流式输出、多轮记忆、清空会话、错误恢复和文档。

任务 2-5 使用测试驱动开发（TDD）的“红、绿”循环：先写测试并看到它因为功能不存在而失败（红），再写最少实现让测试通过（绿）。这里的首次失败是计划的一部分，不代表操作出错。

每完成一个任务就停下来检查该任务的预期结果并提交 Git。某一步的实际结果与“预期结果”不一致时，不要继续后面的任务；先记录命令、完整报错和当前任务编号，再定位当前这一层的问题。

---

### 任务 1：运行官方模板，完成一次性冒烟测试

**涉及文件：**
- 在 Git 仓库外创建：`D:\code\aiagent\0824_langchain\scratch\official-smoke\`
- 不修改前端和后端两个正式仓库。

**输入与产出：**
- 输入：公司提供的 `OPENAI_API_KEY`、`OPENAI_BASE_URL` 和 `OPENAI_MODEL`。
- 产出：验证 Node、Python、浏览器和公司模型接口能够共同完成一次 CopilotKit 对话。

- [ ] **步骤 1：生成官方模板项目**

在 `D:\code\aiagent\0824_langchain\scratch` 目录运行：

```powershell
npx.cmd copilotkit@latest create
```

按照下面的选项回答脚手架问题：

```text
Project name: official-smoke
Enterprise Intelligence Platform: No
Framework: LangGraph (Python)
Package manager: npm
```

- [ ] **步骤 2：找到模板生成的模型配置**

运行：

```powershell
Set-Location D:\code\aiagent\0824_langchain\scratch\official-smoke
rg -n "create_agent|ChatOpenAI|OPENAI_API_KEY|gpt-" .
```

预期结果：至少找到一个 Python Agent 文件和一个环境变量示例文件。把路径临时记录在 Git 仓库外，因为 CLI 在不同版本中可能生成不同的目录结构。

- [ ] **步骤 3：让临时 Agent 使用公司的模型接口**

在生成的 Python Agent 文件中显式创建模型，并把它传给模板生成的图或 `create_agent` 调用：

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

三个真实值只能写入本地生成的 `.env` 文件。不要把它们粘贴到源码或终端输出中。

- [ ] **步骤 4：启动模板并验证一次回复**

运行：

```powershell
npm.cmd install
npm.cmd run dev
```

预期结果：前端界面和 Agent 服务都成功启动。打开终端打印的本地地址，发送 `你好，请只回复“连接成功”`，确认能够收到回复。

- [ ] **步骤 5：停止服务，只把模板保留为本地参考**

按 `Ctrl+C` 停止服务。不要初始化 Git，也不要把生成的文件复制进正式仓库。如果冒烟测试失败，就暂时停在这里，先判断问题出在 Node、Python、浏览器还是公司模型接口；修复后再开始任务 2。

---

### 任务 2：建立后端依赖和经过校验的配置

**涉及文件：**
- 新建：`requirements.txt`
- 新建：`requirements-dev.txt`
- 新建：`.env.example`
- 新建：`app/__init__.py`
- 新建：`app/config.py`
- 新建：`tests/test_config.py`
- 修改：`.gitignore`

**输入与产出：**
- 输入：环境变量 `OPENAI_API_KEY`、`OPENAI_BASE_URL` 和 `OPENAI_MODEL`。
- 产出：`Settings`、`get_settings() -> Settings`，以及可重复安装的 Python 依赖集合。

- [ ] **步骤 1：声明运行依赖和测试依赖**

新建 `requirements.txt`：

```text
ag-ui-langgraph==0.0.42
fastapi==0.141.1
langchain==1.3.14
langchain-openai==1.4.1
langgraph==1.2.10
pydantic-settings>=2.0,<3.0
uvicorn[standard]==0.52.1
```

新建 `requirements-dev.txt`：

```text
-r requirements.txt
httpx>=0.28,<0.29
pytest>=8.0,<9.0
pytest-asyncio>=0.25,<2.0
```

运行：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

- [ ] **步骤 2：先编写会失败的配置测试**

新建 `tests/test_config.py`：

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

- [ ] **步骤 3：运行测试并确认它按预期失败**

运行：

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_config.py -v
```

预期结果：测试收集阶段失败，原因是 `app.config` 还不存在。这次失败证明测试确实能发现尚未实现的功能。

- [ ] **步骤 4：实现带校验的配置类**

先新建空文件 `app/__init__.py`，再新建 `app/config.py`：

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

新建 `.env.example`：

```dotenv
OPENAI_API_KEY=change-me
OPENAI_BASE_URL=https://company-endpoint.example/v1
OPENAI_MODEL=company-model-name
```

确认 `.gitignore` 包含以下规则：

```gitignore
.env
.env.*
!.env.example
```

- [ ] **步骤 5：运行当前测试和全部后端测试**

运行：

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_config.py -v
.\.venv\Scripts\python.exe -m pytest -q
```

预期结果：全部测试通过。

- [ ] **步骤 6：提交后端基础配置**

```powershell
git add requirements.txt requirements-dev.txt .env.example .gitignore app tests
git commit -m "build: add backend settings and dependencies"
```

---

### 任务 3：添加 LangChain 模型工厂和学习示例

**涉及文件：**
- 新建：`app/model.py`
- 新建：`examples/01_model_call.py`
- 新建：`examples/02_stream_chat.py`
- 新建：`tests/test_model.py`

**输入与产出：**
- 输入：任务 2 创建的 `Settings`。
- 产出：`create_chat_model(settings: Settings | None = None) -> ChatOpenAI`，以及两个可在终端运行的学习程序。

- [ ] **步骤 1：先编写会失败的模型工厂测试**

新建 `tests/test_model.py`：

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

- [ ] **步骤 2：运行测试并确认它按预期失败**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_model.py -v
```

预期结果：测试失败，因为 `app.model` 还不存在。

- [ ] **步骤 3：实现模型工厂**

新建 `app/model.py`：

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

- [ ] **步骤 4：运行测试并确认它通过**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_model.py -v
```

- [ ] **步骤 5：添加单轮模型调用学习示例**

新建 `examples/01_model_call.py`：

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

准备好包含真实配置的本地 `.env` 后运行：

```powershell
.\.venv\Scripts\python.exe examples\01_model_call.py
```

预期结果：终端一次性打印一条完整的模型回答。这个示例先帮助你理解最基础的 `model.invoke()`。

- [ ] **步骤 6：添加流式多轮对话学习示例**

新建 `examples/02_stream_chat.py`：

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

运行：

```powershell
.\.venv\Scripts\python.exe examples\02_stream_chat.py
```

先发送 `记住我的名字叫小羽`，再发送 `我的名字是什么？`。预期结果：文字逐段出现，而且第二次回答能够利用第一轮的内容。这里的 `history` 就是最直观的多轮上下文。

- [ ] **步骤 7：运行全部测试并提交**

```powershell
.\.venv\Scripts\python.exe -m pytest -q
git add app\model.py examples tests\test_model.py
git commit -m "feat: add LangChain model and chat examples"
```

---

### 任务 4：构建最小的有状态 LangGraph

**涉及文件：**
- 新建：`app/agent.py`
- 新建：`examples/03_minimal_graph.py`
- 新建：`tests/test_agent.py`

**输入与产出：**
- 输入：任意 `BaseChatModel`，以及可选的 LangGraph checkpointer（检查点保存器）。
- 产出：`build_chat_graph(model, checkpointer=None) -> CompiledStateGraph`。图中只有一个 `model` 节点，不同 `thread_id` 的对话在当前进程内彼此隔离。

- [ ] **步骤 1：先编写会失败的图记忆测试**

新建 `tests/test_agent.py`：

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

- [ ] **步骤 2：运行测试并确认它按预期失败**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_agent.py -v
```

预期结果：测试失败，因为 `build_chat_graph` 还不存在。

- [ ] **步骤 3：实现只有一个节点的图**

新建 `app/agent.py`：

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

- [ ] **步骤 4：运行图相关测试**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_agent.py -v
```

预期结果：两个测试都通过。第一个测试证明同一 `thread_id` 会保留上下文，第二个测试证明不同 `thread_id` 不会串话。

- [ ] **步骤 5：添加用于学习的图流式输出示例**

新建 `examples/03_minimal_graph.py`：

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

运行该示例，并重复任务 3 中的两轮姓名测试。注意这次消息历史不再由示例代码手动维护，而是交给 LangGraph 的 checkpointer。

- [ ] **步骤 6：运行全部测试并提交**

```powershell
.\.venv\Scripts\python.exe -m pytest -q
git add app\agent.py examples\03_minimal_graph.py tests\test_agent.py
git commit -m "feat: add minimal stateful LangGraph agent"
```

---

### 任务 5：通过 FastAPI 和 AG-UI 暴露 LangGraph 服务

**涉及文件：**
- 新建：`app/main.py`
- 新建：`tests/conftest.py`
- 新建：`tests/test_health.py`
- 新建：`tests/test_ag_ui.py`

**输入与产出：**
- 输入：`build_chat_graph()` 和 `create_chat_model()`。
- 产出：`create_app(model=None) -> FastAPI`、模块级 `app`、`GET /health`、`POST /agent` 和 `GET /agent/health`。

- [ ] **步骤 1：为测试提供不含秘密的环境变量默认值**

新建 `tests/conftest.py`：

```python
import os


os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("OPENAI_BASE_URL", "https://models.example.test/v1")
os.environ.setdefault("OPENAI_MODEL", "test-model")
```

- [ ] **步骤 2：先编写会失败的健康检查和 CORS 测试**

新建 `tests/test_health.py`：

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

- [ ] **步骤 3：编写会失败的 AG-UI 流式响应测试**

新建 `tests/test_ag_ui.py`：

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

- [ ] **步骤 4：运行测试并确认它按预期失败**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_health.py tests\test_ag_ui.py -v
```

预期结果：测试失败，因为 `app.main` 还不存在。

- [ ] **步骤 5：实现 FastAPI 应用**

新建 `app/main.py`：

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

- [ ] **步骤 6：运行当前测试和全部测试**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_health.py tests\test_ag_ui.py -v
.\.venv\Scripts\python.exe -m pytest -q
```

预期结果：所有测试通过，而且不会调用真实模型接口。测试使用 `FakeListChatModel`，因此不会消耗公司接口额度。

- [ ] **步骤 7：在 PyCharm 中启动并检查后端**

在 PyCharm 中创建 Python 运行配置：

```text
Module name: uvicorn
Parameters: app.main:app --host 127.0.0.1 --port 8000 --reload
Working directory: D:\code\aiagent\0824_langchain\backend
Interpreter: D:\code\aiagent\0824_langchain\backend\.venv\Scripts\python.exe
```

确认真实的 `backend/.env` 已存在，启动服务后运行：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/agent/health
```

预期结果：两个地址都返回 `status: ok`；第二个响应还会显示 Agent 名称 `local_chat`。

- [ ] **步骤 8：提交后端服务**

```powershell
git add app\main.py tests\conftest.py tests\test_health.py tests\test_ag_ui.py
git commit -m "feat: expose chat agent over FastAPI and AG-UI"
```

---

### 任务 6：克隆正式前端仓库并生成 Next.js 脚手架

**涉及文件：**
- 克隆得到：`D:\code\aiagent\0824_langchain\frontend\.git`
- 替换：`README.md`
- 由脚手架生成：`package.json`、`package-lock.json`、`tsconfig.json`、`next.config.ts`、`eslint.config.mjs`、`src/app/*`
- 新建：`.env.local.example`
- 修改：`.gitignore`

**输入与产出：**
- 输入：GitHub 仓库 `https://github.com/yutou-ii/showcon-demo-web.git`。
- 产出：一个使用 Next.js App Router 和 TypeScript 的干净前端仓库，并安装 CopilotKit v2 与 AG-UI client 依赖。

- [ ] **步骤 1：克隆已有的前端仓库**

当前本地 `frontend` 目录为空。在 `D:\code\aiagent\0824_langchain` 中运行：

```powershell
git clone https://github.com/yutou-ii/showcon-demo-web.git frontend
Set-Location frontend
git status --short --branch
```

预期结果：本地 `main` 分支跟踪 `origin/main`，仓库中只有 GitHub 自动生成的 README。

- [ ] **步骤 2：通过普通工作区修改覆盖已跟踪的 README**

```powershell
Remove-Item -LiteralPath README.md
npx.cmd create-next-app@16.3.0 . --typescript --eslint --app --src-dir --use-npm --no-tailwind --no-agents-md --import-alias "@/*" --yes
```

预期结果：create-next-app 在检查冲突文件时忽略并保留已有的 `.git` 目录，同时写入新的 README 和应用脚手架。`--no-agents-md` 用于避免生成与项目无关的 Agent 说明。不要运行 `git init`，也不要强制推送。

- [ ] **步骤 3：安装前端 Agent 相关依赖**

```powershell
npm.cmd install @copilotkit/react-core@1.66.2 @copilotkit/runtime@1.66.2 @ag-ui/client@0.0.57 lucide-react@1.28.0
```

必须提交生成的 `package-lock.json`，它记录了项目实际安装的精确依赖版本。

- [ ] **步骤 4：添加服务端 Agent 地址示例**

新建 `.env.local.example`：

```dotenv
AGENT_URL=http://127.0.0.1:8000/agent
```

确认 `.gitignore` 包含：

```gitignore
.env*
!.env.local.example
```

把示例复制为本地使用的 `.env.local`；`.env.local` 必须继续被 Git 忽略。

- [ ] **步骤 5：验证并提交尚未加入业务代码的脚手架**

```powershell
npm.cmd run lint
npm.cmd run build
git add .
git commit -m "build: scaffold CopilotKit frontend"
```

预期结果：在添加 CopilotKit 业务代码之前，代码检查和生产构建都通过。这样后续出现问题时，更容易判断是脚手架问题还是新增代码问题。

---

### 任务 7：添加 CopilotKit v2 Runtime 代理

**涉及文件：**
- 新建：`src/app/api/copilotkit/[...path]/route.ts`
- 使用：`.env.local`

**输入与产出：**
- 输入：`AGENT_URL`；未配置时默认使用 `http://127.0.0.1:8000/agent`。
- 产出：`/api/copilotkit/*` 下的 `GET` 和 `POST` 处理函数，并把 `local_chat` 注册为 AG-UI `HttpAgent`。

- [ ] **步骤 1：创建 Runtime 通配路由**

新建 `src/app/api/copilotkit/[...path]/route.ts`：

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

- [ ] **步骤 2：进行静态检查**

```powershell
npm.cmd run lint
npm.cmd run build
```

预期结果：没有 TypeScript、ESLint 或路由构建错误。

- [ ] **步骤 3：同时运行两个服务，检查 Agent 发现接口**

保持任务 5 的 Python 服务运行，在 VS Code 终端中运行：

```powershell
npm.cmd run dev
```

在另一个终端中运行：

```powershell
Invoke-RestMethod http://localhost:3000/api/copilotkit/info
```

预期结果：响应中列出 ID 为 `local_chat` 的 Agent。如果没有，先对照已安装 Runtime 的 `/info` 响应和官方 v2 Runtime HTTP endpoints 文档，不要急着修改其他层。这个检查专门验证 Next.js Runtime 是否正确注册了 Python Agent。

- [ ] **步骤 4：提交 Runtime 路由**

```powershell
git add src\app\api\copilotkit .env.local.example .gitignore package.json package-lock.json
git commit -m "feat: connect runtime to Python chat agent"
```

---

### 任务 8：构建 CopilotChat 页面和新建对话按钮

**涉及文件：**
- 修改：`src/app/layout.tsx`
- 替换：`src/app/page.tsx`
- 替换：`src/app/globals.css`

**输入与产出：**
- 输入：Runtime 地址 `/api/copilotkit` 和 Agent ID `local_chat`。
- 产出：一个响应式全页面聊天界面；`startNewThread()` 清空当前可见消息，并让下一次请求使用新的 LangGraph `thread_id`。

- [ ] **步骤 1：使用 CopilotKit Provider 和聊天组件替换页面**

创建 `src/app/page.tsx`：

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

- [ ] **步骤 2：设置页面元数据和语言**

把 `src/app/layout.tsx` 替换为：

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

- [ ] **步骤 3：添加简洁的响应式布局**

把 `src/app/globals.css` 替换为：

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

- [ ] **步骤 4：进行前端静态检查**

```powershell
npm.cmd run lint
npm.cmd run build
```

预期结果：两个命令都通过。CopilotKit 的预制组件负责发送中、加载中和错误状态；自定义按钮只负责开始新会话。

- [ ] **步骤 5：在桌面和手机宽度下手动检查页面**

保持前后端开发服务运行，打开 `http://localhost:3000` 并检查：

```text
桌面端 1440x900：页头和聊天区域没有重叠，也没有水平滚动条。
移动端 390x844：标题、重置图标、消息和输入框都保持可见并且可以操作。
```

- [ ] **步骤 6：提交聊天页面**

```powershell
git add src\app\layout.tsx src\app\page.tsx src\app\globals.css
git commit -m "feat: add streaming CopilotKit chat page"
```

---

### 任务 9：完成端到端验收和仓库文档

**涉及文件：**
- 在后端仓库替换：`README.md`
- 在前端仓库替换：`README.md`

**输入与产出：**
- 输入：已经完成的后端服务和前端应用。
- 产出：其他人可以重复执行的安装说明，以及覆盖第一阶段每项验收标准的验证记录。

- [ ] **步骤 1：运行全部后端自动化检查**

在 `backend` 目录运行：

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

预期结果：配置、模型工厂、图记忆、健康检查、CORS 和 AG-UI 流式响应测试全部通过，而且不调用真实模型接口。

- [ ] **步骤 2：运行全部前端自动化检查**

在 `frontend` 目录运行：

```powershell
npm.cmd run lint
npm.cmd run build
```

预期结果：代码检查和生产构建都通过。

- [ ] **步骤 3：使用真实模型完成对话验收**

在 PyCharm 中启动后端，在 VS Code 中启动前端，然后严格按以下顺序操作：

```text
1. 发送：你好，请记住我的名字叫小羽。
2. 确认回答逐段出现，而不是等待结束后一次性显示。
3. 发送：我的名字是什么？
4. 确认回答中包含“小羽”。
5. 单击重置图标。
6. 再次发送：我的名字是什么？
7. 确认新会话不知道旧会话中的名字。
```

- [ ] **步骤 4：完成故障和恢复验收**

保持页面打开，但停止 Python 服务。发送消息，确认 CopilotChat 能结束加载状态，并显示可以理解的运行或连接错误。重新启动 Python，再发送一条消息，确认不必重启整个开发环境就能恢复对话。

- [ ] **步骤 5：编写后端 README**

后端 README 必须包含以下章节和准确命令：

~~~~markdown
# showcon-demo-langchain

第一阶段本地对话智能体的 Python 后端。

## 环境要求

- Python 3.12
- 公司 OpenAI 兼容接口的 API Key、Base URL 和模型名称

## 安装与启动

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

在 `.env` 中填写公司提供的三个真实值，然后启动服务：

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

健康检查：`http://127.0.0.1:8000/health`

## 学习示例

按照学习顺序运行示例：

```powershell
.\.venv\Scripts\python.exe examples\01_model_call.py
.\.venv\Scripts\python.exe examples\02_stream_chat.py
.\.venv\Scripts\python.exe examples\03_minimal_graph.py
```

## 测试

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## 架构

参见 `docs/superpowers/specs/2026-08-05-local-chat-agent-design.md`。
~~~~

- [ ] **步骤 6：编写前端 README**

前端 README 必须包含：

~~~~markdown
# showcon-demo-web

第一阶段本地对话智能体的 Next.js 和 CopilotKit 前端。

## 环境要求

- Node.js 20+
- 已经在 8000 端口运行的 Python 后端

## 安装与启动

```powershell
npm.cmd install
Copy-Item .env.local.example .env.local
npm.cmd run dev
```

打开 `http://localhost:3000`。

## 检查

```powershell
npm.cmd run lint
npm.cmd run build
```

## 架构

浏览器调用 `/api/copilotkit`；服务端 Runtime 把 `local_chat` 的运行请求转发到 `AGENT_URL` 配置的 Python AG-UI 地址。模型 API Key 不应出现在本仓库中。

参见后端仓库中的[第一阶段设计文档](https://github.com/yutou-ii/showcon-demo-langchain/blob/main/docs/superpowers/specs/2026-08-05-local-chat-agent-design.md)。
~~~~

- [ ] **步骤 7：检查两个仓库是否错误跟踪了秘密或 IDE 文件**

分别在两个仓库中运行：

```powershell
git status --short
git ls-files | rg "(^|/)(\.env|\.idea|\.vscode|\.venv)(/|$)"
```

预期结果：输出中不出现 `.env`、`.env.local`、`.idea/`、`.vscode/` 和 `.venv/`。只有 `.env.example` 和 `.env.local.example` 可以被 Git 跟踪。

- [ ] **步骤 8：在两个仓库中分别提交文档**

后端仓库：

```powershell
git add README.md
git commit -m "docs: add backend setup and verification guide"
```

前端仓库：

```powershell
git add README.md
git commit -m "docs: add frontend setup and verification guide"
```

- [ ] **步骤 9：记录最终本地状态，但暂不推送**

分别在两个仓库中运行：

```powershell
git status --short --branch
git log --oneline -8
```

预期结果：两个工作区都干净。先与带教一起检查提交记录和测试结果，再决定是否推送两个仓库的 `main` 分支。
