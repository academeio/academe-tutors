-- Academe Tutors — Initial schema
-- Depends on: pgvector extension, shared canvascbme tables (subjects, topics, competencies)

CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- Tutor Bots — per-course or per-topic AI tutor configurations
-- ============================================================================
CREATE TABLE IF NOT EXISTS tutor_bots (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       INTEGER REFERENCES tenants(id),
    course_id       INTEGER,                    -- Canvas course ID
    topic_id        INTEGER REFERENCES topics(id),
    name            TEXT NOT NULL DEFAULT 'Academe Tutor',
    soul_template   TEXT,                       -- Personality/behavior markdown
    llm_model       TEXT NOT NULL DEFAULT 'claude-opus-4-6',
    max_iterations  INTEGER NOT NULL DEFAULT 20,
    is_active       BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- Knowledge Bases — per-course document collections for RAG
-- ============================================================================
CREATE TABLE IF NOT EXISTS tutor_knowledge_bases (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bot_id          UUID REFERENCES tutor_bots(id) ON DELETE CASCADE,
    tenant_id       INTEGER REFERENCES tenants(id),
    course_id       INTEGER,
    name            TEXT NOT NULL,
    description     TEXT,
    embedding_model TEXT NOT NULL DEFAULT 'text-embedding-3-large',
    embedding_dim   INTEGER NOT NULL DEFAULT 3072,
    doc_count       INTEGER NOT NULL DEFAULT 0,
    chunk_count     INTEGER NOT NULL DEFAULT 0,
    status          TEXT NOT NULL DEFAULT 'empty'
                    CHECK (status IN ('empty', 'indexing', 'ready', 'error')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- Documents — source documents in a knowledge base
-- ============================================================================
CREATE TABLE IF NOT EXISTS tutor_documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kb_id           UUID REFERENCES tutor_knowledge_bases(id) ON DELETE CASCADE,
    filename        TEXT NOT NULL,
    mime_type       TEXT,
    source_type     TEXT NOT NULL DEFAULT 'upload'
                    CHECK (source_type IN ('upload', 'capsule', 'url', 'canvas_page')),
    source_ref      TEXT,                       -- capsule_id, URL, or Canvas page ID
    content_hash    TEXT,                       -- SHA-256 for dedup
    chunk_count     INTEGER NOT NULL DEFAULT 0,
    status          TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'processing', 'indexed', 'error')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- Embeddings — pgvector chunks for RAG retrieval
-- ============================================================================
CREATE TABLE IF NOT EXISTS tutor_embeddings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_id          UUID REFERENCES tutor_documents(id) ON DELETE CASCADE,
    kb_id           UUID REFERENCES tutor_knowledge_bases(id) ON DELETE CASCADE,
    chunk_index     INTEGER NOT NULL,
    chunk_text      TEXT NOT NULL,
    embedding       vector(3072),               -- text-embedding-3-large
    metadata        JSONB DEFAULT '{}',          -- page number, heading, etc.
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tutor_embeddings_vector
    ON tutor_embeddings USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_tutor_embeddings_kb
    ON tutor_embeddings(kb_id);

-- ============================================================================
-- Sessions — chat sessions with LTI launch context
-- ============================================================================
CREATE TABLE IF NOT EXISTS tutor_sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bot_id          UUID REFERENCES tutor_bots(id),
    tenant_id       INTEGER REFERENCES tenants(id),
    user_email      TEXT NOT NULL,
    user_name       TEXT,
    user_role       TEXT NOT NULL DEFAULT 'student'
                    CHECK (user_role IN ('student', 'faculty', 'admin')),
    lti_user_id     TEXT,                       -- LTI sub claim
    canvas_user_id  INTEGER,
    course_id       INTEGER,
    competency_ids  INTEGER[],                  -- Relevant NMC competencies
    started_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_active_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    message_count   INTEGER NOT NULL DEFAULT 0,
    is_active       BOOLEAN NOT NULL DEFAULT true
);

CREATE INDEX IF NOT EXISTS idx_tutor_sessions_user
    ON tutor_sessions(user_email, bot_id);

-- ============================================================================
-- Messages — conversation history
-- ============================================================================
CREATE TABLE IF NOT EXISTS tutor_messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      UUID REFERENCES tutor_sessions(id) ON DELETE CASCADE,
    role            TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content         TEXT NOT NULL,
    thinking        TEXT,                       -- Extended thinking trace (optional)
    citations       JSONB,                      -- Source references from RAG
    tool_calls      JSONB,                      -- Tools invoked during generation
    tokens_in       INTEGER,
    tokens_out      INTEGER,
    latency_ms      INTEGER,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tutor_messages_session
    ON tutor_messages(session_id, created_at);

-- ============================================================================
-- Student Profiles — evolving learner models
-- ============================================================================
CREATE TABLE IF NOT EXISTS tutor_profiles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       INTEGER REFERENCES tenants(id),
    user_email      TEXT NOT NULL,
    canvas_user_id  INTEGER,
    learning_style  TEXT,                       -- Visual, auditory, kinesthetic, reading
    knowledge_gaps  JSONB DEFAULT '[]',          -- Identified weak areas
    strengths       JSONB DEFAULT '[]',          -- Identified strong areas
    preferences     JSONB DEFAULT '{}',          -- Language, detail level, etc.
    competency_progress JSONB DEFAULT '{}',      -- {competency_id: mastery_level}
    total_sessions  INTEGER NOT NULL DEFAULT 0,
    total_messages  INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(tenant_id, user_email)
);
