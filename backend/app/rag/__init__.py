"""RAG (Retrieval-Augmented Generation) pipeline.

Components:
- parsers/   — Document parsing (PDF, DOCX, HTML, Markdown)
- chunkers/  — Text chunking strategies (fixed, semantic)
- embedders/ — Embedding providers (OpenAI, local)
- indexers/  — Vector indexing via pgvector
- retrievers/ — Similarity search and reranking
"""
