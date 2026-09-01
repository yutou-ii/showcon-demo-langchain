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
        """列出当前已上传合同的条款编号和标题， 不返回整份合同正文。"""
        try:
            document = current_document(runtime)
        except MissingDocumentContextError as error:
            return {"error": "document_not_found", "message": str(error)}
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
            return {"error": "document_not_fount", "message": str(error)}
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
