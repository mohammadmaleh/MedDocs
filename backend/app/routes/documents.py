from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Document, User
from app.schemas import DocumentResponse
from app.services.document_processor import (
    chunk_text,
    embed_and_store,
    extract_text_from_pdf,
)
from app.services.keyword_service import check_keyword

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_bytes = await file.read()
    text_list = extract_text_from_pdf(file_bytes=file_bytes)

    text = " ".join([item["text"] for item in text_list])

    all_flags = []
    for item in text_list:
      all_flags += check_keyword(text=item["text"], page_number=item["page_number"])

    chunks = chunk_text(text=text)
    document = Document(
        filename=file.filename,
        original_text=text,
        user_id=current_user.id,
        flags=all_flags,
        status="processing",
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    embed_and_store(doc_id=document.id, chunks=chunks, user_id=current_user.id)

    document.status = "done"
    db.commit()
    db.refresh(document)
    return {"id": document.id, "filename": document.filename, "chunks": len(chunks)}


@router.get("/", status_code=200, response_model=list[DocumentResponse])
async def get_documents(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):

    document = db.query(Document).filter(Document.user_id == current_user.id).all()

    return list(document)


@router.get("/{id}", status_code=200, response_model=DocumentResponse)
async def get_document_by_id(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = (
        db.query(Document)
        .filter(Document.id == id, Document.user_id == current_user.id)
        .first()
    )
    if document is None:
        raise HTTPException(status_code=404, detail="Document was not found")
    return document
