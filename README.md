# showcon-demo-langchain

第一阶段本地对话智能体的 Python 后端服务。

本项目使用 FastAPI 提供 HTTP 服务，使用 LangChain 调用公司提供的 OpenAI 兼容模型接口，使用 LangGraph 保存进程内多轮对话上下文，并通过 AG-UI 协议暴露给 CopilotKit 前端调用。

## 环境要求

- Python 3.12
- 公司提供的 OpenAI 兼容接口配置：
  - `OPENAI_API_KEY`
  - `OPENAI_BASE_URL`
  - `OPENAI_MODEL`

## 安装依赖

需要先安装 [uv](https://docs.astral.sh/uv/)。在本仓库根目录执行：

```powershell
uv sync
```

uv 会自动创建 `.venv` 虚拟环境并安装全部依赖（含开发依赖）。后续依赖变更后再次执行 `uv sync` 即可同步。

## 配置环境变量

复制示例环境变量文件：

```powershell
Copy-Item .env.example .env
```

然后在 `.env` 中填写公司提供的真实配置：

```dotenv
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://your-company-openai-compatible-endpoint/v1
OPENAI_MODEL=your-model-name
```

注意：`.env` 只保存在本地，不要提交到 GitHub。

## 启动服务

在终端运行：

```powershell
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

启动后检查：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/agent/health
```

预期返回服务状态正常，并能看到 Agent 名称 `local_chat`。

## 学习示例

按顺序运行：

```powershell
uv run examples\01_model_call.py
uv run examples\02_stream_chat.py
uv run examples\03_minimal_graph.py
```

三个示例分别用于理解：

- `01_model_call.py`：最基础的一次性模型调用
- `02_stream_chat.py`：流式输出和手动维护多轮消息历史
- `03_minimal_graph.py`：把模型调用放进最小 LangGraph，并按线程保存上下文

## 测试

运行全部后端测试：

```powershell
uv run -m pytest -q
```

这些测试使用假模型或本地配置校验，不会消耗公司模型接口额度。

## 接口说明

- `GET /health`：后端服务健康检查
- `GET /agent/health`：AG-UI Agent 健康检查
- `POST /agent`：AG-UI 协议入口，由 CopilotKit Runtime 调用

## 架构说明

浏览器中的 CopilotKit 前端不会直接访问模型接口，而是通过前端 Runtime 转发到本后端服务：

```text
CopilotChat
→ Next.js /api/copilotkit
→ FastAPI /agent
→ LangGraph
→ LangChain ChatOpenAI
→ 公司 OpenAI 兼容模型接口
```

模型密钥只应该出现在后端 `.env` 文件中，不能写入前端代码，也不能提交到 GitHub。
