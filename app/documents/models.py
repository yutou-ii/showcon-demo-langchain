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