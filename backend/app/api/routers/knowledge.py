"""Knowledge Base API — document upload, indexing, and management."""

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

router = APIRouter()


@router.post("/bases")
async def create_knowledge_base(
    name: str,
    course_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Create a new knowledge base for a course."""
    # TODO: Insert into tutor_knowledge_bases
    return {"status": "not_implemented"}


@router.post("/bases/{kb_id}/documents")
async def upload_document(
    kb_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a document to a knowledge base.

    Pipeline:
    1. Save file and compute content hash (dedup)
    2. Parse document (PDF/DOCX/HTML/MD)
    3. Chunk text (semantic chunking preferred)
    4. Generate embeddings (OpenAI text-embedding-3-large)
    5. Store in tutor_embeddings (pgvector)
    6. Update knowledge base stats
    """
    # TODO: Implement RAG ingestion pipeline
    return {"status": "not_implemented", "filename": file.filename}


@router.post("/bases/{kb_id}/ingest-capsule")
async def ingest_capsule(
    kb_id: str,
    capsule_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Ingest an Academe Capsule into the knowledge base.

    Reads capsule content from shared Neon tables (capsule_versions)
    and indexes it for RAG retrieval.
    """
    # TODO: Read capsule JSONB content, render to text, chunk, embed
    return {"status": "not_implemented", "capsule_id": capsule_id}


@router.get("/bases/{kb_id}")
async def get_knowledge_base(kb_id: str, db: AsyncSession = Depends(get_db)):
    """Get knowledge base details and document list."""
    return {"status": "not_implemented", "kb_id": kb_id}
