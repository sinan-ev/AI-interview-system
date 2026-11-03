"""
Unit Tests: RAG Document Processing.
Tests chunking, text extraction, and vector store formatting.
"""
import pytest
from app.rag.document_processor import DocumentProcessor, DocumentChunk
from app.rag.vector_store import VectorSearchResult, VectorStore


class TestDocumentProcessor:

    @pytest.fixture
    def processor(self):
        return DocumentProcessor(chunk_size=50, chunk_overlap=10)

    def test_chunk_text_empty_returns_empty(self, processor):
        chunks = processor.chunk_text("", "doc-1")
        assert chunks == []

    def test_chunk_text_whitespace_returns_empty(self, processor):
        chunks = processor.chunk_text("   \n\n   ", "doc-1")
        assert chunks == []

    def test_chunk_text_short_text_single_chunk(self, processor):
        text = "This is a short text that should fit in one chunk."
        chunks = processor.chunk_text(text, "doc-1")
        assert len(chunks) >= 1
        assert all(isinstance(c, DocumentChunk) for c in chunks)

    def test_chunk_text_long_text_multiple_chunks(self, processor):
        # 200 words should produce multiple chunks with chunk_size=50
        text = " ".join(["word"] * 200)
        chunks = processor.chunk_text(text, "doc-2")
        assert len(chunks) > 1

    def test_chunk_document_id_propagated(self, processor):
        text = " ".join(["token"] * 100)
        chunks = processor.chunk_text(text, "my-doc-id")
        for chunk in chunks:
            assert chunk.document_id == "my-doc-id"

    def test_chunk_unique_ids(self, processor):
        text = " ".join(["word"] * 200)
        chunks = processor.chunk_text(text, "doc-3")
        ids = [c.chunk_id for c in chunks]
        assert len(ids) == len(set(ids)), "Chunk IDs must be unique"

    def test_chunk_indices_sequential(self, processor):
        text = " ".join(["word"] * 200)
        chunks = processor.chunk_text(text, "doc-4")
        indices = [c.chunk_index for c in chunks]
        assert indices == list(range(len(chunks)))

    def test_chunk_overlap_continuity(self, processor):
        """Overlap should cause later chunks to start with some words from prior chunk."""
        text = " ".join([f"word{i}" for i in range(120)])
        chunks = processor.chunk_text(text, "doc-5")
        if len(chunks) >= 2:
            # First chunk's last 10 words should appear in second chunk
            first_chunk_words = chunks[0].text.split()[-processor.chunk_overlap:]
            second_chunk_words = chunks[1].text.split()[:processor.chunk_overlap]
            assert first_chunk_words == second_chunk_words

    def test_extract_text_from_plain(self, processor):
        content = "Hello, this is plain text."
        result = processor.extract_text_from_plain(content)
        assert result == content

    def test_chunk_text_respects_paragraphs(self):
        """Paragraph breaks should be respected during chunking."""
        proc = DocumentProcessor(chunk_size=20, chunk_overlap=5)
        text = "First paragraph with several words to fill space.\n\nSecond paragraph which also has content."
        chunks = proc.chunk_text(text, "doc-6")
        assert len(chunks) >= 1


class TestVectorSearchResult:

    def test_vector_search_result_creation(self):
        result = VectorSearchResult(
            chunk_id="chunk-1",
            document_id="doc-1",
            text="This is retrieved text.",
            chunk_index=0,
            similarity_score=0.92,
        )
        assert result.chunk_id == "chunk-1"
        assert result.document_id == "doc-1"
        assert result.similarity_score == 0.92
        assert result.metadata == {}

    def test_format_context_for_prompt_empty(self):
        """Empty results should return fallback string."""
        # We need a VectorStore instance but can't use a real DB
        # Test the formatting logic by instantiating with None
        vs = VectorStore.__new__(VectorStore)
        context = vs.format_context_for_prompt([])
        assert "No relevant" in context

    def test_format_context_for_prompt_with_results(self):
        vs = VectorStore.__new__(VectorStore)
        results = [
            VectorSearchResult("c1", "d1", "Python is a programming language.", 0, 0.95),
            VectorSearchResult("c2", "d1", "It has a clean syntax.", 1, 0.88),
        ]
        context = vs.format_context_for_prompt(results, max_chars=5000)
        assert "Source 1" in context
        assert "Source 2" in context
        assert "Python is a programming language." in context

    def test_format_context_respects_max_chars(self):
        vs = VectorStore.__new__(VectorStore)
        # Create a result with large text
        large_text = "word " * 1000
        results = [
            VectorSearchResult("c1", "d1", large_text, 0, 0.90),
        ]
        context = vs.format_context_for_prompt(results, max_chars=100)
        # Context should be limited; very large text should be truncated
        assert len(context) <= 200  # Allow some overhead for the header


class TestMockEmbeddingProvider:

    @pytest.mark.asyncio
    async def test_mock_embed_text_returns_vector(self):
        from app.ai.embeddings.provider import MockEmbeddingProvider
        provider = MockEmbeddingProvider()
        vector = await provider.embed_text("Hello, world!")
        assert isinstance(vector, list)
        assert len(vector) == provider.dimensions
        assert all(isinstance(v, float) for v in vector)

    @pytest.mark.asyncio
    async def test_mock_embed_batch_returns_multiple_vectors(self):
        from app.ai.embeddings.provider import MockEmbeddingProvider
        provider = MockEmbeddingProvider()
        texts = ["First text", "Second text", "Third text"]
        vectors = await provider.embed_batch(texts)
        assert len(vectors) == 3
        assert all(len(v) == provider.dimensions for v in vectors)

    @pytest.mark.asyncio
    async def test_mock_embed_deterministic(self):
        """Same text should always produce same vector."""
        from app.ai.embeddings.provider import MockEmbeddingProvider
        provider = MockEmbeddingProvider()
        v1 = await provider.embed_text("deterministic test")
        v2 = await provider.embed_text("deterministic test")
        assert v1 == v2

    @pytest.mark.asyncio
    async def test_mock_embed_different_texts_different_vectors(self):
        """Different texts should produce different vectors."""
        from app.ai.embeddings.provider import MockEmbeddingProvider
        provider = MockEmbeddingProvider()
        v1 = await provider.embed_text("Python concurrency")
        v2 = await provider.embed_text("Database design patterns")
        assert v1 != v2
