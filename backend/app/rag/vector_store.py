"""
RAG Vector Store.
Section 29-31: Similarity search using pgvector for semantic retrieval.
"""
from typing import List, Optional, Tuple
from app.core.logging import logger


class VectorSearchResult:
    """A retrieved document chunk with its similarity score."""

    def __init__(
        self,
        chunk_id: str,
        document_id: str,
        text: str,
        chunk_index: int,
        similarity_score: float,
        metadata: Optional[dict] = None,
    ):
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.text = text
        self.chunk_index = chunk_index
        self.similarity_score = similarity_score
        self.metadata = metadata or {}


class VectorStore:
    """
    pgvector-backed semantic vector store.
    Wraps raw SQLAlchemy async session for embedding upsert and cosine similarity queries.
    """

    def __init__(self, db_session):
        self.db = db_session

    async def upsert_chunk_embedding(
        self,
        chunk_id: str,
        document_id: str,
        text: str,
        chunk_index: int,
        embedding: List[float],
        user_id: str,
    ) -> None:
        """
        Persist or update a chunk's embedding in the document_chunks table.
        Uses the ORM model from app.models.document_chunk.
        """
        from sqlalchemy import text as sql_text

        # Upsert: if chunk_id already exists, update embedding; else insert
        upsert_sql = sql_text("""
            INSERT INTO document_chunks (id, document_id, text_content, chunk_index, embedding, created_at, updated_at)
            VALUES (:chunk_id, :document_id, :text, :chunk_index, :embedding, NOW(), NOW())
            ON CONFLICT (id) DO UPDATE SET
                embedding = EXCLUDED.embedding,
                updated_at = NOW()
        """)

        try:
            await self.db.execute(
                upsert_sql,
                {
                    "chunk_id": chunk_id,
                    "document_id": document_id,
                    "text": text,
                    "chunk_index": chunk_index,
                    "embedding": embedding,
                }
            )
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            logger.error(f"VectorStore upsert failed for chunk '{chunk_id}': {str(e)}")
            raise

    async def similarity_search(
        self,
        query_embedding: List[float],
        document_ids: Optional[List[str]] = None,
        top_k: int = 5,
        min_similarity: float = 0.70,
    ) -> List[VectorSearchResult]:
        """
        Retrieve top-K most semantically similar chunks via cosine similarity.
        Optionally scoped to specific document IDs (for per-interview RAG context).
        """
        from sqlalchemy import text as sql_text

        # Build dynamic filter clause
        filter_clause = ""
        params: dict = {
            "query_embedding": query_embedding,
            "top_k": top_k,
            "min_similarity": min_similarity,
        }

        if document_ids:
            # Parameterize document IDs safely
            id_placeholders = ", ".join([f":doc_id_{i}" for i in range(len(document_ids))])
            filter_clause = f"AND dc.document_id IN ({id_placeholders})"
            for i, doc_id in enumerate(document_ids):
                params[f"doc_id_{i}"] = doc_id

        query_sql = sql_text(f"""
            SELECT
                dc.id AS chunk_id,
                dc.document_id,
                dc.text_content,
                dc.chunk_index,
                1 - (dc.embedding <=> CAST(:query_embedding AS vector)) AS similarity_score
            FROM document_chunks dc
            WHERE dc.embedding IS NOT NULL
                {filter_clause}
                AND 1 - (dc.embedding <=> CAST(:query_embedding AS vector)) >= :min_similarity
            ORDER BY dc.embedding <=> CAST(:query_embedding AS vector)
            LIMIT :top_k
        """)

        try:
            result = await self.db.execute(query_sql, params)
            rows = result.fetchall()

            search_results = [
                VectorSearchResult(
                    chunk_id=str(row.chunk_id),
                    document_id=str(row.document_id),
                    text=row.text_content,
                    chunk_index=row.chunk_index,
                    similarity_score=float(row.similarity_score),
                )
                for row in rows
            ]

            logger.info(
                f"Vector search returned {len(search_results)} results (top_k={top_k}, min_sim={min_similarity})",
                extra={"rag": "VectorStore", "results_count": len(search_results)}
            )
            return search_results

        except Exception as e:
            logger.error(f"VectorStore similarity search failed: {str(e)}")
            raise

    def format_context_for_prompt(
        self,
        results: List[VectorSearchResult],
        max_chars: int = 3000,
    ) -> str:
        """
        Format retrieved chunks into a prompt-ready context block.
        Respects max_chars budget to avoid token overflow.
        """
        if not results:
            return "No relevant document context available."

        context_parts = []
        total_chars = 0

        for i, result in enumerate(results, 1):
            snippet = f"[Source {i} | Score: {result.similarity_score:.2f}]\n{result.text}"
            if total_chars + len(snippet) > max_chars:
                break
            context_parts.append(snippet)
            total_chars += len(snippet)

        return "\n\n---\n\n".join(context_parts)
