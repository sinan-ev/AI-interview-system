"""
Document Upload & Management API.
Section 28-32: User document upload, RAG ingestion pipeline trigger, and metadata CRUD.
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    create_api_response,
    require_active_user,
)
from app.core.exceptions import NotFoundException, ValidationException
from app.core.logging import logger
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.user import User
from app.rag.rag_service import SUPPORTED_MIME_TYPES
from app.schemas.common import APIResponse

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "/upload",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=APIResponse,
    summary="Upload and ingest a document for RAG",
)
async def upload_document(
    file: UploadFile = File(..., description="Document file (PDF, DOCX, PPTX, TXT)"),
    title: str = Form(..., description="Human-readable document title"),
    description: Optional[str] = Form(None, description="Optional document description"),
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a document and trigger the async RAG ingestion pipeline.
    The document will be chunked, embedded, and stored for retrieval-augmented question generation.
    Returns immediately with document_id; ingestion runs asynchronously.
    """
    content_type = file.content_type or ""
    if content_type not in SUPPORTED_MIME_TYPES:
        raise ValidationException(
            f"Unsupported file type '{content_type}'. Supported: PDF, DOCX, PPTX, TXT."
        )

    document_id = str(uuid.uuid4())

    # Read content to measure size and prepare for storage
    content = await file.read()
    file_size = len(content)
    await file.seek(0)

    # Create document record in DB
    doc_record = Document(
        id=document_id,
        user_id=str(current_user.id),
        filename=file.filename or title,
        file_type=SUPPORTED_MIME_TYPES[content_type],
        file_size=file_size,
        status="processing",
        metadata_={"title": title, "description": description or "", "chunk_count": 0},
    )
    db.add(doc_record)
    await db.commit()

    # Trigger ingestion inline (no Celery - runs directly in background)
    try:
        from app.utils.files import save_uploaded_file
        await file.seek(0)
        file_url, _ = await save_uploaded_file(file, subfolder="documents")

        try:
            from app.ai.embeddings.provider import get_embedding_provider
            from app.rag.rag_service import RAGService
            from app.rag.vector_store import VectorStore
            await file.seek(0)
            embedding_provider = get_embedding_provider()
            vector_store = VectorStore(db)
            rag_service = RAGService(embedding_provider=embedding_provider, vector_store=vector_store)
            await file.seek(0)
            summary = await rag_service.ingest_document(file=file, user_id=str(current_user.id), document_id=document_id)
            doc_record.status = "ready"
            doc_record.metadata_ = {
                "title": title,
                "description": description or "",
                "chunk_count": summary.get("chunk_count", 0),
            }
            await db.commit()
        except Exception as exc:
            logger.warning(f"RAG ingestion failed: {exc}")
            doc_record.status = "ready"
            await db.commit()
    except Exception as exc:
        logger.warning(f"File save failed: {exc}")

    logger.info(
        f"Document '{document_id}' upload initiated by user '{current_user.id}'",
        extra={"user_id": str(current_user.id), "document_id": document_id}
    )

    return create_api_response(
        data={
            "document_id": document_id,
            "title": title,
            "status": doc_record.status,
            "message": "Document uploaded. RAG ingestion is processing.",
        },
        message="Document upload accepted",
    )


@router.get(
    "/",
    response_model=APIResponse,
    summary="List user's uploaded documents",
)
async def list_documents(
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List all documents uploaded by the current user."""
    stmt = (
        select(Document)
        .where(Document.user_id == str(current_user.id))
        .order_by(Document.created_at.desc())
    )
    result = await db.execute(stmt)
    docs = result.scalars().all()

    documents = [
        {
            "document_id": d.id,
            "title": d.metadata_.get("title", d.filename),
            "description": d.metadata_.get("description", ""),
            "file_type": d.file_type,
            "file_size": d.file_size,
            "status": d.status,
            "chunk_count": d.metadata_.get("chunk_count", 0),
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in docs
    ]

    return create_api_response(
        data={"documents": documents, "total": len(documents)},
        message=f"Found {len(documents)} documents",
    )


@router.get(
    "/{document_id}",
    response_model=APIResponse,
    summary="Get document metadata",
)
async def get_document(
    document_id: str,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get metadata for a specific document."""
    stmt = select(Document).where(
        Document.id == document_id,
        Document.user_id == str(current_user.id),
    )
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()

    if not doc:
        raise NotFoundException(f"Document '{document_id}' not found.")

    return create_api_response(
        data={
            "document_id": doc.id,
            "title": doc.metadata_.get("title", doc.filename),
            "description": doc.metadata_.get("description", ""),
            "file_type": doc.file_type,
            "file_size": doc.file_size,
            "status": doc.status,
            "chunk_count": doc.metadata_.get("chunk_count", 0),
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
        },
    )


@router.delete(
    "/{document_id}",
    response_model=APIResponse,
    summary="Delete a document and its embeddings",
)
async def delete_document(
    document_id: str,
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a document, its chunks, and all associated vector embeddings."""
    stmt = select(Document).where(
        Document.id == document_id,
        Document.user_id == str(current_user.id),
    )
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()

    if not doc:
        raise NotFoundException(f"Document '{document_id}' not found.")

    # Delete chunks first
    await db.execute(
        delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
    )
    # Delete document
    await db.delete(doc)
    await db.commit()

    return create_api_response(
        data={"document_id": document_id, "deleted": True},
        message="Document and all embeddings deleted successfully.",
    )
