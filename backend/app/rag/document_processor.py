"""
RAG Document Processor.
Section 28-31: Document ingestion, chunking, embedding, and vector storage.
"""
import re
import uuid
from typing import List, Optional

from app.core.logging import logger


class DocumentChunk:
    """Represents a single embedded chunk of a document."""

    def __init__(
        self,
        chunk_id: str,
        document_id: str,
        text: str,
        chunk_index: int,
        embedding: Optional[List[float]] = None,
        metadata: Optional[dict] = None,
    ):
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.text = text
        self.chunk_index = chunk_index
        self.embedding = embedding
        self.metadata = metadata or {}


class DocumentProcessor:
    """
    Orchestrates text extraction, chunking, and embedding for RAG ingestion.
    Supports plain text, PDF (via pypdf), DOCX, PPTX content extraction.
    """

    def __init__(
        self,
        chunk_size: int = 600,
        chunk_overlap: int = 100,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def extract_text_from_plain(self, content: str) -> str:
        """Return raw text content as-is."""
        return content

    def extract_text_from_pdf(self, file_bytes: bytes) -> str:
        """Extract text from PDF bytes using pypdf."""
        try:
            import io
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(file_bytes))
            pages = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages.append(text.strip())
            return "\n\n".join(pages)
        except ImportError:
            raise RuntimeError("pypdf is required for PDF extraction. Install it: pip install pypdf")
        except Exception as e:
            raise RuntimeError(f"PDF extraction failed: {str(e)}")

    def extract_text_from_docx(self, file_bytes: bytes) -> str:
        """Extract text from DOCX bytes using python-docx."""
        try:
            import io
            from docx import Document
            doc = Document(io.BytesIO(file_bytes))
            paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            return "\n\n".join(paragraphs)
        except ImportError:
            raise RuntimeError("python-docx is required. Install it: pip install python-docx")
        except Exception as e:
            raise RuntimeError(f"DOCX extraction failed: {str(e)}")

    def extract_text_from_pptx(self, file_bytes: bytes) -> str:
        """Extract text from PPTX bytes using python-pptx."""
        try:
            import io
            from pptx import Presentation
            prs = Presentation(io.BytesIO(file_bytes))
            slides_text = []
            for slide in prs.slides:
                slide_texts = []
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        slide_texts.append(shape.text.strip())
                if slide_texts:
                    slides_text.append("\n".join(slide_texts))
            return "\n\n".join(slides_text)
        except ImportError:
            raise RuntimeError("python-pptx is required. Install it: pip install python-pptx")
        except Exception as e:
            raise RuntimeError(f"PPTX extraction failed: {str(e)}")

    def chunk_text(self, text: str, document_id: str) -> List[DocumentChunk]:
        """
        Split text into overlapping chunks preserving sentence boundaries where possible.
        Uses paragraph-aware splitting to minimize context fragmentation.
        """
        if not text.strip():
            return []

        # Split into paragraphs first
        paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]

        chunks: List[DocumentChunk] = []
        current_chunk_words: List[str] = []
        chunk_index = 0

        for paragraph in paragraphs:
            para_words = paragraph.split()
            for word in para_words:
                current_chunk_words.append(word)

                if len(current_chunk_words) >= self.chunk_size:
                    chunk_text = " ".join(current_chunk_words)
                    chunks.append(
                        DocumentChunk(
                            chunk_id=str(uuid.uuid4()),
                            document_id=document_id,
                            text=chunk_text,
                            chunk_index=chunk_index,
                        )
                    )
                    chunk_index += 1
                    # Keep overlap: retain last N words for continuity
                    current_chunk_words = current_chunk_words[-self.chunk_overlap:]

        # Add remaining text as final chunk
        if current_chunk_words:
            chunk_text = " ".join(current_chunk_words)
            if len(chunk_text.split()) > 10:  # skip tiny trailing fragments
                chunks.append(
                    DocumentChunk(
                        chunk_id=str(uuid.uuid4()),
                        document_id=document_id,
                        text=chunk_text,
                        chunk_index=chunk_index,
                    )
                )

        logger.info(
            f"Document '{document_id}' split into {len(chunks)} chunks "
            f"(size={self.chunk_size}, overlap={self.chunk_overlap})",
            extra={"rag": "DocumentProcessor", "document_id": document_id, "chunk_count": len(chunks)}
        )
        return chunks
