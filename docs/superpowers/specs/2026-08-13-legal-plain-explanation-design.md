# 合同条款通俗解释功能设计

## 1. 目标

在第一阶段本地对话智能体基础上，增加“一次对话上传并处理一份 Word 合同”的能力。用户上传一份虚构或脱敏的 `.docx` 合同后，可以继续在原有 CopilotKit 对话窗口中询问某个条款或法律术语的含义；Agent 必须先从当前合同中定位原文，再按照公司 `legal-plain-explanation` Skill 的规则输出“原文 → 白话解释 → 实际案例”，并保留法律服务边界声明。

本阶段既要跑通后端工具调用，也要实现一个最小、可复用、可测试的 Skill 发现与按需加载机制。现有 CopilotKit、AG-UI、FastAPI 和 LangGraph 通信链路继续沿用，不改写第一阶段已经跑通的基础架构。

## 2. 用户可见结果

完整演示路径如下：

1. 用户在现有聊天页面选择并上传一份 `.docx` 合同。
2. 页面显示文件名、解析状态和识别到的条款数量。
3. 当前对话记住上传接口返回的 `document_id`；同一对话再次上传时，新文件替换旧文件。
4. 用户询问：“第八条中的连带责任是什么意思？”
5. Agent 先获得当前合同目录，再按条款编号或关键词定位相关原文。
6. Agent 按需加载 `legal-plain-explanation/SKILL.md` 和合同领域参考文件 `references/contract-terms.md`。
7. Agent 严格输出原文、白话解释、3 至 5 句虚构生活案例，以及统一的非法律建议声明。
8. 如果找不到条款、文件已经失效或问题越过能力边界，页面显示明确的可恢复提示，而不是编造内容。

## 3. 第一版范围

### 3.1 包含

- 每个对话同时只关联一份 `.docx` 合同。
- 仅使用虚构、脱敏且获准用于模型测试的合同。
- 浏览器上传、后端大小与类型校验、Word 结构化解析。
- 本地临时文档存储和不透明 `document_id`。
- 合同目录查询工具和条款定位工具。
- LangGraph 的 `model → tools → model` 条件循环。
- 公司法律条款通俗解释 Skill 的发现、加载和合同领域参考资料按需加载。
- 原文可追溯、边界声明、工具失败和上传失败处理。
- 后端单元测试、接口测试和前端 lint/build 验证。

### 3.2 不包含

- `.doc`、PDF、扫描图片和 OCR。
- 同一对话多份合同、跨合同检索和版本对比。
- 合同预审、深度审查、合规结论和签署建议。
- 数据库、对象存储、向量数据库和 RAG。
- 真实 CLM 服务、MCP、Deep Agents 和多 Agent。
- 用户账号、权限系统和文件永久保存。
- 第一版自定义工具卡片；CopilotKit 默认工具过程展示与文本回答足够完成验收。

## 4. 端到端架构

```text
浏览器选择 .docx
    ↓ multipart/form-data
Next.js 上传代理路由
    ↓
FastAPI /documents
    ↓ 校验、解析、临时保存
DocumentStore ───────────────→ document_id
    ↑                              ↓
    │                         useAgentContext
    │                              ↓
用户问题 → CopilotKit Runtime → AG-UI /agent
                                    ↓
                              LangGraph model
                                    ↓ tool call
                         get_document_outline / find_contract_clause
                                    ↓
                           ToolNode 执行并返回证据
                                    ↓
                              LangGraph model
                                    ↓
          legal-plain-explanation Skill + contract-terms 约束回答
                                    ↓
                         AG-UI 流式事件 → CopilotKit
```

前端不直接访问后端文件系统，也不把合同全文保存在浏览器或聊天消息中。上传接口只把 `document_id` 和无敏感内容的摘要返回给前端。每次用户发起聊天时，前端通过 CopilotKit v2 的 `useAgentContext` 注册当前文档信息；AG-UI 将该上下文放入 Agent 运行状态，工具从运行上下文获得当前 `document_id`。

## 5. 组件与职责

### 5.1 Word 解析器

后端新增独立解析模块，只负责把 `.docx` 转成项目内部的数据结构，不负责存储、模型调用或法律解释。

输入：本地 `.docx` 路径或字节流。

输出至少包括：

- 原始文件名。
- 合同标题（能够识别时）。
- 按原始顺序保存的段落和表格文本。
- 识别出的条款编号、条款标题和正文。
- 解析警告，例如“未识别出显式条款标题”。

条款识别采用可解释的规则作为第一版：匹配“第一条”“第 8 条”“一、付款方式”等常见标题形式，并把后续内容归入该条款，直到出现下一个标题。无法识别条款标题时，仍保留按段落组织的全文，允许关键词定位；不得因为格式不标准而静默丢失内容。

### 5.2 临时文档存储

后端新增 `DocumentStore` 抽象及内存实现。它负责：

- 生成随机、不可从文件名推断的 `document_id`。
- 保存解析后的合同对象，而不是把全文交给前端。
- 根据 `document_id` 读取合同。
- 同一会话上传新文件时允许前端切换到新 `document_id`。
- 服务重启后数据可以丢失；第一版明确这是本地临时能力。

上传文件目录与本地测试合同目录必须加入 `.gitignore`。错误日志不得打印合同全文、API Key 或完整文件路径。

### 5.3 上传接口

FastAPI 新增 `POST /documents`，请求使用 `multipart/form-data`，字段名为 `file`。

第一版校验规则：

- 扩展名必须为 `.docx`。
- 文件大小上限设为 10 MiB。
- 空文件拒绝处理。
- 无法被 `python-docx` 打开的文件返回 `422`。
- 成功返回 `201`。

成功响应不包含合同正文，只返回：

```json
{
  "document_id": "8c03e47b-...",
  "filename": "示例采购合同.docx",
  "section_count": 12,
  "table_count": 2,
  "warnings": []
}
```

Next.js 增加同源上传代理路由，浏览器请求 `/api/documents`，由该路由转发至 FastAPI。这样浏览器仍只连接 `localhost:3000`，后端地址继续由服务端环境变量管理。

### 5.4 当前合同上下文

前端上传成功后保存当前文档摘要，并使用 `useAgentContext` 注册 JSON 值：

```json
{
  "document_id": "8c03e47b-...",
  "filename": "示例采购合同.docx"
}
```

上下文描述固定为“当前对话中用户已上传的合同”。聊天组件在没有上传合同的情况下仍可普通对话；当用户要求解释“这份合同里的条款”但上下文没有 `document_id` 时，Agent 应提示先上传合同。

用户点击“清空对话”时，同时清除前端当前合同状态，避免新对话意外引用旧合同。第一版不要求后端立即删除旧对象；它只是不再可被当前对话引用。后续可以增加 TTL 清理。

### 5.5 合同工具

第一版只暴露两个只读工具，保持能力边界小而清楚。

#### `get_document_outline`

用途：当用户按条款编号询问或问题较模糊时，向 Agent 返回当前合同的标题和条款目录。

输入：无显式 `document_id` 参数给模型；工具从可信运行上下文读取当前文档编号，避免模型编造或覆盖文档编号。

输出：文件名、条款编号、标题和稳定的 `section_id`，不返回整份合同正文。

#### `find_contract_clause`

用途：根据用户的条款编号、标题或关键词定位原文。

输入：模型提供 `query`；工具从可信运行上下文读取 `document_id`。

输出：按相关度排序的少量匹配项，每项包括 `section_id`、条款编号、标题、原文和匹配依据。默认最多返回 3 项，单项原文保留完整条款但设置安全长度上限，防止一次把整份合同送入模型。

定位顺序：

1. 精确条款编号。
2. 精确或包含式标题匹配。
3. 关键词匹配。
4. 无可靠匹配时返回“未找到”，不得让模型凭常识补写合同原文。

工具错误使用结构化错误码区分：`missing_document`、`document_not_found`、`clause_not_found` 和 `document_parse_error`。错误信息面向用户可恢复，且不泄露合同内容。

### 5.6 LangGraph 工具循环

现有图是 `START → model → END`。第二阶段改为：

```text
START → model
           ├─ 没有 tool_calls → END
           └─ 有 tool_calls → tools → model
```

模型通过 `bind_tools` 获得两个工具的名称、说明和参数结构。`ToolNode` 负责真正执行 Python 工具，条件边只检查模型响应中是否存在工具请求。

必须保留现有 `MemorySaver` 和 `thread_id` 多轮上下文。增加最大工具循环次数或递归上限，避免模型反复调用同一工具。工具只读，不允许修改合同、发送消息或产生法律决定，因此第一版不需要人工审批节点。

### 5.7 Skill 目录、发现与加载

后端仓库增加：

```text
skills/
└── legal-plain-explanation/
    ├── SKILL.md
    └── references/
        ├── contract-terms.md
        ├── civil-terms.md
        ├── corporate-terms.md
        └── labor-terms.md
```

公司 Skill 文件作为业务规则来源复制到项目中，提交前需得到公司允许；如果公司不允许复制，则使用环境变量配置只读外部 Skill 根目录，仓库只保留接口和示例 Skill。不得擅自改变公司 Skill 的能力边界。

`SkillRegistry` 负责：

- 扫描一级 Skill 目录。
- 解析 `SKILL.md` 的 YAML frontmatter，读取 `name` 和 `description`。
- 按名称获取 Skill 正文。
- 安全解析 Skill 内声明的相对 reference 路径，禁止 `..` 越出 Skill 根目录。
- 缓存不含用户合同内容的静态 Skill 文本。

Agent 启动时只把全部已登记 Skill 的 `name` 和 `description` 组成简短目录放入系统提示，让模型粗略知道“有哪些技能可以使用”，但不预先加载所有 Skill 正文。用户问题命中某个技能时，模型调用受限工具 `read_skill_file(skill_name, relative_path)`：先读取该 Skill 的 `SKILL.md`，再依据其中的按需加载规则读取必要 reference。合同条款问题只读取 `references/contract-terms.md`，其他三个领域资料不自动读取。

`read_skill_file` 不是通用电脑文件读取工具。它只能接受 Registry 已登记的 `skill_name`，并且只能读取该 Skill 根目录内的 `SKILL.md` 或 `references/` 文件；绝对路径、`..` 路径穿越、未登记 Skill 和目录外文件全部拒绝。工具读取到的 Skill 内容作为 `ToolMessage` 回到模型上下文，由模型依照规则继续执行。这既符合带教提出的渐进式 Skill 加载方式，也避免模型读取任意本地文件。

### 5.8 模型提示组合

模型节点根据本轮状态组合三类指令：

1. 基础助手指令：说明可以普通对话，也可以对当前合同执行只读查询，并附已登记 Skill 的名称和描述目录。
2. 工具使用指令：涉及上传合同中的具体条款时，必须先调用工具取得原文；没有证据不得解释为合同原文。
3. Skill 使用指令：命中技能时先调用 `read_skill_file` 读取 `SKILL.md`，再按该文件的说明按需读取 reference；不得跳过 Skill 直接凭模型常识生成受约束的业务回答。

最终回答必须遵循公司 Skill：

- 严格使用“原文 → 白话解释 → 实际案例”三段式。
- 原文只能来自工具返回内容，并尽可能附条款编号或标题。
- 解释中避免产生新的法律术语。
- 案例为 3 至 5 句的中性生活或商业虚构场景。
- 不提供“该不该签、能不能告、怎样规避责任”等行动建议。
- 统一附“以上是通俗解释，具体法律问题请咨询执业律师。”
- 单次待解释文本超过 2000 字时，只处理前 500 字以内核心内容，并明确提示可以继续。

### 5.9 前端交互

现有页面保持单屏聊天布局，在聊天区域上方增加小型合同区：

- 未上传：显示“上传 Word 合同”，仅允许 `.docx`。
- 上传中：按钮禁用并显示解析状态。
- 成功：显示文件名、条款数和“更换合同”。
- 失败：显示明确错误，允许重新选择文件。
- 清空对话：同时清除当前合同显示和 Agent Context。

第一版不把上传文件加入聊天附件，也不依赖模型原生附件能力。上传是独立、可测试的 HTTP 流程，聊天只传 `document_id` 上下文。

## 6. 数据流

### 6.1 上传阶段

1. 浏览器校验扩展名并将文件发送至 Next.js `/api/documents`。
2. Next.js 将 multipart 请求转发至 FastAPI `POST /documents`。
3. FastAPI 校验大小和格式，调用 Word 解析器。
4. 解析器产出结构化合同；DocumentStore 生成 `document_id` 并保存。
5. 前端收到摘要，更新页面状态并注册 Agent Context。

### 6.2 解释阶段

1. 用户在原聊天框提问。
2. CopilotKit 将消息和当前合同 Context 发送至 AG-UI。
3. Agent 判断问题涉及当前合同条款，发起目录或定位工具调用。
4. 工具从运行上下文读取 `document_id`，从 DocumentStore 读取合同并返回原文证据。
5. 模型根据预加载的 Skill 目录识别法律通俗解释能力，通过 `read_skill_file` 先读取完整 Skill，再按其中规则读取合同参考资料。
6. 模型依据证据和 Skill 输出三段式回答。
7. AG-UI 将工具事件和文本事件流式传给 CopilotKit。

## 7. 错误与降级行为

| 场景 | 用户结果 |
| --- | --- |
| 未上传合同却询问“这份合同” | 提示先上传一份 `.docx`，不调用条款工具 |
| 文件不是 `.docx` | 上传区提示仅支持 Word `.docx` |
| 文件超过 10 MiB | 上传区提示大小上限，不进入解析 |
| Word 损坏或加密 | 返回无法解析提示，不创建 `document_id` |
| 未识别出规范条款标题 | 保留段落并允许关键词查找，同时显示解析警告 |
| 找不到用户所说条款 | 说明未在当前合同中找到，提示提供条款编号、标题或关键词 |
| 用户问题可能对应多个条款 | 返回最多 3 个候选并请用户确认，不擅自选择 |
| 用户要求法律建议 | 按公司 Skill 说明能力边界，只解释相关术语 |
| 模型接口失败 | 保留上传状态，显示可重试错误，不要求重新上传 |
| 后端重启导致文档失效 | 提示临时文件已失效，请重新上传 |

## 8. 测试策略

### 8.1 后端单元测试

- `.docx` 段落、标题和表格解析。
- 无显式标题合同的降级解析。
- DocumentStore 保存、读取和不存在错误。
- `get_document_outline` 不返回正文。
- `find_contract_clause` 的编号、标题、关键词和无匹配路径。
- 工具只能从运行上下文取得文档编号。
- Skill frontmatter 解析、名称发现、路径安全和缓存。
- 合同任务只加载 `contract-terms.md`，不加载其他领域文件。

测试合同由测试代码在内存中生成，或使用完全虚构、明确可提交的小型 fixture；不使用真实或脱敏业务合同作为自动化测试素材。

### 8.2 后端集成测试

- `POST /documents` 成功、类型错误、过大、空文件和损坏文件。
- 带伪造模型响应的 `model → tools → model` 循环。
- 无 `document_id`、文档失效和条款不存在时的 Agent 行为。
- `/agent` 继续输出 `RUN_STARTED`、工具事件、文本事件和 `RUN_FINISHED`。
- 第一阶段的多轮对话和 `/health` 测试保持通过。

### 8.3 前端验证

- 上传控件的未上传、上传中、成功和失败状态。
- 上传成功后 Agent Context 包含正确 `document_id`。
- 更换合同时替换 Context。
- 清空对话时同时清除当前合同。
- `npm.cmd run lint` 和 `npm.cmd run build` 通过。

### 8.4 手工验收

至少准备一份虚构采购合同，覆盖以下场景：

1. 按条款编号解释。
2. 按术语解释，例如“连带责任”。
3. 找不到条款。
4. 用户询问“我该不该签”，验证拒绝给法律建议但仍解释术语。
5. 普通聊天不触发合同工具。
6. 后端重启后旧文档提示重新上传。

## 9. 安全与隐私

- 开发和演示只使用虚构或脱敏且获准处理的 `.docx`。
- `.env`、上传目录、测试合同目录和 IDE 本地状态不得提交 Git。
- 前端不保存合同全文，接口响应不回传全文。
- 模型只接收解决当前问题所需的少量条款，不接收整份合同。
- 日志不记录合同正文、密钥、签章、身份证号、银行账号或完整文件路径。
- `document_id` 使用随机标识，不能由用户输入任意服务器路径。
- Skill reference 读取限制在登记的 Skill 目录中。
- 回答不构成法律建议，不评价合同效力，不代替律师。

## 10. 文件职责规划

后端预计新增或修改：

```text
app/
├── agent.py                 # 把单模型图升级为工具循环并组合 Skill 指令
├── main.py                  # 注册上传接口并注入 DocumentStore
├── documents/
│   ├── models.py            # ParsedDocument、ContractSection 等数据结构
│   ├── parser.py            # .docx 结构化解析
│   ├── store.py             # DocumentStore 接口及内存实现
│   └── router.py            # POST /documents
├── skills/
│   ├── models.py            # SkillMetadata、LoadedSkill
│   └── registry.py          # Skill 发现、加载、reference 路径限制和缓存
└── tools/
    └── contract.py          # 合同目录和条款定位工具

skills/
└── legal-plain-explanation/ # 经授权复制的公司 Skill 及 references

tests/
├── test_document_parser.py
├── test_document_store.py
├── test_documents_api.py
├── test_contract_tools.py
├── test_skill_registry.py
├── test_agent_tools.py
└── fixtures/                # 仅放虚构且明确可提交的极小测试材料
```

前端预计新增或修改：

```text
src/app/
├── page.tsx                         # 当前合同状态、上传区和 Agent Context
├── page.module.css                  # 上传区样式（若继续使用模块样式）
└── api/documents/route.ts           # 同源上传代理
```

实施时可以在不改变职责边界的前提下调整具体文件名，但不得把 Word 解析、存储、工具和 Skill 加载全部堆进 `agent.py` 或 `main.py`。

## 11. 依赖变化

后端新增最小依赖：

- `python-docx`：读取 `.docx` 段落和表格。
- `python-multipart`：FastAPI 接收上传文件。
- YAML frontmatter 优先使用项目已有解析能力；如果标准库无法满足，再选择一个小型 YAML 解析依赖，不引入 Deep Agents 只为读取 Skill 元数据。

不在本阶段增加 Redis、Milvus、数据库、MCP 或 Deep Agents。

## 12. 完成标准

只有同时满足以下条件，才能认为该功能完成：

- 一份获准测试的 `.docx` 可以在页面上传并得到解析摘要。
- 当前对话能携带上传返回的 `document_id`。
- Agent 能真实产生并执行合同工具调用，而不是只在提示词中模拟。
- 回答中的原文来自工具定位结果，找不到时不会编造。
- `legal-plain-explanation` Skill 被独立发现和按需加载。
- 合同问题只加载 `contract-terms.md`。
- 回答遵守三段式和法律边界要求。
- 普通聊天、多轮上下文、`/health` 和现有 AG-UI 链路没有回归。
- 后端测试全部通过，前端 lint/build 通过。
- Git 中不包含 `.env`、上传文件、业务合同或密钥。

## 13. 后续扩展顺序

本功能稳定后，再按下列顺序扩展：

1. 用同一份测试合同增加“合同预审 Skill”，复用解析器和 DocumentStore。
2. 增加规则型预审工具，并让结果带条款依据和风险等级。
3. 与带教确认公司 Deep Agents Skill 运行规范，将自建 Registry 替换或适配为公司标准机制。
4. 在获得接口、权限和安全规范后，再连接真实 CLM 测试服务。
5. 最后评估 RAG、向量数据库、持久化、人工审批和深度审查。
