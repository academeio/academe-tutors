# Academe Tutors — Project Instructions

## Project Overview
LTI-deployable AI tutoring system for Competency-Based Medical Education (CBME).
Inspired by DeepTutor (HKUDS, Apache 2.0). Deploys to any LTI 1.3 compliant LMS.

**Primary targets:** Canvas LMS at SBV institutions (MGMCRI, SSSMCRI, Santosh).

## Architecture

```
┌──────────────────────────────────┐
│          Canvas LMS              │
│  (sbvlms.cloudintegral.com)      │
└──────────┬───────────────────────┘
           │ LTI 1.3 Launch
           │ (OIDC + JWT + AGS + NRPS)
┌──────────▼───────────────────────┐
│     Academe Tutors Backend       │
│     Python 3.12 / FastAPI        │
│  ┌─────────┐  ┌───────────────┐  │
│  │ LTI 1.3 │  │  TutorBot     │  │
│  │ Provider │  │  Agent Loop   │  │
│  └────┬────┘  └───────┬───────┘  │
│       │               │          │
│  ┌────▼────────────────▼───────┐ │
│  │   RAG Pipeline              │ │
│  │   (parse→chunk→embed→index) │ │
│  └────────────┬────────────────┘ │
└───────────────┼──────────────────┘
           ┌────▼────┐
           │  Neon   │  ← Shared with canvascbme
           │ Postgres│    (competencies, topics, subjects)
           └─────────┘
```

## Tech Stack
- **Backend:** Python 3.12+, FastAPI, Uvicorn, WebSockets
- **Frontend:** Next.js 16, React 19, TypeScript, Tailwind CSS
- **Database:** Neon PostgreSQL (shared with canvascbme project)
- **Vector Store:** pgvector (Neon-native, no separate service)
- **LTI:** pylti1p3 (LTI 1.3 Advantage — OIDC, AGS, NRPS)
- **AI:** Claude API (primary), OpenAI (embeddings), pluggable providers
- **Deployment:** Docker → Railway (or any container host)

## Key URLs
- LMS Instance: https://sbvlms.cloudintegral.com/
- Shared Neon DB: fragrant-sea-37321263 (Singapore, aws-ap-southeast-1)
- Canvas Courses: MGMCRI=834, SSSMCRI=837, Santosh=838

## Credentials
- Stored in `.env` (gitignored, NEVER commit)
- LTI platform credentials from Canvas Developer Keys
- Neon connection via DATABASE_URL

## Directory Structure
```
academe-tutors/
├── backend/                 # Python FastAPI application
│   ├── app/
│   │   ├── api/routers/     # FastAPI route modules
│   │   ├── core/            # Config, security, dependencies
│   │   ├── db/              # Neon PostgreSQL + pgvector
│   │   │   └── migrations/  # SQL migration files
│   │   ├── lti/             # LTI 1.3 provider (pylti1p3)
│   │   ├── rag/             # RAG pipeline components
│   │   │   ├── parsers/     # Document parsing (PDF, MD, HTML)
│   │   │   ├── chunkers/    # Text chunking strategies
│   │   │   ├── embedders/   # Embedding providers
│   │   │   ├── indexers/    # Vector indexing (pgvector)
│   │   │   └── retrievers/  # Retrieval strategies
│   │   ├── services/        # Business logic services
│   │   └── tutorbot/        # Autonomous agent framework
│   │       ├── agent/       # Agent loop, context, memory
│   │       ├── channels/    # LTI channel adapter
│   │       ├── templates/   # Soul/personality templates
│   │       └── heartbeat/   # Scheduled autonomous actions
│   └── tests/               # pytest test suite
├── web/                     # Next.js frontend
│   ├── src/
│   │   ├── app/             # Next.js App Router pages
│   │   ├── components/      # React components
│   │   ├── lib/             # Utilities, API client
│   │   └── hooks/           # Custom React hooks
│   └── public/              # Static assets
├── scripts/                 # Setup, migration, seed scripts
├── docker/                  # Dockerfiles
├── docker-compose.yml
└── .env.example
```

## Development Commands
```bash
# Backend
cd backend && uv run uvicorn app.main:app --reload --port 8001

# Frontend
cd web && npm run dev    # port 3782

# Tests
cd backend && uv run pytest

# Docker (full stack)
docker compose up --build
```

## Shared Database Tables (READ-ONLY from canvascbme)
- subjects, topics, competencies (2,623 NMC 2024 competencies)
- capsules, capsule_versions (content for RAG ingestion)
- tenants, tenant_institutions (SBV + 11 sub-accounts)

## Tutor-Owned Tables (this project)
- tutor_sessions — Chat sessions with LTI context
- tutor_messages — Message history per session
- tutor_knowledge_bases — Per-course document collections
- tutor_documents — Uploaded/linked documents
- tutor_embeddings — pgvector embeddings
- tutor_profiles — Student learning profiles (evolving)
- tutor_bots — Bot configurations per course/topic

## Design Principles
1. **LTI-first:** Every session starts from an LMS launch. No standalone mode.
2. **Competency-aware:** Tutoring aligned to NMC CBUC competencies.
3. **Multi-tenant:** Institution isolation at database level.
4. **RAG-grounded:** Responses cite course materials, not just parametric knowledge.
5. **pgvector over external stores:** Keep vectors in Neon, no separate Pinecone/Weaviate.
6. **Capsule-connected:** Ingest Academe Capsule content as primary knowledge base.
