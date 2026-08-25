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