# Academe Tutors — Deployment & LTI Integration Design

**Date:** 14-04-2026
**Status:** Approved
**Scope:** Deployment topology, LTI 1.3 integration, AI provider architecture, quota system, staged rollout

---

## 1. Overview

Academe Tutors is an LTI-deployable AI tutoring system for Competency-Based Medical Education. This spec covers how it deploys, connects to Canvas LMS, routes AI requests, and manages usage quotas.

**Target LMS installations:**
- **SBV** (`sbvlms.cloudintegral.com`) — root account 7, sub-accounts MGMCRI (17) and SSSMCRI (18)
- **Santosh** — separate Canvas installation (different URL/instance)

Each installation requires its own Canvas Developer Key (LTI 1.3).

---

## 2. Deployment Architecture

### 2.1 Topology

```
┌─────────────────────────────────────────────────────────┐
│  Canvas LMS (SBV)           Canvas LMS (Santosh)        │
│  sbvlms.cloudintegral.com   [santosh instance URL]      │
└────────┬────────────────────────────┬───────────────────┘
         │ LTI 1.3 (Dev Key #1)      │ LTI 1.3 (Dev Key #2)
         └────────────┬──────────────┘
                      │ HTTPS
         ┌────────────▼──────────────┐
         │  Cloudflare DNS           │
         │  tutor.ai.in (primary)    │
         │  tutor.academe.org.in     │
         │    → CNAME tutor.ai.in    │
         └────────────┬──────────────┘
                      │
         ┌────────────┴────────────┐
         ▼                         ▼
  ┌─────────────┐         ┌──────────────┐
  │ Cloudflare  │         │   Railway     │
  │ Pages       │ ◄─API──│   (backend)   │
  │ (frontend)  │         │   FastAPI     │
  │ Next.js     │         │   Python 3.12 │
  │ tutor.ai.in │         │   WebSocket   │
  └─────────────┘         └──────┬───────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
              ┌─────────┐ ┌──────────┐ ┌──────────┐
              │  Neon    │ │OpenRouter│ │Cloudflare│
              │PostgreSQL│ │  (AI GW) │ │ R2 (CDN) │
              │+pgvector │ │ 300+     │ │ assets   │
              │ shared   │ │ models   │ │          │
              └─────────┘ └──────────┘ └──────────┘
```

### 2.2 Domains

| Domain | Target | Purpose |
|--------|--------|---------|
| `tutor.ai.in` | Cloudflare Pages | Primary frontend |
| `tutor.academe.org.in` | CNAME → `tutor.ai.in` | Alias |
| `api.tutor.ai.in` | Railway service | Backend API + WebSocket |

### 2.3 Infrastructure

| Component | Service | Details |
|-----------|---------|---------|
| **Frontend** | Cloudflare Pages | Next.js, Edge Functions or static export |
| **Backend** | Railway | Python 3.12, FastAPI, Uvicorn, Docker |
| **Database** | Neon PostgreSQL | Shared with canvascbme (fragrant-sea-37321263, Singapore) |
| **Vector store** | pgvector (Neon) | No separate vector DB service |
| **AI gateway** | OpenRouter | OpenAI-compatible API, 300+ models |
| **Embeddings** | OpenAI via OpenRouter | text-embedding-3-large, 3072 dimensions |
| **File storage** | Cloudflare R2 | Document uploads for knowledge bases |
| **Payments** | Razorpay | INR credit top-ups |

---

## 3. LTI 1.3 Integration

### 3.1 Approach: Manual OIDC (No pylti1p3)

The LTI 1.3 tool provider spec is implemented directly using python-jose (JWT) and httpx (OIDC). This avoids pylti1p3's Django-centric storage layer and keeps the code FastAPI-native.

### 3.2 Platform Registration

Each Canvas installation is registered in a `lti_platforms` table:

```sql
CREATE TABLE lti_platforms (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    issuer          TEXT NOT NULL UNIQUE,   -- e.g. https://sbvlms.cloudintegral.com
    client_id       TEXT NOT NULL,          -- From Canvas Developer Key
    deployment_id   TEXT,
    auth_url        TEXT NOT NULL,          -- /api/lti/authorize_redirect
    jwks_url        TEXT NOT NULL,          -- /api/lti/security/jwks
    token_url       TEXT NOT NULL,          -- /login/oauth2/token
    jwks_cache      JSONB,                  -- Cached JWKS keys
    jwks_cached_at  TIMESTAMPTZ,
    tenant_id       INTEGER REFERENCES tenants(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Two rows: one for SBV, one for Santosh.

### 3.3 OIDC Login Flow

**Endpoint: `GET /lti/login`**

Canvas sends: `iss`, `login_hint`, `target_link_uri`, `lti_message_hint`, `client_id`.

1. Look up platform by `iss` (issuer URL) in `lti_platforms`
2. Generate `state` (random, 32 bytes) and `nonce` (random, 32 bytes)
3. Store `{state, nonce}` in a short-lived cookie (5 min, `SameSite=None; Secure; HttpOnly`)
4. Build auth redirect URL:
   ```
   {platform.auth_url}?
     response_type=id_token
     &redirect_uri=https://api.tutor.ai.in/lti/launch
     &client_id={platform.client_id}
     &login_hint={login_hint}
     &state={state}
     &nonce={nonce}
     &scope=openid
     &response_mode=form_post
     &lti_message_hint={lti_message_hint}
     &prompt=none
   ```
5. Redirect (302) to Canvas authorization endpoint

### 3.4 Launch Callback

**Endpoint: `POST /lti/launch`**

Canvas POSTs: `id_token` (JWT), `state`.

1. **Verify state** — Compare `state` param with cookie value. Reject if mismatch (CSRF).
2. **Fetch JWKS** — GET `platform.jwks_url`, cache keys for 24h in `lti_platforms.jwks_cache`.
3. **Validate JWT** — Using python-jose:
   - Verify signature against Canvas JWKS
   - Check `iss` matches platform issuer
   - Check `aud` contains our `client_id`
   - Check `nonce` matches cookie value
   - Check `exp` is in the future
   - Check `iat` is within acceptable skew (60s)
4. **Extract LTI claims:**
   - `sub` → LMS user ID
   - `name`, `email` → User identity
   - `https://purl.imsglobal.org/spec/lti/claim/roles` → Role array
   - `https://purl.imsglobal.org/spec/lti/claim/context` → Course (id, label, title)
   - `https://purl.imsglobal.org/spec/lti/claim/resource_link` → Resource link
5. **Resolve tenant** — Map `iss` → `lti_platforms.tenant_id`
6. **Map role** — Parse LTI role URNs:
   - `*/membership#Instructor` → `faculty`
   - `*/membership#Learner` → `student`
   - `*/institution/role#Administrator` → `admin`
7. **Find or create user** — Upsert into `tutor_profiles` by `(tenant_id, user_email)`
8. **Create session** — Insert into `tutor_sessions` with LTI context
9. **Mint session JWT** — Sign with `SECRET_KEY`, 8h expiry:
   ```json
   {
     "session_id": "uuid",
     "user_email": "student@mgmcri.ac.in",
     "tenant_id": 1,
     "course_id": 834,
     "role": "student",
     "exp": 1744761600
   }
   ```
10. **Redirect** to `https://tutor.ai.in/chat?token={session_jwt}`

### 3.5 JWKS Endpoint

**Endpoint: `GET /lti/jwks`**

Returns our tool's public key set. Needed for AGS (Assignment and Grade Services) in S3 when we sign messages back to Canvas. For S1, returns empty keyset `{"keys": []}`.

### 3.6 Session Model

- Backend mints JWT with session context (not stored in cookie — avoids iframe `SameSite` issues)
- Frontend receives JWT via URL query param on redirect
- Frontend stores JWT in memory (not localStorage)
- Frontend passes JWT as `Authorization: Bearer {token}` on WebSocket connect and all API calls
- Backend validates JWT on every request via FastAPI dependency

### 3.7 Canvas Developer Key Configuration

For each Canvas installation, create an LTI Developer Key:

| Field | Value |
|-------|-------|
| **Key Type** | LTI Key |
| **Redirect URIs** | `https://api.tutor.ai.in/lti/launch` |
| **Target Link URI** | `https://api.tutor.ai.in/lti/launch` |
| **OpenID Connect Initiation URL** | `https://api.tutor.ai.in/lti/login` |
| **JWK Method** | Public JWK URL |
| **Public JWK URL** | `https://api.tutor.ai.in/lti/jwks` |
| **LTI Advantage Services** | Enable all (AGS, NRPS, public JWK) |

After creating the key, enable it and add as an External Tool in the desired courses/sub-accounts.

---

## 4. AI Provider Architecture

### 4.1 OpenRouter as Unified Gateway

All LLM calls route through OpenRouter via the OpenAI-compatible API. The app never calls Anthropic, OpenAI, or other providers directly. This provides:

- Single API for 300+ models
- Per-key spending limits and usage tracking
- Model fallback chains
- No vendor lock-in

**SDK usage:**
```python
from openai import AsyncOpenAI

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=tenant_openrouter_key,
)

response = await client.chat.completions.create(
    model=selected_model,  # e.g. "anthropic/claude-sonnet-4"
    messages=messages,
    stream=True,
)
```

### 4.2 Model Selection — Phase 1 (Opaque)

Users see "Academe Tutor" — never a model name. The system selects models based on:

1. **Institution default** — Set in `tenant_provider_config.default_model`
2. **Course override** — Faculty can set per-course preference in `tutor_bots.llm_config`
3. **Complexity routing** — System auto-routes based on message characteristics:
   - Simple factual Q&A → cost-efficient model (e.g., `anthropic/claude-haiku-4-5`)
   - Multi-step reasoning → mid-tier (e.g., `anthropic/claude-sonnet-4-6`)
   - Complex Socratic dialogue → premium (e.g., `anthropic/claude-opus-4-6`)

All routing decisions logged in `tutor_usage.routing_reason` for later analysis.

### 4.3 Model Selection — Phase 2 (Transparent, Future)

After studying usage patterns and getting student feedback:

- Users see model tiers: "Standard" / "Advanced" / "Research"
- Each tier maps to specific models, with approximate cost shown per message
- Users manage their own quota allocation across tiers
- Rollout gated by feature flag in `tenant_provider_config`

### 4.4 Provider Config Table

```sql
CREATE TABLE tenant_provider_config (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           INTEGER REFERENCES tenants(id) UNIQUE,
    openrouter_key_encrypted TEXT NOT NULL,
    default_model       TEXT NOT NULL DEFAULT 'anthropic/claude-sonnet-4-6',
    model_routing_rules JSONB DEFAULT '{}',   -- complexity thresholds
    monthly_budget_usd  NUMERIC(10,2),
    spend_this_month    NUMERIC(10,2) NOT NULL DEFAULT 0,
    budget_reset_day    INTEGER NOT NULL DEFAULT 1,  -- day of month
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

## 5. Quota & Credits System

### 5.1 Three-Tier Quota Cascade

| Level | Who sets it | What it controls |
|-------|------------|-----------------|
| **Institution** | Admin | Monthly budget cap for all users at that institution |
| **User (free tier)** | System | Monthly allocation per student (e.g., ₹150 / ~$1.80 worth) |
| **User (paid credits)** | Student | Purchased credits via Razorpay, consumed after free tier |

### 5.2 Quota Enforcement Flow

```
User sends message
  → Check tutor_quotas.cost_used_this_month < max_cost_per_month
    → YES: proceed to LLM call
    → NO: Check tutor_wallets.balance_usd > 0
      → YES: deduct from wallet, proceed
      → NO: Return quota-exceeded message with top-up CTA
  → After response: log to tutor_usage, increment quota counters
  → Monthly cron: reset cost_used_this_month to 0
```

### 5.3 Credits Top-Up (Razorpay)

Students who exhaust their free monthly allocation can purchase credits:

1. Chat UI shows: "You've used your monthly allocation. Top up credits to continue."
2. Student clicks "Buy Credits" → modal with INR packages (e.g., ₹50, ₹100, ₹250)
3. Razorpay checkout (UPI, cards, net banking)
4. Webhook callback → verify payment → credit `tutor_wallets.balance_usd`
5. INR → USD conversion at payment time, stored as USD (matches OpenRouter billing)
6. Credits never expire, carry over across months

**Razorpay integration:**
- Backend endpoint: `POST /api/payments/create-order` (creates Razorpay order)
- Frontend: Razorpay checkout.js (opens payment modal)
- Backend webhook: `POST /api/payments/webhook` (verifies signature, credits wallet)
- Table: `tutor_wallets` + `tutor_payment_log`

### 5.4 E-Commerce — Future Scope (Separate Project)

A full e-commerce flow with:
- Credit packages with volume discounts
- Subscription plans (monthly unlimited for power users)
- Institutional bulk purchase and allocation
- Payment history and invoices
- Refund policy

This will be designed and implemented as a separate sub-project once usage patterns are understood.

### 5.5 Quota Tables

```sql
CREATE TABLE tutor_quotas (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_email              TEXT NOT NULL,
    tenant_id               INTEGER REFERENCES tenants(id),
    plan_tier               TEXT NOT NULL DEFAULT 'free'
                            CHECK (plan_tier IN ('free', 'paid', 'unlimited')),
    max_cost_per_month      NUMERIC(10,4) NOT NULL DEFAULT 1.80,  -- ~₹150
    cost_used_this_month    NUMERIC(10,4) NOT NULL DEFAULT 0,
    message_count_this_month INTEGER NOT NULL DEFAULT 0,
    quota_reset_at          TIMESTAMPTZ NOT NULL DEFAULT (date_trunc('month', now()) + interval '1 month'),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(tenant_id, user_email)
);

CREATE TABLE tutor_wallets (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_email      TEXT NOT NULL,
    tenant_id       INTEGER REFERENCES tenants(id),
    balance_usd     NUMERIC(10,4) NOT NULL DEFAULT 0,
    total_topped_up NUMERIC(10,4) NOT NULL DEFAULT 0,
    last_topped_up  TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(tenant_id, user_email)
);

CREATE TABLE tutor_usage (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      UUID REFERENCES tutor_sessions(id),
    user_email      TEXT NOT NULL,
    tenant_id       INTEGER REFERENCES tenants(id),
    model           TEXT NOT NULL,
    provider        TEXT NOT NULL DEFAULT 'openrouter',
    tokens_in       INTEGER NOT NULL,
    tokens_out      INTEGER NOT NULL,
    cost_usd        NUMERIC(10,6) NOT NULL,
    routing_reason  TEXT,            -- 'default', 'complexity:high', 'course_override'
    funded_by       TEXT NOT NULL DEFAULT 'institution'
                    CHECK (funded_by IN ('institution', 'wallet')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_tutor_usage_user_month
    ON tutor_usage(user_email, tenant_id, created_at);

CREATE TABLE tutor_payment_log (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_email          TEXT NOT NULL,
    tenant_id           INTEGER REFERENCES tenants(id),
    razorpay_order_id   TEXT NOT NULL,
    razorpay_payment_id TEXT,
    amount_inr          NUMERIC(10,2) NOT NULL,
    amount_usd          NUMERIC(10,4) NOT NULL,
    exchange_rate       NUMERIC(10,4) NOT NULL,
    status              TEXT NOT NULL DEFAULT 'created'
                        CHECK (status IN ('created', 'paid', 'failed', 'refunded')),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

## 6. Staged Implementation

### S1 — LTI + Chat (2-3 days)

**Goal:** Student launches from Canvas, chats with Academe Tutor, responses stream in real-time.

| Component | Details |
|-----------|---------|
| LTI OIDC | 3 endpoints: `/lti/login`, `/lti/launch`, `/lti/jwks` |
| `lti_platforms` table | Platform registration for SBV + Santosh |
| Session JWT | Mint on launch, validate on every request |
| Chat WebSocket | `/api/chat/ws/{session_id}` with JWT auth |
| LLM streaming | OpenRouter → Claude via OpenAI SDK, streamed to client |
| Chat UI | Next.js `/chat` page: message list, input, streaming display |
| Deploy | Railway (backend at `api.tutor.ai.in`) + Cloudflare Pages (frontend at `tutor.ai.in`) |
| Canvas config | Create Developer Keys in SBV and Santosh, add External Tool to test courses |

**Exit criteria:** Student clicks LTI tool in Canvas → OIDC → chat UI → sends message → receives streamed response.

### S2 — RAG + Knowledge Base (1-2 days)

**Goal:** Faculty uploads course materials, student gets grounded answers with citations.

| Component | Details |
|-----------|---------|
| Document parsers | PDF (pymupdf), DOCX (python-docx), HTML (beautifulsoup4), Markdown |
| Semantic chunker | Heading-aware + sentence boundary chunking, ~500 token target |
| Embeddings | OpenAI text-embedding-3-large via OpenRouter → pgvector |
| Retrieval | Cosine similarity top-k (k=5), with relevance threshold |
| Knowledge base API | CRUD endpoints + document upload + capsule ingestion from Neon |
| RAG context injection | Retrieved chunks injected into system prompt as `<retrieved_context>` |
| Citation display | Frontend renders source references inline with chunk highlights |

**Exit criteria:** Faculty uploads anatomy PDF → student asks "What are the branches of the axillary artery?" → answer cites specific pages from the PDF.

### S3 — Agent Loop + Quotas + Profiles (1-2 days)

**Goal:** Full autonomous tutor with competency awareness, usage tracking, and credit top-ups.

| Component | Details |
|-----------|---------|
| Agent loop | Iterative tool-use loop (max 20 iterations): RAG search, web search |
| Competency awareness | Link responses to NMC competency codes from shared Neon tables |
| Student profiles | Evolving profile: knowledge gaps, strengths, learning style |
| OpenRouter routing | Opaque model selection based on complexity + institution config |
| `tenant_provider_config` | Per-institution OpenRouter key, default model, budget |
| `tutor_quotas` | Per-user monthly allocation, enforcement middleware |
| `tutor_usage` | Every LLM call logged with model, tokens, cost, routing reason |
| `tutor_wallets` | Credit balance, top-up history |
| Razorpay checkout | INR credit packages, webhook verification, wallet crediting |
| `tutor_payment_log` | Payment audit trail |
| Soul template | Socratic method, NMC-aligned, adaptive to student level |

**Exit criteria:** Tutor adapts to student level, cites competency codes, institution has budget cap, student can buy credits when quota exhausted.

---

## 7. Security Considerations

- **API keys encrypted at rest** — `tenant_provider_config.openrouter_key_encrypted` uses Fernet symmetric encryption with a key derived from `SECRET_KEY`
- **JWT session tokens** — Short-lived (8h), signed with HMAC-SHA256, never stored in localStorage
- **LTI iframe security** — JWT passed via URL param on redirect, then via WebSocket auth header (avoids `SameSite` cookie issues in iframes)
- **JWKS caching** — Canvas public keys cached 24h in database, refreshed on signature validation failure
- **Nonce replay prevention** — Nonces stored in the state cookie alongside `state` (same 5-min TTL cookie from OIDC step 3), validated on launch callback, cookie cleared after use
- **Razorpay webhook verification** — HMAC-SHA256 signature verification on all payment callbacks
- **CORS** — Backend allows only `tutor.ai.in` and Canvas instance URLs
- **Rate limiting** — Per-user request rate limit on chat endpoint (10 req/min)
