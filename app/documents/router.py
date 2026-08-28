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