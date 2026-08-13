# 合同条款通俗解释功能实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标：** 在第一阶段本地对话智能体上增加“一次对话上传一份 `.docx` 合同、Agent 调用工具定位条款、按需读取公司 `legal-plain-explanation` Skill、以原文—白话—案例格式回答”的完整闭环。

**架构：** Word 文件通过独立 HTTP 接口上传到 FastAPI，由 Python 解析为结构化条款并存入进程内 `DocumentStore`，前端只保存并随聊天传递 `document_id`。LangGraph 从单节点聊天图升级为 `model → tools → model` 条件循环；模型启动时只看到 Skill 的名称和描述，命中后通过受限的 `read_skill_file` 工具读取完整 `SKILL.md` 及必要 reference。

**技术栈：** Python 3.12、FastAPI、python-docx、LangChain 1.3、LangGraph 1.2、AG-UI、pytest、Next.js 16、React 19、TypeScript 5、CopilotKit v2。

## 全局约束

- 第一版每个对话同时只关联一份 `.docx`，上传新文件即替换当前合同上下文。
- 只使用虚构、脱敏且公司允许用于模型测试的合同；测试不读取真实业务合同。
- `.docx` 最大 10 MiB；空文件、非 `.docx`、损坏或加密文件必须明确报错。
- 合同全文不返回前端、不写入日志、不提交 Git；模型只接收解决当前问题所需的少量条款。
- `document_id` 由后端随机生成，模型不能自行填写或覆盖。
- Skill 采用渐进加载：预加载 `name/description`，命中后读取完整 `SKILL.md`，再按说明读取必要 reference。
- `read_skill_file` 只能访问已登记 Skill 目录内的 `SKILL.md` 和 `references/*.md`，禁止绝对路径与 `..` 路径穿越。
- 条款解释不提供法律建议、不做合规判断、不评价合同效力，结尾保留公司 Skill 的律师咨询声明。
- 不增加数据库、Redis、Milvus、RAG、MCP、Deep Agents、多 Agent、OCR、PDF 或 `.doc` 支持。
- 后端继续使用现有 `requirements.txt` 和 `.venv`；前端继续使用 npm 和 `package-lock.json`，不迁移到 `uv` 或 pnpm。
- 后端在 PyCharm 中学习和运行；前端在 VS Code 中学习和运行。
- 每次提交前显式暂存本任务文件，不使用未经检查的 `git add .`。

## 学习路线总图

```text
任务 1 依赖与安全边界
  ↓
任务 2 Word 解析（先获得可靠数据）
  ↓
任务 3 临时文档仓库（用 document_id 找回数据）
  ↓
任务 4 上传接口（让浏览器能送文件）
  ↓
任务 5 Skill Registry（先看技能目录，后读全文）
  ↓
任务 6 合同工具（目录、定位、读取 Skill）
  ↓
任务 7 LangGraph 工具循环（模型决定，工具执行）
  ↓
任务 8 AG-UI 回归验证（工具事件穿过现有链路）
  ↓
任务 9 Next.js 上传代理
  ↓
任务 10 React 上传区与 document_id Context
  ↓
任务 11 端到端验收、文档与 GitHub 交付
```

## 文件职责锁定

### 后端仓库 `D:\code\aiagent\0824_langchain\backend`

```text
app/
├── config.py                    # 模型配置和 SKILLS_ROOT
├── main.py                      # 组装 Store、Registry、工具、Graph 和 FastAPI
├── agent.py                     # 动态系统提示与 model→tools→model 图
├── documents/
│   ├── __init__.py
│   ├── models.py                # ParsedDocument、ContractSection
│   ├── parser.py                # .docx → 结构化合同
│   ├── store.py                 # DocumentStore 与内存实现
│   └── router.py                # POST /documents
├── skills/
│   ├── __init__.py
│   ├── models.py                # SkillMetadata
│   └── registry.py              # Skill 发现、目录和受限读取
└── tools/
    ├── __init__.py
    ├── context.py               # 从 CopilotKit Context 提取 document_id
    ├── contract.py              # get_document_outline、find_contract_clause
    └── skill.py                 # read_skill_file

tests/
├── __init__.py
├── fakes.py
├── test_document_parser.py
├── test_document_store.py
├── test_documents_api.py
├── test_skill_registry.py
├── test_contract_tools.py
├── test_agent_tools.py
└── test_ag_ui.py                # 扩展第一阶段 AG-UI 回归测试
```

### 前端仓库 `D:\code\aiagent\0824_langchain\frontend`

```text
src/app/
├── page.tsx                     # 当前合同状态、上传控件、清空联动、Agent Context
├── globals.css                  # 上传区四种状态样式
└── api/documents/route.ts       # 浏览器到 FastAPI 的同源上传代理
```

---

### 任务 1：创建第二阶段分支并建立依赖与隐私边界

**它位于链路哪里：** 环境层和交付层。它还没有产生业务能力，但为后续 Word 上传、Skill 路径和安全提交提供地基。

**完成后能看到：** 后端和前端各有一个清晰的第二阶段分支；后端能导入 `docx`、`multipart` 和 `yaml`；本地合同目录与上传文件不会进入 Git。

**为什么先做：** 如果依赖和忽略规则最后才补，可能出现代码写完却无法运行，或测试合同被误提交 GitHub 的风险。

**学习级别：**

- **必须掌握：** 分支用于隔离任务，`.gitignore` 用于阻止本地敏感文件进入提交。
- **熟悉即可：** Python 包为什么分运行依赖和开发依赖。
- **了解即可：** 锁文件和依赖解析器内部如何选择版本。

**文件：**

- 修改：`requirements.txt`
- 修改：`.env.example`
- 修改：`.gitignore`
- 修改：`app/config.py`
- 修改：`tests/test_config.py`
- 前端仅创建分支，本任务不改前端代码。

**接口：**

- 产出：`Settings.skills_root: Path`
- 后续消费：`SkillRegistry(settings.skills_root)`

- [ ] **步骤 1：确认现有未提交内容，不把第一阶段文档改动混入功能提交**

在后端仓库运行：

```powershell
Set-Location D:\code\aiagent\0824_langchain\backend
git status --short --branch
```

命令解释：`Set-Location` 进入后端仓库；`git status` 只查看当前分支和改动，不会修改文件。当前已知旧实施计划存在用户改动，后续每次 `git add` 都必须显式写文件名。

- [ ] **步骤 2：创建后端第二阶段分支**

```powershell
git switch -c feat/legal-explanation
```

命令解释：以当前已包含第一阶段和设计文档的提交为起点，创建并切换到 `feat/legal-explanation`。未提交文件仍会保留，但不会自动进入提交。

- [ ] **步骤 3：创建前端第二阶段分支**

在 VS Code 前端终端运行：

```powershell
Set-Location D:\code\aiagent\0824_langchain\frontend
git switch -c feat/legal-explanation
```

预期：两个仓库执行 `git branch --show-current` 都输出 `feat/legal-explanation`。

- [ ] **步骤 4：先写配置失败测试**

在 `tests/test_config.py` 增加：

```python
from pathlib import Path


def test_settings_accepts_external_skills_root() -> None:
    settings = Settings(
        OPENAI_API_KEY=SecretStr("test-key"),
        OPENAI_BASE_URL="https://models.example.test/v1",
        OPENAI_MODEL="test-model",
        SKILLS_ROOT="D:/company/skills",
    )

    assert settings.skills_root == Path("D:/company/skills")
```

- [ ] **步骤 5：运行测试并确认它按预期失败**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_config.py -q
```

命令解释：使用后端项目自己的虚拟环境，只运行配置测试。预期失败原因是 `Settings` 还没有 `skills_root` 字段，而不是导入错误。

- [ ] **步骤 6：增加最小配置实现**

在 `app/config.py` 增加导入和字段：

```python
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: SecretStr = Field(validation_alias="OPENAI_API_KEY")
    openai_base_url: str = Field(validation_alias="OPENAI_BASE_URL")
    openai_model: str = Field(validation_alias="OPENAI_MODEL")
    skills_root: Path = Field(
        default=Path("skills"),
        validation_alias="SKILLS_ROOT",
    )
```

- [ ] **步骤 7：增加依赖和示例配置**

在 `requirements.txt` 末尾增加：

```text
python-docx>=1.1,<2.0
python-multipart>=0.0.20,<1.0
PyYAML>=6.0,<7.0
```

在 `.env.example` 增加：

```dotenv
SKILLS_ROOT=skills
```

你自己的 `.env` 使用本机公司 Skill 路径，例如 `D:/code/公司/skills`；不要把个人绝对路径写进 `.env.example`。

- [ ] **步骤 8：增加合同文件忽略规则**

在 `.gitignore` 增加：

```gitignore
# Local contract inputs
uploads/
local-contracts/
*.docx
```

自动化测试将在内存中生成 Word，不依赖提交 `.docx` fixture，因此可以安全地全局忽略 `.docx`。

- [ ] **步骤 9：安装依赖并验证配置测试**

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest tests\test_config.py -q
.\.venv\Scripts\python.exe -m pip check
```

命令解释：第一条把新增运行依赖装进现有后端虚拟环境；第二条验证配置；第三条检查已安装包之间是否有冲突。预期配置测试通过，`pip check` 输出 `No broken requirements found.`。

- [ ] **步骤 10：只提交本任务文件**

```powershell
git add requirements.txt .env.example .gitignore app/config.py tests/test_config.py
git diff --cached --check
git commit -m "build: prepare contract skill dependencies"
```

---

### 任务 2：把 Word 合同解析成可追溯的条款结构

**它位于链路哪里：** 后端数据入口层。它把人类使用的 Word 文件转换成工具能够稳定查询的数据。

**完成后能看到：** 一段测试代码生成虚构 Word 后，解析结果中能看到合同标题、条款编号、标题、正文、表格数量和警告。

**为什么这样做：** 模型不能可靠地直接处理不同格式的 Word。先结构化后，回答才能引用“第八条”而不是从整份文本里猜。

**学习级别：**

- **必须掌握：** 解析器的输入是 Word 字节，输出是结构化合同；解析与法律解释是两个职责。
- **熟悉即可：** dataclass、正则表达式、段落和表格。
- **了解即可：** `.docx` 内部 XML 以及如何按原顺序遍历块。

**文件：**

- 新建：`app/documents/__init__.py`
- 新建：`app/documents/models.py`
- 新建：`app/documents/parser.py`
- 新建：`tests/test_document_parser.py`

**接口：**

- 产出：`parse_docx(content: bytes, filename: str) -> ParsedDocument`
- 产出：`ContractSection(section_id, number, heading, content)`
- 后续消费：`InMemoryDocumentStore.put()`、合同查询工具。

- [ ] **步骤 1：写解析器失败测试**

新建 `tests/test_document_parser.py`：

```python
from io import BytesIO

from docx import Document

from app.documents.parser import parse_docx


def build_contract_bytes() -> bytes:
    document = Document()
    document.add_paragraph("示例采购合同")
    document.add_paragraph("第一条 合同标的")
    document.add_paragraph("乙方向甲方提供测试设备。")
    document.add_paragraph("第二条 付款方式")
    document.add_paragraph("甲方应当于验收后十日内付款。")
    table = document.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "合同金额"
    table.cell(0, 1).text = "1000元"
    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def test_parse_docx_preserves_sections_and_tables() -> None:
    parsed = parse_docx(build_contract_bytes(), "示例采购合同.docx")

    assert parsed.filename == "示例采购合同.docx"
    assert parsed.title == "示例采购合同"
    assert parsed.table_count == 1
    assert [(section.number, section.heading) for section in parsed.sections] == [
        ("第一条", "合同标的"),
        ("第二条", "付款方式"),
    ]
    assert "验收后十日内付款" in parsed.sections[1].content


def test_parse_docx_without_headings_falls_back_to_paragraph_sections() -> None:
    document = Document()
    document.add_paragraph("未使用标准标题的合同")
    document.add_paragraph("双方约定按月付款。")
    buffer = BytesIO()
    document.save(buffer)

    parsed = parse_docx(buffer.getvalue(), "非标准合同.docx")

    assert len(parsed.sections) == 2
    assert "未识别出显式条款标题" in parsed.warnings
```

- [ ] **步骤 2：运行并确认失败位置正确**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_document_parser.py -q
```

预期：`ModuleNotFoundError: No module named 'app.documents'`。这表示测试已经到达我们计划新增的模块边界。

- [ ] **步骤 3：定义数据模型**

新建空文件 `app/documents/__init__.py`，新建 `app/documents/models.py`：

```python
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ContractSection:
    section_id: str
    number: str | None
    heading: str | None
    content: str


@dataclass(frozen=True)
class ParsedDocument:
    filename: str
    title: str | None
    sections: tuple[ContractSection, ...]
    blocks: tuple[str, ...]
    table_count: int
    warnings: tuple[str, ...] = field(default_factory=tuple)
```

- [ ] **步骤 4：实现最小 Word 解析器**

新建 `app/documents/parser.py`：

```python
import re
from io import BytesIO
from typing import Iterator

from docx import Document
from docx.document import Document as DocxDocument
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph

from app.documents.models import ContractSection, ParsedDocument


ARTICLE_RE = re.compile(
    r"^(第[一二三四五六七八九十百零〇0-9]+条)\s*[：:、.．]?\s*(.*)$"
)
NUMBERED_RE = re.compile(r"^([一二三四五六七八九十]+、)\s*(.*)$")


class DocumentParseError(ValueError):
    pass


def _iter_blocks(document: DocxDocument) -> Iterator[tuple[str, bool]]:
    for child in document.element.body.iterchildren():
        if isinstance(child, CT_P):
            text = Paragraph(child, document).text.strip()
            if text:
                yield text, False
        elif isinstance(child, CT_Tbl):
            table = Table(child, document)
            rows = [
                " | ".join(cell.text.strip() for cell in row.cells)
                for row in table.rows
            ]
            text = "\n".join(row for row in rows if row.strip(" |"))
            if text:
                yield text, True


def _heading(text: str) -> tuple[str, str] | None:
    match = ARTICLE_RE.match(text) or NUMBERED_RE.match(text)
    if match is None:
        return None
    return match.group(1), match.group(2).strip()


def _build_sections(blocks: list[str]) -> tuple[list[ContractSection], list[str]]:
    sections: list[ContractSection] = []
    current_number: str | None = None
    current_heading: str | None = None
    current_content: list[str] = []

    def flush() -> None:
        nonlocal current_number, current_heading, current_content
        if current_number is None:
            return
        sections.append(
            ContractSection(
                section_id=f"section-{len(sections) + 1}",
                number=current_number,
                heading=current_heading or None,
                content="\n".join(current_content).strip(),
            )
        )
        current_content = []

    for block in blocks:
        heading = _heading(block)
        if heading is not None:
            flush()
            current_number, current_heading = heading
        elif current_number is not None:
            current_content.append(block)

    flush()
    if sections:
        return sections, []

    fallback = [
        ContractSection(
            section_id=f"paragraph-{index}",
            number=None,
            heading=None,
            content=block,
        )
        for index, block in enumerate(blocks, start=1)
    ]
    return fallback, ["未识别出显式条款标题"]


def parse_docx(content: bytes, filename: str) -> ParsedDocument:
    if not content:
        raise DocumentParseError("Word 文件为空")

    try:
        document = Document(BytesIO(content))
    except Exception as error:
        raise DocumentParseError("Word 文件损坏、加密或格式不受支持") from error

    block_items = list(_iter_blocks(document))
    blocks = [text for text, _ in block_items]
    table_count = sum(1 for _, is_table in block_items if is_table)
    sections, warnings = _build_sections(blocks)
    title = blocks[0] if blocks and _heading(blocks[0]) is None else None

    return ParsedDocument(
        filename=filename,
        title=title,
        sections=tuple(sections),
        blocks=tuple(blocks),
        table_count=table_count,
        warnings=tuple(warnings),
    )
```

- [ ] **步骤 5：运行解析器测试并检查全量回归**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_document_parser.py -q
.\.venv\Scripts\python.exe -m pytest -q
```

第一条应显示 `2 passed`；第二条确保第一阶段配置、模型、对话和接口没有被破坏。

- [ ] **步骤 6：提交解析器**

```powershell
git add app/documents/__init__.py app/documents/models.py app/documents/parser.py tests/test_document_parser.py
git diff --cached --check
git commit -m "feat: parse Word contracts into sections"
```

---

### 任务 3：用 `document_id` 管理当前合同

**它位于链路哪里：** 后端状态层，连接“上传文件”和“后续聊天”。

**完成后能看到：** 解析后的合同可以存入内存，得到随机 `document_id`，并能用该编号重新取回；不存在的编号产生明确错误。

**为什么这样做：** 前端不能每问一句都重传合同全文；模型也不能直接接触服务器路径。`document_id` 就是安全的取件码。

**学习级别：**

- **必须掌握：** `document_id` 是引用，不是合同内容；Store 隔离了“怎么保存”和“怎么使用”。
- **熟悉即可：** Protocol、UUID、自定义异常。
- **了解即可：** 后续如何替换成 Redis 或数据库。

**文件：**

- 新建：`app/documents/store.py`
- 新建：`tests/test_document_store.py`

**接口：**

- 产出：`DocumentStore.put(document) -> str`
- 产出：`DocumentStore.get(document_id) -> ParsedDocument`
- 产出：`DocumentNotFoundError`

- [ ] **步骤 1：写 Store 失败测试**

新建 `tests/test_document_store.py`：

```python
import pytest

from app.documents.models import ParsedDocument
from app.documents.store import DocumentNotFoundError, InMemoryDocumentStore


def make_document() -> ParsedDocument:
    return ParsedDocument(
        filename="示例合同.docx",
        title="示例合同",
        sections=(),
        blocks=(),
        table_count=0,
    )


def test_store_returns_document_by_random_id() -> None:
    store = InMemoryDocumentStore()
    document_id = store.put(make_document())

    assert document_id != "示例合同.docx"
    assert store.get(document_id).filename == "示例合同.docx"


def test_store_raises_for_unknown_document() -> None:
    store = InMemoryDocumentStore()

    with pytest.raises(DocumentNotFoundError):
        store.get("missing")
```

- [ ] **步骤 2：确认测试因模块缺失失败**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_document_store.py -q
```

- [ ] **步骤 3：实现 Store 接口和内存版本**

新建 `app/documents/store.py`：

```python
from typing import Protocol
from uuid import uuid4

from app.documents.models import ParsedDocument


class DocumentNotFoundError(KeyError):
    pass


class DocumentStore(Protocol):
    def put(self, document: ParsedDocument) -> str: ...

    def get(self, document_id: str) -> ParsedDocument: ...


class InMemoryDocumentStore:
    def __init__(self) -> None:
        self._documents: dict[str, ParsedDocument] = {}

    def put(self, document: ParsedDocument) -> str:
        document_id = str(uuid4())
        self._documents[document_id] = document
        return document_id

    def get(self, document_id: str) -> ParsedDocument:
        try:
            return self._documents[document_id]
        except KeyError as error:
            raise DocumentNotFoundError(document_id) from error
```

- [ ] **步骤 4：运行测试、提交**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_document_store.py -q
git add app/documents/store.py tests/test_document_store.py
git diff --cached --check
git commit -m "feat: add temporary document store"
```

---

### 任务 4：增加安全、可测试的 Word 上传接口

**它位于链路哪里：** FastAPI HTTP 边界。浏览器文件第一次进入 Python 后端就在这里。

**完成后能看到：** 测试客户端上传虚构 `.docx` 后收到 `201` 和 `document_id`；错误扩展名、空文件、超大文件和损坏文件得到明确状态码。

**为什么这样做：** 上传与聊天分开后，每个接口都能单独测试；模型不需要理解 multipart 或 Word 格式。

**学习级别：**

- **必须掌握：** 上传接口只负责校验、解析、存储和返回摘要。
- **熟悉即可：** `UploadFile`、HTTP 201/400/413/415/422。
- **了解即可：** multipart 的底层编码。

**文件：**

- 新建：`tests/__init__.py`
- 新建：`app/documents/router.py`
- 新建：`tests/test_documents_api.py`
- 修改：`app/main.py`

**接口：**

- 产出：`create_documents_router(store: DocumentStore) -> APIRouter`
- 产出：`POST /documents`
- 后续消费：Next.js `/api/documents` 代理。

- [ ] **步骤 1：写成功与失败接口测试**

新建 `tests/test_documents_api.py`：

```python
from io import BytesIO

from docx import Document
from fastapi.testclient import TestClient

from app.documents.store import InMemoryDocumentStore
from app.main import create_app
from tests.fakes import BindableFakeListChatModel


def contract_bytes() -> bytes:
    document = Document()
    document.add_paragraph("示例合同")
    document.add_paragraph("第一条 付款")
    document.add_paragraph("甲方应当于十日内付款。")
    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def test_upload_document_returns_summary() -> None:
    store = InMemoryDocumentStore()
    app = create_app(
        model=BindableFakeListChatModel(responses=["ok"]),
        document_store=store,
    )

    response = TestClient(app).post(
        "/documents",
        files={
            "file": (
                "示例合同.docx",
                contract_bytes(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["filename"] == "示例合同.docx"
    assert payload["section_count"] == 1
    assert store.get(payload["document_id"]).filename == "示例合同.docx"


def test_upload_rejects_non_docx() -> None:
    app = create_app(
        model=BindableFakeListChatModel(responses=["ok"]),
        document_store=InMemoryDocumentStore(),
    )

    response = TestClient(app).post(
        "/documents",
        files={"file": ("contract.txt", b"text", "text/plain")},
    )

    assert response.status_code == 415


def test_upload_rejects_empty_docx() -> None:
    app = create_app(
        model=BindableFakeListChatModel(responses=["ok"]),
        document_store=InMemoryDocumentStore(),
    )

    response = TestClient(app).post(
        "/documents",
        files={"file": ("empty.docx", b"", "application/octet-stream")},
    )

    assert response.status_code == 400


def test_upload_rejects_oversized_docx() -> None:
    app = create_app(
        model=BindableFakeListChatModel(responses=["ok"]),
        document_store=InMemoryDocumentStore(),
    )

    response = TestClient(app).post(
        "/documents",
        files={
            "file": (
                "large.docx",
                b"x" * (10 * 1024 * 1024 + 1),
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 413


def test_upload_rejects_broken_docx() -> None:
    app = create_app(
        model=BindableFakeListChatModel(responses=["ok"]),
        document_store=InMemoryDocumentStore(),
    )

    response = TestClient(app).post(
        "/documents",
        files={
            "file": (
                "broken.docx",
                b"not-a-word-file",
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 422
```

- [ ] **步骤 2：先创建测试假模型，避免现有 Fake 模型不支持 `bind_tools`**

新建空文件 `tests/__init__.py`，让 `tests.fakes` 稳定表示项目自己的测试模块，而不是误导入环境中其他同名包。再新建 `tests/fakes.py`：

```python
from collections.abc import Sequence
from typing import Any

from langchain_core.language_models.fake_chat_models import (
    FakeListChatModel,
    FakeMessagesListChatModel,
)


class BindableFakeListChatModel(FakeListChatModel):
    def bind_tools(self, tools: Sequence[Any], **kwargs: Any):
        return self


class BindableFakeMessagesListChatModel(FakeMessagesListChatModel):
    def bind_tools(self, tools: Sequence[Any], **kwargs: Any):
        return self
```

这里不是模拟工具执行，而只是让测试假模型接受“绑定工具”这一步；真正的 `ToolNode` 仍由 LangGraph 执行。

- [ ] **步骤 3：运行接口测试并确认路由尚不存在**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_documents_api.py -q
```

预期最先失败于 `create_app` 尚不接受 `document_store` 或 `/documents` 返回 404。

- [ ] **步骤 4：实现上传路由**

新建 `app/documents/router.py`：

```python
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.documents.parser import DocumentParseError, parse_docx
from app.documents.store import DocumentStore


MAX_DOCUMENT_BYTES = 10 * 1024 * 1024


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    section_count: int
    table_count: int
    warnings: list[str]


def create_documents_router(store: DocumentStore) -> APIRouter:
    router = APIRouter()

    @router.post(
        "/documents",
        response_model=DocumentUploadResponse,
        status_code=status.HTTP_201_CREATED,
    )
    async def upload_document(file: UploadFile = File(...)) -> DocumentUploadResponse:
        filename = Path(file.filename or "").name
        if Path(filename).suffix.lower() != ".docx":
            raise HTTPException(status_code=415, detail="仅支持 .docx Word 文件")

        content = await file.read(MAX_DOCUMENT_BYTES + 1)
        if not content:
            raise HTTPException(status_code=400, detail="上传文件为空")
        if len(content) > MAX_DOCUMENT_BYTES:
            raise HTTPException(status_code=413, detail="文件不能超过 10 MiB")

        try:
            document = parse_docx(content, filename)
        except DocumentParseError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

        document_id = store.put(document)
        return DocumentUploadResponse(
            document_id=document_id,
            filename=document.filename,
            section_count=len(document.sections),
            table_count=document.table_count,
            warnings=list(document.warnings),
        )

    return router
```

- [ ] **步骤 5：让 `create_app` 接受并注册 Store**

在 `app/main.py` 中增加两个导入，并把 `create_app` 函数调整为：

```python
from app.documents.router import create_documents_router
from app.documents.store import DocumentStore, InMemoryDocumentStore


def create_app(
    model: BaseChatModel | None = None,
    document_store: DocumentStore | None = None,
) -> FastAPI:
    resolved_model = model or create_chat_model()
    resolved_store = document_store or InMemoryDocumentStore()
    graph = build_chat_graph(resolved_model)

    agent = LangGraphAgent(
        name=AGENT_ID,
        description="A local streaming chat agent.",
        graph=graph,
        config={"recursion_limit": 12},
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

    fastapi_app.include_router(create_documents_router(resolved_store))
    add_langgraph_fastapi_endpoint(fastapi_app, agent, path="/agent")
    return fastapi_app
```

这一阶段 `resolved_store` 还没有传入 Agent 工具；任务 6 会把它接上。先让上传接口独立通过。

- [ ] **步骤 6：运行接口与全量测试**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_documents_api.py -q
.\.venv\Scripts\python.exe -m pytest -q
```

- [ ] **步骤 7：提交上传接口**

```powershell
git add app/documents/router.py app/main.py tests/__init__.py tests/fakes.py tests/test_documents_api.py
git diff --cached --check
git commit -m "feat: add Word document upload endpoint"
```

---

### 任务 5：实现 Skill 目录预加载和受限文件读取

**它位于链路哪里：** Agent 能力层。它让模型先知道“有哪些技能”，命中后再读取完整操作手册。

**完成后能看到：** Registry 可以列出 `legal-plain-explanation` 的名称和描述；能读取它的 `SKILL.md` 与 `references/contract-terms.md`；无法读取其他目录或任意电脑文件。

**为什么这样做：** 全量加载所有 Skill 会浪费上下文；通用 `read_file` 又会带来文件泄露风险。Registry 是“技能目录管理员”和“安全门卫”。

**学习级别：**

- **必须掌握：** 预加载元数据、按需读取正文，以及 Tool 与 Skill 的区别。
- **熟悉即可：** YAML frontmatter、路径解析和缓存。
- **了解即可：** 将来 Deep Agents 如何替换这层 Registry。

**文件：**

- 新建：`app/skills/__init__.py`
- 新建：`app/skills/models.py`
- 新建：`app/skills/registry.py`
- 新建：`tests/test_skill_registry.py`

**接口：**

- 产出：`SkillRegistry.discover() -> tuple[SkillMetadata, ...]`
- 产出：`SkillRegistry.catalog_prompt() -> str`
- 产出：`SkillRegistry.read_file(skill_name, relative_path) -> str`

- [ ] **步骤 1：使用临时目录写失败测试**

新建 `tests/test_skill_registry.py`：

```python
from pathlib import Path

import pytest

from app.skills.registry import SkillAccessError, SkillRegistry


def create_skill(root: Path) -> None:
    skill = root / "legal-plain-explanation"
    references = skill / "references"
    references.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\n"
        "name: legal-plain-explanation\n"
        "description: 将合同条款翻译为日常语言。\n"
        "---\n\n"
        "# 法律条款通俗解释\n",
        encoding="utf-8",
    )
    (references / "contract-terms.md").write_text(
        "# 合同术语\n",
        encoding="utf-8",
    )


def test_registry_preloads_only_name_and_description(tmp_path: Path) -> None:
    create_skill(tmp_path)
    registry = SkillRegistry(tmp_path)

    catalog = registry.catalog_prompt()

    assert "legal-plain-explanation" in catalog
    assert "将合同条款翻译为日常语言" in catalog
    assert "# 法律条款通俗解释" not in catalog


def test_registry_reads_registered_skill_files(tmp_path: Path) -> None:
    create_skill(tmp_path)
    registry = SkillRegistry(tmp_path)

    assert "# 法律条款通俗解释" in registry.read_file(
        "legal-plain-explanation",
        "SKILL.md",
    )
    assert "# 合同术语" in registry.read_file(
        "legal-plain-explanation",
        "references/contract-terms.md",
    )


@pytest.mark.parametrize(
    "relative_path",
    ["../secret.txt", "C:/Windows/win.ini", "references/../../secret.txt"],
)
def test_registry_rejects_paths_outside_skill(
    tmp_path: Path,
    relative_path: str,
) -> None:
    create_skill(tmp_path)
    registry = SkillRegistry(tmp_path)

    with pytest.raises(SkillAccessError):
        registry.read_file("legal-plain-explanation", relative_path)
```

- [ ] **步骤 2：运行并确认模块缺失失败**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_skill_registry.py -q
```

- [ ] **步骤 3：定义 Skill 元数据**

新建空文件 `app/skills/__init__.py`，新建 `app/skills/models.py`：

```python
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SkillMetadata:
    name: str
    description: str
    root: Path
```

- [ ] **步骤 4：实现 Registry**

新建 `app/skills/registry.py`：

```python
from functools import lru_cache
from pathlib import Path, PurePosixPath

import yaml

from app.skills.models import SkillMetadata


class SkillRegistryError(ValueError):
    pass


class SkillAccessError(SkillRegistryError):
    pass


def _frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        raise SkillRegistryError("SKILL.md 缺少 YAML frontmatter")
    _, raw_metadata, _ = text.split("---", maxsplit=2)
    data = yaml.safe_load(raw_metadata) or {}
    if not isinstance(data.get("name"), str) or not isinstance(
        data.get("description"), str
    ):
        raise SkillRegistryError("SKILL.md 必须包含 name 和 description")
    return data


class SkillRegistry:
    def __init__(self, root: Path) -> None:
        self.root = root.expanduser().resolve()
        self._skills = {skill.name: skill for skill in self.discover()}

    def discover(self) -> tuple[SkillMetadata, ...]:
        if not self.root.exists():
            return ()
        discovered: list[SkillMetadata] = []
        for skill_file in sorted(self.root.glob("*/SKILL.md")):
            text = skill_file.read_text(encoding="utf-8")
            metadata = _frontmatter(text)
            discovered.append(
                SkillMetadata(
                    name=metadata["name"],
                    description=metadata["description"],
                    root=skill_file.parent.resolve(),
                )
            )
        return tuple(discovered)

    def catalog_prompt(self) -> str:
        if not self._skills:
            return "当前没有已登记的 Skill。"
        lines = ["可用 Skills："]
        lines.extend(
            f"- {skill.name}: {skill.description}"
            for skill in self._skills.values()
        )
        return "\n".join(lines)

    @lru_cache(maxsize=64)
    def read_file(self, skill_name: str, relative_path: str) -> str:
        skill = self._skills.get(skill_name)
        if skill is None:
            raise SkillAccessError(f"未登记的 Skill: {skill_name}")

        posix_path = PurePosixPath(relative_path.replace("\\", "/"))
        if posix_path.is_absolute() or ".." in posix_path.parts:
            raise SkillAccessError("Skill 文件路径不合法")
        if posix_path.as_posix() != "SKILL.md" and (
            len(posix_path.parts) < 2 or posix_path.parts[0] != "references"
        ):
            raise SkillAccessError("只允许读取 SKILL.md 或 references 目录")

        target = (skill.root / Path(*posix_path.parts)).resolve()
        try:
            target.relative_to(skill.root)
        except ValueError as error:
            raise SkillAccessError("Skill 文件路径越界") from error
        if not target.is_file():
            raise SkillAccessError(f"Skill 文件不存在: {relative_path}")
        return target.read_text(encoding="utf-8")
```

- [ ] **步骤 5：运行测试并验证实际公司 Skill 只读发现**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_skill_registry.py -q
.\.venv\Scripts\python.exe -c "from app.config import get_settings; from app.skills.registry import SkillRegistry; print(SkillRegistry(get_settings().skills_root).catalog_prompt())"
```

第二条命令只打印 Skill 名称和描述，不读取合同，也不打印 API Key。预期目录中出现 `legal-plain-explanation`。如果没有出现，检查 `.env` 的 `SKILLS_ROOT`，不要把密钥或完整 `.env` 发出来。

- [ ] **步骤 6：提交 Registry**

```powershell
git add app/skills/__init__.py app/skills/models.py app/skills/registry.py tests/test_skill_registry.py
git diff --cached --check
git commit -m "feat: add progressive skill registry"
```

---

### 任务 6：实现三个只读工具和当前合同上下文解析

**它位于链路哪里：** LangChain 工具层。它把 DocumentStore 和 SkillRegistry 中的确定性能力包装成模型可以请求的工具。

**完成后能看到：** 在不调用真实模型的测试中，工具能从 CopilotKit Context 找到当前 `document_id`，列出合同目录、定位指定条款，并读取指定 Skill 文件。

**为什么这样做：** 模型只负责决定“用哪个工具、查什么”，真正的数据读取由 Python 完成。`document_id` 必须由运行状态注入，不能让模型猜。

**学习级别：**

- **必须掌握：** 工具名称、描述、模型可填参数、系统注入参数和返回值。
- **熟悉即可：** `ToolRuntime` 如何把当前 LangGraph 状态注入工具。
- **了解即可：** LangGraph 如何从类型标注中隐藏注入参数。

**文件：**

- 新建：`app/tools/__init__.py`
- 新建：`app/tools/context.py`
- 新建：`app/tools/contract.py`
- 新建：`app/tools/skill.py`
- 新建：`tests/test_contract_tools.py`

**接口：**

- 产出：`extract_current_document_id(state: dict) -> str`
- 产出：`create_contract_tools(store) -> list[BaseTool]`
- 产出：`create_skill_tools(registry) -> list[BaseTool]`

- [ ] **步骤 1：写 Context 与合同工具失败测试**

新建 `tests/test_contract_tools.py`：

```python
import json
from types import SimpleNamespace

import pytest

from app.documents.models import ContractSection, ParsedDocument
from app.documents.store import InMemoryDocumentStore
from app.skills.registry import SkillRegistry
from app.tools.context import MissingDocumentContextError, extract_current_document_id
from app.tools.contract import create_contract_tools
from app.tools.skill import create_skill_tools


def uploaded_document() -> ParsedDocument:
    return ParsedDocument(
        filename="示例采购合同.docx",
        title="示例采购合同",
        sections=(
            ContractSection(
                section_id="section-1",
                number="第一条",
                heading="付款方式",
                content="甲方应当于验收后十日内付款。",
            ),
            ContractSection(
                section_id="section-2",
                number="第二条",
                heading="违约责任",
                content="保证人承担连带责任。",
            ),
        ),
        blocks=(),
        table_count=0,
    )


def runtime_for(document_id: str):
    return SimpleNamespace(
        state={
            "copilotkit": {
                "context": [
                    {
                        "description": "当前对话中用户已上传的合同",
                        "value": json.dumps(
                            {
                                "document_id": document_id,
                                "filename": "示例采购合同.docx",
                            },
                            ensure_ascii=False,
                        ),
                    }
                ]
            }
        }
    )


def test_extract_document_id_rejects_missing_context() -> None:
    with pytest.raises(MissingDocumentContextError):
        extract_current_document_id({"copilotkit": {"context": []}})


def test_outline_and_clause_tools_use_context_document_id() -> None:
    store = InMemoryDocumentStore()
    document_id = store.put(uploaded_document())
    outline_tool, clause_tool = create_contract_tools(store)
    runtime = runtime_for(document_id)

    outline = outline_tool.func(runtime=runtime)
    matches = clause_tool.func(query="连带责任", runtime=runtime)

    assert outline["filename"] == "示例采购合同.docx"
    assert outline["sections"][1]["heading"] == "违约责任"
    assert matches["matches"][0]["section_id"] == "section-2"
    assert "连带责任" in matches["matches"][0]["content"]
```

再增加两个断言：查询“第二条”优先命中精确编号；查询不存在的“自动续约”返回 `{"error": "clause_not_found", ...}`，不得生成伪原文。

- [ ] **步骤 2：写受限 Skill 工具测试**

在同一文件增加：

```python
def test_read_skill_file_tool_delegates_to_registry(tmp_path) -> None:
    skill = tmp_path / "legal-plain-explanation"
    skill.mkdir()
    (skill / "SKILL.md").write_text(
        "---\n"
        "name: legal-plain-explanation\n"
        "description: 通俗解释合同条款。\n"
        "---\n\n"
        "严格三段式。\n",
        encoding="utf-8",
    )
    registry = SkillRegistry(tmp_path)
    (read_skill_file,) = create_skill_tools(registry)

    result = read_skill_file.func(
        skill_name="legal-plain-explanation",
        relative_path="SKILL.md",
    )

    assert "严格三段式" in result
```

- [ ] **步骤 3：运行并确认工具模块缺失**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_contract_tools.py -q
```

- [ ] **步骤 4：实现 CopilotKit Context 解析**

新建空文件 `app/tools/__init__.py`，新建 `app/tools/context.py`：

```python
import json
from typing import Any


CURRENT_DOCUMENT_CONTEXT = "当前对话中用户已上传的合同"


class MissingDocumentContextError(ValueError):
    pass


def extract_current_document_id(state: dict[str, Any]) -> str:
    copilotkit = state.get("copilotkit") or {}
    for item in copilotkit.get("context") or []:
        if item.get("description") != CURRENT_DOCUMENT_CONTEXT:
            continue
        value = item.get("value")
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                value = {}
        if isinstance(value, dict):
            document_id = value.get("document_id")
            if isinstance(document_id, str) and document_id:
                return document_id
    raise MissingDocumentContextError("请先上传一份 Word 合同")
```

这里同时兼容字典和 JSON 字符串，是因为 CopilotKit v2 会把 JSON 可序列化 Context 转换后送入协议。

- [ ] **步骤 5：实现合同目录和条款定位工具**

新建 `app/tools/contract.py`：

```python
from typing import Any

from langchain_core.tools import BaseTool, tool
from langgraph.prebuilt import ToolRuntime

from app.documents.models import ContractSection
from app.documents.store import DocumentNotFoundError, DocumentStore
from app.tools.context import MissingDocumentContextError, extract_current_document_id


def _match_score(section: ContractSection, query: str) -> tuple[int, str]:
    normalized = query.strip().lower()
    number = (section.number or "").lower()
    heading = (section.heading or "").lower()
    content = section.content.lower()
    if normalized == number:
        return 100, "条款编号精确匹配"
    if normalized == heading:
        return 90, "条款标题精确匹配"
    if normalized and normalized in heading:
        return 80, "条款标题包含关键词"
    if normalized and normalized in content:
        return 60, "条款正文包含关键词"
    return 0, ""


def create_contract_tools(store: DocumentStore) -> list[BaseTool]:
    def current_document(runtime: ToolRuntime):
        document_id = extract_current_document_id(runtime.state)
        return store.get(document_id)

    @tool
    def get_document_outline(runtime: ToolRuntime) -> dict[str, Any]:
        """列出当前已上传合同的条款编号和标题，不返回整份合同正文。"""
        try:
            document = current_document(runtime)
        except MissingDocumentContextError as error:
            return {"error": "missing_document", "message": str(error)}
        except DocumentNotFoundError:
            return {
                "error": "document_not_found",
                "message": "临时合同已失效，请重新上传",
            }
        return {
            "filename": document.filename,
            "title": document.title,
            "sections": [
                {
                    "section_id": section.section_id,
                    "number": section.number,
                    "heading": section.heading,
                }
                for section in document.sections
            ],
        }

    @tool
    def find_contract_clause(
        query: str,
        runtime: ToolRuntime,
    ) -> dict[str, Any]:
        """按条款编号、标题或关键词查找当前合同原文；找不到时不要猜测。"""
        try:
            document = current_document(runtime)
        except MissingDocumentContextError as error:
            return {"error": "missing_document", "message": str(error)}
        except DocumentNotFoundError:
            return {
                "error": "document_not_found",
                "message": "临时合同已失效，请重新上传",
            }

        ranked = []
        for section in document.sections:
            score, reason = _match_score(section, query)
            if score:
                ranked.append((score, reason, section))
        ranked.sort(key=lambda item: item[0], reverse=True)
        if not ranked:
            return {
                "error": "clause_not_found",
                "message": f"未在当前合同中找到与“{query}”可靠匹配的条款",
            }

        return {
            "query": query,
            "matches": [
                {
                    "section_id": section.section_id,
                    "number": section.number,
                    "heading": section.heading,
                    "content": section.content[:4000],
                    "match_reason": reason,
                }
                for _, reason, section in ranked[:3]
            ],
        }

    return [get_document_outline, find_contract_clause]
```

- [ ] **步骤 6：实现 Skill 文件读取工具**

新建 `app/tools/skill.py`：

```python
from langchain_core.tools import BaseTool, tool

from app.skills.registry import SkillAccessError, SkillRegistry


def create_skill_tools(registry: SkillRegistry) -> list[BaseTool]:
    @tool
    def read_skill_file(skill_name: str, relative_path: str) -> str:
        """读取已登记 Skill 的 SKILL.md 或 references 文件；不能读取其他路径。"""
        try:
            return registry.read_file(skill_name, relative_path)
        except SkillAccessError as error:
            return f"Skill 文件读取失败：{error}"

    return [read_skill_file]
```

- [ ] **步骤 7：运行工具测试和全量回归**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_contract_tools.py -q
.\.venv\Scripts\python.exe -m pytest -q
```

- [ ] **步骤 8：提交工具层**

```powershell
git add app/tools/__init__.py app/tools/context.py app/tools/contract.py app/tools/skill.py tests/test_contract_tools.py
git diff --cached --check
git commit -m "feat: add contract and skill tools"
```

---

### 任务 7：把 LangGraph 从聊天直线升级为工具循环

**它位于链路哪里：** Agent 编排核心。第一阶段的 `START → model → END` 在这里升级为模型判断、工具执行、再回到模型的循环。

**完成后能看到：** 自动化测试中的假模型先发出 `find_contract_clause` 请求，LangGraph 执行后把原文作为 `ToolMessage` 送回模型；模型还可以继续调用 `read_skill_file`，最后再生成答案。

**为什么这样做：** `bind_tools` 只是把工具菜单交给模型，真正执行必须有 `ToolNode` 和条件边。缺少任何一环，模型都只会“说自己要调用工具”而不会得到结果。

**学习级别：**

- **必须掌握：** `bind_tools`、`ToolNode`、`tool_calls`、条件边和 `model → tools → model`。
- **熟悉即可：** 动态系统提示、递归上限、ToolMessage。
- **了解即可：** LangGraph 内部事件调度和 Runnable 协议。

**文件：**

- 修改：`app/agent.py`
- 修改：`app/main.py`
- 修改：`tests/test_agent.py`
- 新建：`tests/test_agent_tools.py`
- 修改：`tests/test_health.py`
- 修改：`tests/test_ag_ui.py`

**接口：**

- 修改：`build_chat_graph(model, document_store, skill_registry, checkpointer=None)`
- 产出：工具绑定后的 `CompiledStateGraph`

- [ ] **步骤 1：先让现有纯聊天测试适配可绑定工具的假模型**

把 `tests/test_agent.py` 中的 `FakeListChatModel` 替换为：

```python
from tests.fakes import BindableFakeListChatModel
```

并把两处实例改成 `BindableFakeListChatModel(...)`。在测试中创建空 Store 和空 Skill 根目录，通过新增参数传给 `build_chat_graph`。

- [ ] **步骤 2：写完整工具循环失败测试**

新建 `tests/test_agent_tools.py`：

```python
import json

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.agent import build_chat_graph
from app.documents.models import ContractSection, ParsedDocument
from app.documents.store import InMemoryDocumentStore
from app.skills.registry import SkillRegistry
from tests.fakes import BindableFakeMessagesListChatModel


def test_graph_executes_clause_and_skill_tools(tmp_path) -> None:
    skill_root = tmp_path / "legal-plain-explanation"
    references = skill_root / "references"
    references.mkdir(parents=True)
    (skill_root / "SKILL.md").write_text(
        "---\n"
        "name: legal-plain-explanation\n"
        "description: 将合同条款翻译成大白话。\n"
        "---\n\n"
        "严格输出原文、白话解释、实际案例。\n",
        encoding="utf-8",
    )
    (references / "contract-terms.md").write_text(
        "连带责任：可以向其中任何一方要求承担全部责任。\n",
        encoding="utf-8",
    )

    store = InMemoryDocumentStore()
    document_id = store.put(
        ParsedDocument(
            filename="示例合同.docx",
            title="示例合同",
            sections=(
                ContractSection(
                    section_id="section-1",
                    number="第八条",
                    heading="保证责任",
                    content="保证人承担连带责任。",
                ),
            ),
            blocks=(),
            table_count=0,
        )
    )
    model = BindableFakeMessagesListChatModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "id": "call-clause",
                        "name": "find_contract_clause",
                        "args": {"query": "连带责任"},
                    }
                ],
            ),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "id": "call-skill",
                        "name": "read_skill_file",
                        "args": {
                            "skill_name": "legal-plain-explanation",
                            "relative_path": "SKILL.md",
                        },
                    }
                ],
            ),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "id": "call-reference",
                        "name": "read_skill_file",
                        "args": {
                            "skill_name": "legal-plain-explanation",
                            "relative_path": "references/contract-terms.md",
                        },
                    }
                ],
            ),
            AIMessage(content="最终三段式解释"),
        ]
    )
    graph = build_chat_graph(model, store, SkillRegistry(tmp_path))

    result = graph.invoke(
        {
            "messages": [HumanMessage(content="连带责任是什么意思？")],
            "copilotkit": {
                "context": [
                    {
                        "description": "当前对话中用户已上传的合同",
                        "value": json.dumps({"document_id": document_id}),
                    }
                ]
            },
        },
        {
            "configurable": {"thread_id": "tool-thread"},
            "recursion_limit": 12,
        },
    )

    tool_messages = [
        message for message in result["messages"] if isinstance(message, ToolMessage)
    ]
    assert len(tool_messages) == 3
    assert "保证人承担连带责任" in tool_messages[0].content
    assert "严格输出原文" in tool_messages[1].content
    assert "可以向其中任何一方" in tool_messages[2].content
    assert result["messages"][-1].content == "最终三段式解释"
```

- [ ] **步骤 3：运行并确认当前图无法执行工具**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_agent.py tests\test_agent_tools.py -q
```

预期：因 `build_chat_graph` 参数或工具循环尚未实现而失败。

- [ ] **步骤 4：实现动态系统提示和工具循环**

将 `app/agent.py` 改为以下完整结构：

```python
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode
from typing import Any
from typing_extensions import NotRequired

from app.documents.store import DocumentStore
from app.skills.registry import SkillRegistry
from app.tools.contract import create_contract_tools
from app.tools.skill import create_skill_tools


BASE_SYSTEM_PROMPT = """你是一个简洁、可靠的助手。

涉及用户上传合同的具体内容时：
1. 必须先调用合同工具取得原文，没有工具证据不得编造合同内容。
2. 当用户意图命中某个 Skill 时，先用 read_skill_file 读取该 Skill 的 SKILL.md。
3. 根据 SKILL.md 的按需加载规则读取必要 reference，不得一次读取所有 reference。
4. 工具返回错误时，向用户说明如何恢复，不要掩盖错误。
5. 条款工具返回多个可靠候选时，先列出编号和标题请用户确认，不得擅自选一个解释。

{skill_catalog}
"""


class AgentState(MessagesState):
    copilotkit: NotRequired[dict[str, Any]]


def build_chat_graph(
    model: BaseChatModel,
    document_store: DocumentStore,
    skill_registry: SkillRegistry,
    checkpointer: BaseCheckpointSaver | None = None,
) -> CompiledStateGraph:
    tools = [
        *create_contract_tools(document_store),
        *create_skill_tools(skill_registry),
    ]
    tool_node = ToolNode(tools)
    model_with_tools = model.bind_tools(tools)
    system_prompt = BASE_SYSTEM_PROMPT.format(
        skill_catalog=skill_registry.catalog_prompt()
    )

    def call_model(state: AgentState) -> dict[str, list]:
        response = model_with_tools.invoke(
            [SystemMessage(content=system_prompt), *state["messages"]]
        )
        return {"messages": [response]}

    def should_continue(state: AgentState) -> str:
        last_message = state["messages"][-1]
        return "tools" if getattr(last_message, "tool_calls", None) else END

    builder = StateGraph(AgentState)
    builder.add_node("model", call_model)
    builder.add_node("tools", tool_node)
    builder.add_edge(START, "model")
    builder.add_conditional_edges("model", should_continue, ["tools", END])
    builder.add_edge("tools", "model")
    return builder.compile(checkpointer=checkpointer or MemorySaver())
```

`AgentState` 扩展 `MessagesState` 是为了保留 AG-UI 合并进来的 `copilotkit.context`；如果仍使用原来的 `MessagesState`，工具就可能看不到前端注册的当前合同。

- [ ] **步骤 5：在 `create_app` 中只组装一次 Store、Registry 和 Graph**

调整 `app/main.py`：

```python
from pathlib import Path

from app.config import get_settings
from app.skills.registry import SkillRegistry


def create_app(
    model: BaseChatModel | None = None,
    document_store: DocumentStore | None = None,
    skill_registry: SkillRegistry | None = None,
) -> FastAPI:
    settings = get_settings()
    resolved_model = model or create_chat_model(settings)
    resolved_store = document_store or InMemoryDocumentStore()
    resolved_registry = skill_registry or SkillRegistry(settings.skills_root)
    graph = build_chat_graph(
        resolved_model,
        resolved_store,
        resolved_registry,
    )
    agent = LangGraphAgent(
        name=AGENT_ID,
        description="A local streaming chat agent.",
        graph=graph,
        config={"recursion_limit": 12},
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

    fastapi_app.include_router(create_documents_router(resolved_store))
    add_langgraph_fastapi_endpoint(fastapi_app, agent, path="/agent")
    return fastapi_app
```

关键点：上传接口与 Agent 必须拿到同一个 `resolved_store` 实例，否则上传成功后工具会在另一个空 Store 中查不到合同。

- [ ] **步骤 6：更新第一阶段接口测试使用可绑定假模型**

把 `tests/test_health.py`、`tests/test_ag_ui.py` 中的 `FakeListChatModel` 替换为 `BindableFakeListChatModel`。为避免测试读取你电脑上的公司 Skill，让相关测试接收 pytest 的 `tmp_path`，并统一这样创建应用：

```python
app = create_app(
    model=BindableFakeListChatModel(responses=["hello"]),
    document_store=InMemoryDocumentStore(),
    skill_registry=SkillRegistry(tmp_path),
)
```

`tests/test_health.py` 的假模型响应仍使用空列表；`tests/test_agent.py` 则直接把 `InMemoryDocumentStore()` 和 `SkillRegistry(tmp_path)` 传入 `build_chat_graph`。这样自动化测试完全不依赖本机 `.env` 中的 `SKILLS_ROOT`。

- [ ] **步骤 7：运行工具循环、原有对话和全量测试**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_agent_tools.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_agent.py tests\test_health.py tests\test_ag_ui.py -q
.\.venv\Scripts\python.exe -m pytest -q
```

- [ ] **步骤 8：提交 LangGraph 工具循环**

```powershell
git add app/agent.py app/main.py tests/fakes.py tests/test_agent.py tests/test_agent_tools.py tests/test_health.py tests/test_ag_ui.py
git diff --cached --check
git commit -m "feat: execute contract skills through LangGraph tools"
```

---

### 任务 8：验证工具事件能够穿过 AG-UI

**它位于链路哪里：** 协议层，连接 Python LangGraph 与浏览器 CopilotKit。

**完成后能看到：** `/agent` 的 SSE 响应中不仅有最终文本，还出现 `find_contract_clause` 的工具调用和工具结果事件。

**为什么单独验证：** 后端图内部能执行工具，不代表 AG-UI 一定把事件正确传给前端。分层测试可以明确故障发生在 Agent 还是协议适配器。

**学习级别：**

- **必须掌握：** 工具在后端执行，AG-UI 负责把过程事件传给前端。
- **熟悉即可：** SSE 是持续返回多条事件的 HTTP 响应。
- **了解即可：** 每种 AG-UI 事件的完整字段。

**文件：**

- 修改：`tests/test_ag_ui.py`

**接口：**

- 验证：`POST /agent` 保持 `text/event-stream`
- 验证：工具名称、参数、结果和最终文本出现在事件流。

- [ ] **步骤 1：增加工具事件集成测试**

在 `tests/test_ag_ui.py` 增加导入：

```python
import json

from langchain_core.messages import AIMessage

from app.documents.models import ContractSection, ParsedDocument
from app.documents.store import InMemoryDocumentStore
from app.skills.registry import SkillRegistry
from tests.fakes import BindableFakeMessagesListChatModel
```

再增加完整测试：

```python
def test_agent_endpoint_streams_contract_tool_events(tmp_path) -> None:
    store = InMemoryDocumentStore()
    document_id = store.put(
        ParsedDocument(
            filename="示例合同.docx",
            title="示例合同",
            sections=(
                ContractSection(
                    section_id="section-1",
                    number="第八条",
                    heading="保证责任",
                    content="保证人承担连带责任。",
                ),
            ),
            blocks=(),
            table_count=0,
        )
    )
    model = BindableFakeMessagesListChatModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "id": "call-clause",
                        "name": "find_contract_clause",
                        "args": {"query": "连带责任"},
                    }
                ],
            ),
            AIMessage(content="这是最终解释"),
        ]
    )
    app = create_app(
        model=model,
        document_store=store,
        skill_registry=SkillRegistry(tmp_path),
    )
    payload = {
        "threadId": "thread-tool",
        "runId": "run-tool",
        "state": {},
        "messages": [
            {
                "id": "user-1",
                "role": "user",
                "content": "连带责任是什么意思？",
            }
        ],
        "tools": [],
        "context": [
            {
                "description": "当前对话中用户已上传的合同",
                "value": json.dumps({"document_id": document_id}),
            }
        ],
        "forwardedProps": {},
    }

    with TestClient(app).stream("POST", "/agent", json=payload) as response:
        body = "".join(response.iter_text())

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "find_contract_clause" in body
    assert "连带责任" in body
    assert "这是最终解释" in body
    assert '"type":"RUN_FINISHED"' in body
```

- [ ] **步骤 2：运行协议测试**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_ag_ui.py -q
```

如果只缺少某个事件字符串，先打印测试中的 `body` 并以当前 `ag-ui-langgraph==0.0.42` 实际输出为准，不为了匹配旧文档硬编码不存在的事件名。

- [ ] **步骤 3：运行全量测试并提交**

```powershell
.\.venv\Scripts\python.exe -m pytest -q
git add tests/test_ag_ui.py
git diff --cached --check
git commit -m "test: cover AG-UI contract tool events"
```

---

### 任务 9：增加 Next.js 同源上传代理

**它位于链路哪里：** 前端服务端边界。浏览器把 Word 发给 Next.js，Next.js 再转发到 FastAPI；它与现有 `/api/copilotkit` Runtime 并列。

**完成后能看到：** 前端开发服务器运行时，向 `http://localhost:3000/api/documents` 上传文件，会得到 Python 后端 `/documents` 的原样状态码和 JSON。

**为什么这样做：** 浏览器只访问一个来源 `localhost:3000`，后端地址保留在服务端环境变量中；以后后端换地址也不用改 React 代码。

**学习级别：**

- **必须掌握：** Next.js 路由是代理，不解析合同、不调用模型。
- **熟悉即可：** `FormData`、`fetch`、HTTP 状态码转发。
- **了解即可：** Next.js Route Handler 的运行时实现。

**文件：**

- 新建：`src/app/api/documents/route.ts`
- 修改：`.env.local.example`

**接口：**

- 消费：FastAPI `POST http://127.0.0.1:8000/documents`
- 产出：Next.js `POST /api/documents`

- [ ] **步骤 1：扩展前端环境变量模板**

在 `.env.local.example` 中保留 `AGENT_URL`，并增加：

```dotenv
BACKEND_URL=http://127.0.0.1:8000
```

`AGENT_URL` 指向 AG-UI Agent 接口；`BACKEND_URL` 指向 FastAPI 服务根地址，用于上传。这两个变量职责不同，不要从字符串中截取 `/agent` 来猜根地址。

- [ ] **步骤 2：实现上传代理**

新建 `src/app/api/documents/route.ts`：

```typescript
const backendUrl = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";

export async function POST(request: Request) {
  try {
    const formData = await request.formData();
    const response = await fetch(`${backendUrl}/documents`, {
      method: "POST",
      body: formData,
      cache: "no-store",
    });
    const body = await response.text();

    return new Response(body, {
      status: response.status,
      headers: {
        "content-type":
          response.headers.get("content-type") ?? "application/json",
      },
    });
  } catch {
    return Response.json(
      { detail: "无法连接合同解析服务，请确认 Python 后端已经启动" },
      { status: 502 },
    );
  }
}
```

不要手动设置 multipart 的 `content-type`；`fetch` 会根据新的 `FormData` 自动生成带 boundary 的正确请求头。

- [ ] **步骤 3：运行静态检查和构建**

在 VS Code 前端终端运行：

```powershell
Set-Location D:\code\aiagent\0824_langchain\frontend
npm.cmd run lint
npm.cmd run build
```

命令解释：`lint` 检查 TypeScript/React 写法；`build` 会实际编译 Next.js 路由并做类型检查。两条都通过才说明代理文件是一个有效模块。

- [ ] **步骤 4：同时启动后端与前端，手工验证代理**

PyCharm 后端终端：

```powershell
Set-Location D:\code\aiagent\0824_langchain\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

VS Code 前端终端：

```powershell
Set-Location D:\code\aiagent\0824_langchain\frontend
Copy-Item .env.local.example .env.local
npm.cmd run dev
```

两个命令都需要持续运行，分别占用一个终端。`Copy-Item` 只在 `.env.local` 不存在时执行；如果已经存在，只补上 `BACKEND_URL`，不要覆盖自己的现有配置。

另开一个 PowerShell，使用获准测试的 Word 路径：

```powershell
$contractPath = "D:\你的脱敏测试目录\示例合同.docx"
curl.exe -X POST -F "file=@$contractPath" http://localhost:3000/api/documents
```

命令解释：`curl.exe -F` 模拟浏览器的 multipart 上传。预期返回包含 `document_id`、`filename` 和 `section_count` 的 JSON。不要把合同内容或路径加入 Git。

- [ ] **步骤 5：提交前端代理**

```powershell
git add .env.local.example src/app/api/documents/route.ts
git diff --cached --check
git commit -m "feat: proxy contract uploads to backend"
```

---

### 任务 10：在聊天页增加上传区并注册当前合同 Context

**它位于链路哪里：** 浏览器交互层。它把用户选择的 Word 变成 `document_id`，再把这个编号随每次 CopilotKit Agent 运行传给后端。

**完成后能看到：** 聊天区上方出现上传按钮；上传中显示进度文字；成功后显示文件名和条款数；询问条款时 Agent 能找到当前合同；清空对话后合同状态也消失。

**为什么这样做：** 上传成功只代表后端保存了合同，Agent 还不知道“当前对话对应哪一份”。`useAgentContext` 就是两条链路之间的桥。

**学习级别：**

- **必须掌握：** React state 保存页面当前合同，`useAgentContext` 把 `document_id` 送入 Agent 上下文。
- **熟悉即可：** 事件处理、`FormData`、条件渲染、联合类型。
- **了解即可：** CopilotKit Context Store 的内部订阅机制。
- **可以借助文档/AI：** CSS、按钮排版和重复的 TypeScript 类型缩窄。

**文件：**

- 修改：`src/app/page.tsx`
- 修改：`src/app/globals.css`

**接口：**

- 消费：`POST /api/documents`
- 产出：CopilotKit Context description 固定为 `当前对话中用户已上传的合同`
- 产出：Context value 为 `{document_id, filename}`

- [ ] **步骤 1：先定义页面状态和上传响应类型**

在 `src/app/page.tsx` 增加 React 与 CopilotKit 导入：

```typescript
import { useState, type ChangeEvent } from "react";
import {
  CopilotChat,
  CopilotKit,
  useAgentContext,
  useCopilotChatConfiguration,
} from "@copilotkit/react-core/v2";
```

在组件前定义：

```typescript
type UploadedDocument = {
  document_id: string;
  filename: string;
  section_count: number;
  table_count: number;
  warnings: string[];
};

type UploadState =
  | { status: "idle"; error: null }
  | { status: "uploading"; error: null }
  | { status: "error"; error: string };
```

`currentDocument` 与上传过程分开保存：更换合同失败时仍保留原合同，只有新上传成功后才替换 `document_id`。

- [ ] **步骤 2：增加只在有合同后挂载的 Context 组件**

在 `ChatWorkspace` 前增加：

```tsx
function CurrentDocumentContext({
  document,
}: {
  document: UploadedDocument;
}) {
  useAgentContext({
    description: "当前对话中用户已上传的合同",
    value: {
      document_id: document.document_id,
      filename: document.filename,
    },
  });

  return null;
}
```

它不画任何 UI，只向 CopilotKit 注册 Context。把它写成独立组件，是因为 React Hook 不能在 `if` 语句中直接调用；父组件可以根据是否有合同决定要不要挂载整个子组件。

- [ ] **步骤 3：在 `ChatWorkspace` 中实现上传状态与请求**

在 `ChatWorkspace` 开头增加：

```tsx
const [currentDocument, setCurrentDocument] =
  useState<UploadedDocument | null>(null);
const [uploadState, setUploadState] = useState<UploadState>({
  status: "idle",
  error: null,
});

async function handleDocumentUpload(event: ChangeEvent<HTMLInputElement>) {
  const file = event.target.files?.[0];
  if (!file) return;
  if (!file.name.toLowerCase().endsWith(".docx")) {
    setUploadState({ status: "error", error: "仅支持 .docx Word 文件" });
    return;
  }
  if (file.size > 10 * 1024 * 1024) {
    setUploadState({ status: "error", error: "文件不能超过 10 MiB" });
    return;
  }

  setUploadState({ status: "uploading", error: null });
  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch("/api/documents", {
      method: "POST",
      body: formData,
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail ?? "合同上传失败");
    }
    setCurrentDocument(payload as UploadedDocument);
    setUploadState({ status: "idle", error: null });
  } catch (error) {
    setUploadState({
      status: "error",
      error: error instanceof Error ? error.message : "合同上传失败",
    });
  } finally {
    event.target.value = "";
  }
}
```

前端扩展名和大小校验用于即时反馈，后端仍必须重复校验，因为浏览器输入不能作为安全边界。

- [ ] **步骤 4：让清空对话同时清除合同 Context**

把原来的清空按钮处理改为：

```tsx
function handleStartNewThread() {
  setCurrentDocument(null);
  setUploadState({ status: "idle", error: null });
  chatConfiguration?.startNewThread();
}
```

按钮使用：

```tsx
onClick={handleStartNewThread}
```

如果只清空聊天、不清空合同，新线程可能继续引用旧 `document_id`，用户会误以为自己在一个完全新的会话中。

- [ ] **步骤 5：在聊天区上方渲染上传状态**

把 `<main className="chat-region">` 调整为包含上传区和聊天区：

```tsx
<main className="workspace-region">
  {currentDocument && (
    <CurrentDocumentContext document={currentDocument} />
  )}

  <section className="document-bar" aria-label="当前合同">
    <div>
      <strong>
        {currentDocument ? currentDocument.filename : "尚未上传合同"}
      </strong>
      <p>
        {uploadState.status === "uploading" && "正在上传并解析 Word…"}
        {uploadState.status === "error" && uploadState.error}
        {uploadState.status === "idle" && currentDocument &&
          `已识别 ${currentDocument.section_count} 个条款、${currentDocument.table_count} 个表格`}
        {uploadState.status === "idle" && !currentDocument &&
          "上传一份虚构或脱敏的 .docx 后，可以询问具体条款。"}
      </p>
    </div>
    <label className="upload-button">
      {currentDocument ? "更换合同" : "上传 Word 合同"}
      <input
        type="file"
        accept=".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        onChange={handleDocumentUpload}
        disabled={uploadState.status === "uploading"}
      />
    </label>
  </section>

  <div className="chat-region">
    <CopilotChat
      agentId="local_chat"
      className="chat"
      labels={{
        modalHeaderTitle: "本地对话智能体",
        welcomeMessageText:
          "你好，上传一份脱敏 Word 合同后，可以询问具体条款。",
      }}
    />
  </div>
</main>
```

页面最外层仍保留现有 `<CopilotKit runtimeUrl="/api/copilotkit" agent="local_chat" useSingleEndpoint={false}>`，只在它内部替换 `ChatWorkspace` 的内容，不重写第一阶段 Runtime。

- [ ] **步骤 6：增加最小样式**

在 `src/app/globals.css` 中调整主网格并增加：

```css
.workspace-region {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  min-width: 0;
  min-height: 0;
}

.document-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 20px;
  border-bottom: 1px solid var(--border);
  background: #f8fbfa;
}

.document-bar p {
  margin: 4px 0 0;
  color: var(--muted);
  font-size: 13px;
}

.upload-button {
  flex: 0 0 auto;
  padding: 8px 12px;
  color: white;
  background: var(--accent);
  border-radius: 6px;
  cursor: pointer;
}

.upload-button input {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}

.chat-region,
.chat {
  min-width: 0;
  min-height: 0;
  height: 100%;
}

@media (max-width: 640px) {
  .document-bar {
    align-items: stretch;
    flex-direction: column;
    padding-inline: 14px;
  }

  .upload-button {
    align-self: flex-start;
  }
}
```

- [ ] **步骤 7：运行前端静态验证**

```powershell
npm.cmd run lint
npm.cmd run build
```

如果出现 Hook 或 TypeScript 错误，先修正再继续；不要使用 `any` 或关闭 ESLint 规则绕过。

- [ ] **步骤 8：浏览器验证四种状态和清空联动**

保持 Python 后端与 Next.js 前端运行，打开：

[http://localhost:3000](http://localhost:3000)

依次验证：

1. 初始显示“尚未上传合同”。
2. 选择 `.txt` 显示格式错误。
3. 上传获准测试的 `.docx` 后显示文件名、条款数和表格数。
4. 点击清空对话后页面回到“尚未上传合同”。
5. 浏览器 Network 中聊天请求的 `context` 含 `document_id`，但不含合同全文。

- [ ] **步骤 9：提交前端上传交互**

```powershell
git add src/app/page.tsx src/app/globals.css
git diff --cached --check
git commit -m "feat: attach uploaded contract to chat context"
```

---

### 任务 11：完成真实模型验收、文档和 GitHub 交付

**它位于链路哪里：** 端到端验收与交付层。前面的局部能力在这里第一次用真实公司模型连成用户可演示的功能。

**完成后能看到：** 上传脱敏合同后，询问条款会显示工具调用过程并得到符合公司 Skill 的三段式回答；两个仓库测试通过并推送独立分支供带教审查。

**为什么最后才用真实模型：** 真实模型调用受网络、权限和模型工具能力影响。先完成确定性自动测试，最后失败时才能准确定位是模型接口还是项目代码。

**学习级别：**

- **必须掌握：** 如何按层定位问题，并能向带教讲清完整数据流。
- **熟悉即可：** README、Git commit、push 和 PR 的交付作用。
- **了解即可：** 生产环境文件存储、审计和法律评测体系。

**文件：**

- 修改：后端 `README.md`
- 修改：前端 `README.md`

**接口：**

- 验收整条链路：`.docx → document_id → Context → tools → Skill → AG-UI → CopilotKit`

- [ ] **步骤 1：运行后端最终自动化验证**

在 PyCharm 后端终端运行：

```powershell
Set-Location D:\code\aiagent\0824_langchain\backend
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
```

预期：全部测试通过，依赖无冲突。记录实际测试数量，不提前在文档中写死。

- [ ] **步骤 2：运行前端最终自动化验证**

在 VS Code 前端终端运行：

```powershell
Set-Location D:\code\aiagent\0824_langchain\frontend
npm.cmd run lint
npm.cmd run build
```

预期：两条命令退出码均为 0。

- [ ] **步骤 3：启动两个服务**

PyCharm：

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

VS Code：

```powershell
npm.cmd run dev
```

后端 `.env` 必须配置已验证支持工具调用的公司 OpenAI 兼容模型；不要在截图或聊天中展示密钥。

- [ ] **步骤 4：执行六个手工验收场景**

使用一份获准测试、含“付款”“违约责任”“连带责任”等内容的虚构或脱敏合同：

1. 上传成功：页面显示文件名与解析摘要。
2. 编号定位：询问“第八条是什么意思？”回答原文来自第八条。
3. 术语定位：询问“连带责任用大白话怎么讲？”看到合同工具、`read_skill_file` 和三段式回答。
4. 找不到：询问合同没有的“自动续约”，Agent 明确说未找到，不编造。
5. 越界问题：询问“我该不该签？”，Agent 不给行动建议，但可以解释相关术语。
6. 普通聊天：询问“你好”，不触发合同工具。

合格回答必须包含：

```text
📋 原文
💬 白话解释
📖 实际案例
以上是通俗解释，具体法律问题请咨询执业律师。
```

如果模型没有调用工具，先检查模型是否支持 OpenAI 风格 `tool_calls`，再检查系统提示和工具描述；不要先怀疑前端卡片。

- [ ] **步骤 5：验证文档失效降级**

上传合同后停止并重启 Python 后端，再询问原合同条款。预期 Agent 提示临时合同已失效、需要重新上传。这验证第一版“内存临时存储”的边界已经诚实暴露给用户。

- [ ] **步骤 6：更新两个 README**

后端 README 增加：

- 新依赖安装方式仍为 `pip install -r requirements-dev.txt`。
- `SKILLS_ROOT` 的作用和本地配置示例。
- `POST /documents`、10 MiB 和 `.docx` 限制。
- 三个工具的职责。
- Skill 渐进加载流程。
- 测试命令和隐私边界。

前端 README 增加：

- `BACKEND_URL` 与 `AGENT_URL` 的区别。
- 页面上传、替换合同和清空对话行为。
- 前后端同时启动的顺序。
- 不上传真实或未授权合同。

- [ ] **步骤 7：提交后端文档与最终检查**

```powershell
Set-Location D:\code\aiagent\0824_langchain\backend
git status --short
git diff --check
git add README.md
git diff --cached --name-status
git commit -m "docs: explain contract skill workflow"
git status --short --branch
```

检查暂存清单中没有 `.env`、`.docx`、`uploads/`、`local-contracts/` 或第一阶段无关文件。

- [ ] **步骤 8：提交前端文档与最终检查**

```powershell
Set-Location D:\code\aiagent\0824_langchain\frontend
git status --short
git diff --check
git add README.md
git diff --cached --name-status
git commit -m "docs: explain contract upload workflow"
git status --short --branch
```

- [ ] **步骤 9：推送两个第二阶段分支**

后端：

```powershell
git push -u origin feat/legal-explanation
```

前端：

```powershell
git push -u origin feat/legal-explanation
```

命令解释：`push` 才把本地提交分享给 GitHub；`-u` 建立本地分支与同名远程分支的跟踪关系。推送不等于合并 `main`。

- [ ] **步骤 10：创建 PR 并向带教说明真实完成范围**

两个仓库分别创建从 `feat/legal-explanation` 到带教指定基线分支的 PR。PR 描述包括：

```text
已完成：
- .docx 上传、解析与进程内临时存储
- document_id 对话上下文
- 合同目录和条款定位工具
- Skill name/description 预加载与按需 read_skill_file
- LangGraph model→tools→model 循环
- AG-UI/CopilotKit 端到端展示

当前边界：
- 单会话单合同
- 仅支持 .docx
- 仅使用脱敏或虚构测试数据
- 不包含预审、深度审查、RAG、数据库和生产 CLM 接口

验证：
- 后端 pytest 全部通过
- 前端 lint/build 通过
- 六个手工场景通过
```

不要自行把 PR 合并到 `main`，等待带教审查和下一步要求。

## 教学陪跑执行约定

执行本计划时，每次只推进一个“小循环”，不要一次复制整项任务：

1. 我先解释当前步骤位于哪条链路、完成后看到什么、为什么要做。
2. 我解释本步文件职责和陌生语法，不要求你机械背诵框架样板。
3. 你在 PyCharm 或 VS Code 中亲手写当前小段代码。
4. 我解释命令的目录、用途和预期结果后，你亲手运行。
5. 你把实际输出发回来，我们依据证据继续或排错。
6. 每个任务结束时，你用自己的话复述一次输入、输出和数据流。
7. 测试和提交通过后再进入下一任务。

学习重点始终保持：

- **必须掌握：** `document_id`、Word 结构化、Tool 契约、`model → tools → model`、Skill 渐进加载和证据引用。
- **熟悉即可：** FastAPI 上传、`ToolRuntime`、AG-UI Context、React state 与 `useAgentContext`。
- **了解即可：** Word XML、SSE 事件细节、Next.js Route Handler 内部实现。
- **可以借助文档/AI：** CSS、TypeScript 框架胶水、重复测试数据和 README 排版。
