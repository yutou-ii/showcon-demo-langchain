# 本地对话智能体第一阶段设计

## 1. 目标

在本机搭建一个有网页聊天窗口和 Python 后端服务的简单智能体。用户从 CopilotKit 聊天窗口发送消息，Python 后端通过 LangChain 技术体系调用公司的 OpenAI 兼容模型接口，并把回答以流式方式返回前端。

第一阶段完成后，开发者应当能够独立解释从 React 页面到公司模型接口的完整数据流，并能判断错误发生在前端、AG-UI、FastAPI、LangGraph、LangChain 或模型服务中的哪一层。

## 2. 第一阶段范围

第一阶段包含：

- 本地 CopilotKit 聊天页面。
- Python FastAPI 后端服务。
- 使用 langchain-openai 的 ChatOpenAI 连接公司 OpenAI 兼容接口。
- 使用最小 LangGraph 管理消息状态。
- 使用 AG-UI 连接 CopilotKit 和 LangGraph。
- 流式输出。
- 当前进程内的多轮对话。
- 清空当前对话。
- 前端加载状态和可理解的错误提示。
- 后端 /health 健康检查。
- 自动测试和人工端到端验收。

第一阶段不包含：

- Skills 和工具调用。
- RAG、向量数据库或文件知识库。
- 登录、鉴权和用户系统。
- 数据库及永久聊天记录。
- 多智能体、复杂工作流和人工审批。
- 生产环境部署、监控和计费。

## 3. 仓库和本地目录

前后端使用两个独立 GitHub 仓库：

| 本地目录 | GitHub 仓库 | 职责 |
| --- | --- | --- |
| frontend/ | yutou-ii/showcon-demo-web | React/Next.js、CopilotKit 页面和前端测试 |
| backend/ | yutou-ii/showcon-demo-langchain | LangChain/LangGraph、FastAPI、AG-UI、后端测试和共享设计文档 |
| scratch/ | 不提交 | CopilotKit 官方模板，仅用于冒烟验证和对照 |

共享架构与实施文档存放在后端仓库的 docs/ 目录。前端 README 只记录前端安装、配置和启动方式，并链接到后端仓库的共享文档。

两个远端仓库由 GitHub 初始化产生的 README 提交保留在历史中。正式 README 通过普通提交覆盖文件内容，不重写历史，不强制推送。

## 4. 开发环境

### 后端

- IDE：PyCharm。
- Python：3.12。
- 虚拟环境：backend/.venv。
- 当前已检测到 LangChain 1.3.14、LangGraph 1.2.10、langchain-openai 1.4.1、FastAPI 0.141.1 和 ag-ui-langgraph 0.0.42。CopilotKit Python SDK 0.1.94 也已安装，但第一阶段纯聊天不依赖其中的工具中间件。
- PyCharm 打开 backend 目录，并使用 backend/.venv/Scripts/python.exe 作为项目解释器。

### 前端

- IDE：VS Code。
- Node.js：20 或更高；当前环境为 Node.js 24.15.0。
- 包管理器：npm；当前环境为 npm 11.12.1。
- 首次搭建锁定 create-next-app 16.3.0、CopilotKit 1.66.2、AG-UI client 0.0.57 和 lucide-react 1.28.0，并提交 package-lock.json。
- VS Code 打开 frontend 目录。
- Windows PowerShell 禁止运行 npm.ps1 时使用 npm.cmd。

.idea/、个人 .vscode/ 配置、虚拟环境、密钥和构建产物不提交到 Git。

## 5. 技术选择

### 前端

使用 Next.js、React、TypeScript 和 CopilotKit。Next.js 是 React 应用框架，页面和组件仍使用 React。选择它是因为 CopilotKit 官方模板和 LangGraph FastAPI 文档以该路径为主，能减少初次接入中的非业务配置。

### 后端

使用 FastAPI、LangChain、LangGraph 和 langchain-openai：

- FastAPI 负责 HTTP 服务、CORS、健康检查和智能体端点。
- LangChain 负责消息类型、模型客户端和流式模型调用。
- LangGraph 只使用消息状态、一个模型节点和内存检查点，不引入复杂图流程。
- ChatOpenAI 通过自定义 base_url、api_key 和 model 连接公司的兼容接口。

### 前后端通信

使用 AG-UI。AG-UI 是 CopilotKit 前端和智能体后端之间的事件协议，不负责模型推理。Python 侧直接使用 ag-ui-langgraph 的 `LangGraphAgent` 和 FastAPI 端点集成，将 LangGraph 的执行和流式输出转换为 CopilotKit 可识别的运行、文本、完成和错误事件。

前端页面不直接调用模型，也不保存模型密钥。页面先请求同一个 Next.js 应用内的 CopilotKit Runtime 路由，再由该路由连接 Python 智能体端点。这个中间路由是带教所给 `page.tsx` 示例中 `runtimeUrl` 指向但未展示的连接代码。

## 6. 带教参考示例的使用边界

参考页面：[CopilotKit Agentic Chat（LangGraph + FastAPI）](https://feature-viewer.copilotkit.ai/langgraph-fastapi/feature/agentic_chat?file=page.tsx)。该页面是功能片段查看器，只展示核心的 `page.tsx` 和 `agent.py`，没有展示完整项目目录、Next.js Runtime 路由、FastAPI 挂载代码和环境变量配置，因此用于对照关键 API，不作为可以整段复制运行的完整模板。

| 示例内容 | 第一阶段处理 | 原因 |
| --- | --- | --- |
| `CopilotKit`、`runtimeUrl` 和智能体名称 | 保留 | 建立页面到 CopilotKit Runtime 的连接 |
| `CopilotChat` | 保留 | 提供现成聊天窗口和流式消息展示 |
| Python `create_agent` / LangGraph 图 | 学完 LangChain 基础后再接入 | 它属于 LangChain 新版智能体 API，底层使用 LangGraph |
| `MemorySaver` 或等价内存检查点 | 保留 | 支持当前进程内的多轮上下文 |
| `CopilotKitState`、`CopilotKitMiddleware` | 第一阶段不使用，第二阶段按工具需求引入 | 示例使用它们是为了让前端工具被智能体发现；纯聊天使用标准 `MessagesState` 即可 |
| `useFrontendTool` 改变背景 | 第二阶段再做 | 这是前端工具调用，不属于第一阶段纯聊天 |
| `useRenderTool` 天气卡片 | 第二阶段再做 | 这是工具结果的自定义 UI |
| `useAgentContext`、`useConfigureSuggestions`、Zod 工具参数 | 第二阶段再做 | 属于工具上下文、建议问题和参数校验能力 |

第一阶段不会直接从 `create_agent` 起步。学习顺序仍然是：先用 `ChatOpenAI` 理解 LangChain 单轮调用和流式多轮消息，再把相同模型调用包装成最小 LangGraph，最后接入 CopilotKit。官方示例作为每个里程碑完成后的对照答案，而不是起点。

## 7. 总体架构

~~~text
浏览器 localhost:3000
Next.js / React / CopilotChat
          |
          | /api/copilotkit
          v
Next.js CopilotKit Runtime / HttpAgent
          |
          | 连接远程智能体
          v
Python localhost:8000
FastAPI / ag-ui-langgraph / AG-UI
          |
          v
LangGraph MessagesState
          |
          v
LangChain ChatOpenAI
          |
          | HTTPS
          v
公司 OpenAI 兼容模型接口
~~~

一次对话的数据流：

1. 用户在 CopilotKit 聊天框输入消息。
2. `CopilotChat` 向 Next.js 的 CopilotKit Runtime 路由发送带有会话标识和消息的运行请求。
3. CopilotKit Runtime 根据智能体名称，通过 `HttpAgent` 把请求转发到 Python FastAPI 的 AG-UI 端点。
4. Python 端点通过 AG-UI 适配器把请求交给 LangGraph。
5. LangGraph 从 MessagesState 读取当前消息并调用 LangChain 模型客户端。
6. 公司模型接口返回流式文本。
7. Python 后端将文本转换为 AG-UI 增量事件并沿原链路返回。
8. `CopilotChat` 边接收边更新助手消息，运行结束事件关闭当前加载状态。

## 8. 组件边界

### 后端正式代码

~~~text
backend/
├─ app/
│  ├─ main.py
│  ├─ config.py
│  ├─ model.py
│  └─ agent.py
├─ examples/
│  ├─ 01_model_call.py
│  ├─ 02_stream_chat.py
│  └─ 03_minimal_graph.py
├─ tests/
│  ├─ conftest.py
│  ├─ test_config.py
│  ├─ test_model.py
│  ├─ test_agent.py
│  ├─ test_health.py
│  └─ test_ag_ui.py
├─ docs/
├─ requirements.txt
├─ .env.example
├─ .gitignore
└─ README.md
~~~

- config.py：读取并校验 OPENAI_API_KEY、OPENAI_BASE_URL 和 OPENAI_MODEL。
- model.py：根据配置创建 ChatOpenAI，不处理 HTTP 或图状态。
- agent.py：定义 MessagesState、模型节点、内存检查点和已编译图。
- main.py：创建 FastAPI 应用、限制本地 CORS、提供 /health 和 AG-UI 端点。
- examples/：按顺序学习模型调用、流式对话和最小图，不被正式服务导入。
- tests/：使用假模型测试配置、健康检查和会话隔离，避免自动测试消耗真实模型额度。

### 前端正式代码

~~~text
frontend/
├─ src/
│  └─ app/
│     ├─ api/
│     │  └─ copilotkit/
│     │     └─ [...path]/
│     │        └─ route.ts
│     ├─ layout.tsx
│     ├─ page.tsx
│     └─ globals.css
├─ public/
├─ .env.local.example
├─ .gitignore
├─ package.json
└─ README.md
~~~

- `[...path]/route.ts`：使用 v2 多路由处理器创建 CopilotKit Runtime，并通过 `HttpAgent` 把已命名智能体连接到 Python FastAPI 端点。
- layout.tsx：提供 Next.js 页面外壳并加载全局样式。
- page.tsx：作为客户端组件提供 `CopilotKit` 上下文，展示 `CopilotChat`，并配置 Runtime 地址、智能体名称和清空交互。
- globals.css：负责页面布局及 CopilotKit 组件样式。
- .env.local.example：说明本地 Python 智能体地址，不包含密钥。

## 9. 学习和实施顺序

### 里程碑 0：官方模板冒烟验证

在 scratch/ 中运行 CopilotKit 官方 CLI 模板，并对照带教提供的 Agentic Chat 页面。只确认页面、服务、网络和公司模型接口可以连通，不要求理解模板中的 LangGraph 和前端工具代码。

通过条件：模板聊天页面能够收到公司模型回答。

### 里程碑 1：LangChain 单轮调用

手写 ChatOpenAI.invoke()，理解兼容接口配置和消息输入输出。

通过条件：终端能够打印一条完整回答，真实密钥只存在于 .env。

### 里程碑 2：LangChain 流式多轮对话

使用 System、Human 和 AI 消息维护历史，并用 stream() 输出增量文本。

通过条件：终端逐段显示回答，并能正确回答关于上一轮内容的问题。

### 里程碑 3：最小 LangGraph

把已经理解的 LangChain 调用包装成一个模型节点，使用 MessagesState 和内存检查点，以 thread_id 区分会话。

通过条件：同一 thread_id 保留上下文，不同 thread_id 相互隔离。

### 里程碑 4：FastAPI 和 AG-UI

提供健康检查、CORS，并使用 ag-ui-langgraph 将 LangGraph 暴露为 AG-UI 智能体端点。

通过条件：/health 返回成功，智能体端点产生正确的 AG-UI 流式事件。

### 里程碑 5：CopilotKit 前端

手动创建 Next.js/CopilotKit 页面和 CopilotKit Runtime 路由，再连接 Python 后端。

通过条件：可以发送消息、流式显示回答、清空会话并显示错误。

### 里程碑 6：联调和交付

运行自动测试和人工验收，对照官方模板检查关键配置，并完成两个仓库的正式 README。

通过条件：所有验收用例通过，开发者能独立向带教讲清完整请求链路。

上一里程碑没有通过时，不同时修改下一层。

## 10. 会话状态

第一阶段只提供进程内记忆：

- LangGraph 内存检查点使用 thread_id 隔离会话。
- 浏览器当前聊天会话复用同一个 thread_id。
- 清空对话时，前端开始一个新的会话标识。
- 后端重启后历史消失，这是第一阶段的预期行为。
- 不使用数据库，不承诺跨设备或跨进程恢复。

## 11. 配置与安全

后端真实 .env 包含：

~~~dotenv
OPENAI_API_KEY=replace-with-company-key
OPENAI_BASE_URL=https://company-endpoint.example/v1
OPENAI_MODEL=company-model-name
~~~

约束：

- .env 永远不提交；只提交 .env.example。
- 前端不持有模型 API Key。
- 日志和错误响应不得输出 API Key 或完整鉴权头。
- CORS 在开发阶段只允许 http://localhost:3000。
- 缺少必需配置时后端启动应快速失败，并明确指出缺少的变量名。
- /health 只表示 Web 服务存活，不调用模型，也不消耗额度。

## 12. 错误处理

- 配置错误：启动时给出明确的缺失变量提示。
- 模型接口错误：转换为可理解的智能体运行错误，不向前端暴露密钥或底层鉴权信息。
- 超时：结束当前运行并允许用户重新发送，不让页面永久停留在加载状态。
- 前端连接失败：提示确认 Python 服务地址和 /health。
- 流式响应中断：保留已显示文本，同时明确标记回答未完成。

## 13. 测试与验收

### 自动测试

- 配置完整时能够创建设置对象。
- 缺少每一个必需环境变量时产生明确错误。
- /health 返回 HTTP 200 和稳定 JSON。
- 假模型输入消息后，图返回助手消息。
- 相同 thread_id 保留上下文。
- 不同 thread_id 不共享上下文。
- CopilotKit Runtime 能发现并连接配置的 Python 智能体。
- 前端构建和静态检查通过。

### 人工端到端验收

1. 分别在 PyCharm 和 VS Code 启动后端与前端。
2. 打开聊天页面并发送“你好，请记住我的名字叫小羽”。
3. 等待流式回答完成。
4. 发送“我的名字是什么”，确认多轮上下文正确。
5. 清空对话后再次询问名字，确认新会话不继承旧历史。
6. 停止后端，确认前端显示连接错误且页面没有卡死。
7. 恢复后端，确认可以重新发送消息。
8. 检查 Git 状态，确认 .env、.idea/、.vscode/ 和 .venv/ 未被跟踪。

## 14. 第二阶段扩展边界

第二阶段在 LangGraph 中增加 skill 或工具执行节点，而不是改写前端通信链路。AG-UI 可继续承载工具调用开始、参数、结果、失败和完成事件；CopilotKit 可以为这些事件增加过程展示。

第二阶段设计必须另外明确：

- skill 的发现与注册。
- 输入参数校验。
- 文件和命令执行权限。
- 超时、取消和失败恢复。
- 工具结果的前端展示。
- 日志、审计和敏感信息处理。

带教示例中的 `useFrontendTool`、`useRenderTool`、`useAgentContext`、`useConfigureSuggestions` 和 Zod 参数结构可以作为第二阶段的直接参考；第二阶段仍需先定义具体 skill 契约，再决定哪些结果只显示文本、哪些结果使用自定义卡片。

这些内容不提前放入第一阶段代码。
