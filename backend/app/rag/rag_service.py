"""
RAG Service.
Section 28-32: Orchestrates document ingestion, embedding, and retrieval-augmented generation.
"""
import uuid
from typing import List, Optional

from fastapi import UploadFile

from app.ai.embeddings.provider import EmbeddingProvider
from app.core.exceptions import NotFoundException, ValidationException
from app.core.logging import logger
from app.rag.document_processor import DocumentChunk, DocumentProcessor
from app.rag.vector_store import VectorSearchResult, VectorStore


SUPPORTED_MIME_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
    "text/plain": "txt",
    "text/markdown": "txt",
}

MAX_DOCUMENT_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB


class RAGService:
    """
    RAG orchestration service: handles upload → extract → chunk → embed → store → retrieve pipeline.
    """

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
        document_processor: Optional[DocumentProcessor] = None,
    ):
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store
        self.processor = document_processor or DocumentProcessor()

    async def ingest_document(
        self,
        file: UploadFile,
        user_id: str,
        document_id: Optional[str] = None,
    ) -> dict:
        """
        Full RAG ingestion pipeline:
        1. Validate file type and size
        2. Extract raw text
        3. Chunk with overlap
        4. Embed each chunk
        5. Persist embeddings to vector store
        Returns a summary dict with document_id and chunk count.
        """
        # --- Validate ---
        content_type = file.content_type or ""
        file_extension = SUPPORTED_MIME_TYPES.get(content_type)
        if not file_extension:
            raise ValidationException(
                f"Unsupported file type '{content_type}'. "
                f"Supported: {list(SUPPORTED_MIME_TYPES.keys())}"
            )

        file_bytes = await file.read()
        if len(file_bytes) > MAX_DOCUMENT_SIZE_BYTES:
            raise ValidationException(
                f"File size {len(file_bytes)} exceeds maximum allowed {MAX_DOCUMENT_SIZE_BYTES} bytes."
            )

        doc_id = document_id or str(uuid.uuid4())

        # --- Extract Text ---
        try:
            if file_extension == "pdf":
                text = self.processor.extract_text_from_pdf(file_bytes)
            elif file_extension == "docx":
                text = self.processor.extract_text_from_docx(file_bytes)
            elif file_extension == "pptx":
                text = self.processor.extract_text_from_pptx(file_bytes)
            else:
                text = file_bytes.decode("utf-8", errors="replace")
        except Exception as e:
            raise ValidationException(f"Failed to extract text from document: {str(e)}")

        if not text.strip():
            raise ValidationException("Extracted document content is empty. Please upload a non-empty document.")

        # --- Chunk ---
        chunks: List[DocumentChunk] = self.processor.chunk_text(text, doc_id)
        if not chunks:
            raise ValidationException("Document could not be split into processable chunks.")

        logger.info(
            f"Ingesting document '{doc_id}' — {len(chunks)} chunks to embed",
            extra={"rag": "RAGService", "document_id": doc_id, "chunks": len(chunks)}
        )

        # --- Embed in batches ---
        batch_size = 20
        embedded_count = 0

        for batch_start in range(0, len(chunks), batch_size):
            batch = chunks[batch_start: batch_start + batch_size]
            texts = [c.text for c in batch]

            try:
                embeddings = await self.embedding_provider.embed_batch(texts)
            except Exception as e:
                logger.error(f"Embedding batch {batch_start}-{batch_start + len(batch)} failed: {str(e)}")
                raise

            for chunk, embedding in zip(batch, embeddings):
                await self.vector_store.upsert_chunk_embedding(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    text=chunk.text,
                    chunk_index=chunk.chunk_index,
                    embedding=embedding,
                    user_id=user_id,
                )
                embedded_count += 1

        logger.info(
            f"Document '{doc_id}' fully ingested: {embedded_count}/{len(chunks)} chunks embedded",
            extra={"rag": "RAGService", "document_id": doc_id, "embedded_chunks": embedded_count}
        )

        return {
            "document_id": doc_id,
            "chunk_count": len(chunks),
            "embedded_count": embedded_count,
            "status": "ready",
        }

    async def retrieve_context(
        self,
        query: str,
        document_ids: Optional[List[str]] = None,
        top_k: int = 5,
        min_similarity: float = 0.70,
    ) -> str:
        """
        Retrieve the most relevant chunks for a query and format them as a prompt context block.
        """
        try:
            query_embedding = await self.embedding_provider.embed_text(query)
        except Exception as e:
            logger.warning(f"Query embedding failed, returning empty context: {str(e)}")
            return "No relevant document context available."

        results: List[VectorSearchResult] = await self.vector_store.similarity_search(
            query_embedding=query_embedding,
            document_ids=document_ids,
            top_k=top_k,
            min_similarity=min_similarity,
        )

        return self.vector_store.format_context_for_prompt(results)

    async def retrieve_raw_results(
        self,
        query: str,
        document_ids: Optional[List[str]] = None,
        top_k: int = 5,
        min_similarity: float = 0.70,
    ) -> List[VectorSearchResult]:
        """Return raw VectorSearchResult objects for inspection/debugging."""
        query_embedding = await self.embedding_provider.embed_text(query)
        return await self.vector_store.similarity_search(
            query_embedding=query_embedding,
            document_ids=document_ids,
            top_k=top_k,
            min_similarity=min_similarity,
        )
