import json
from typing import Any


CURRENT_DOCUMENT_CONTEXT = "当前对话中用户已上传的合同"


class MissingDocumentContextError(ValueError):
    pass


def extract_current_document_id(state: dict[str, Any]) -> str:
    ag_ui = state.get("ag-ui") or {}
    for item in ag_ui.get("context") or []:
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
