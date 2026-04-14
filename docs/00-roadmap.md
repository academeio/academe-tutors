# Academe Tutors — Roadmap

> Single source of truth for project progress, features, and priorities.

## Vision

AI-powered tutoring system for Competency-Based Medical Education (CBME), aligned with India's NMC curriculum. Deployed to Canvas LMS via LTI 1.3, with a path to standalone access.

**Product:** https://tutor.ai.in (also: tutor.academe.org.in)
**Repo:** https://github.com/academeio/academe-tutors

---

## Architecture

```
Canvas LMS (SBV / Santosh)
    │ LTI 1.3
    ▼
┌─────────────────────────────────────┐
│  Backend (Railway)                  │
│  Python 3.12 / FastAPI / WebSocket  │
│  backend.tutor.ai.in               │
│                                     │
│  ┌─────────┐  ┌──────────────────┐  │
│  │ LTI 1.3 │  │ Chat + Agent     │  │
│  │ OIDC    │  │ Loop             │  │
│  └────┬────┘  └───────┬──────────┘  │
│       │               │             │
│  ┌────▼───────────────▼──────────┐  │
│  │  RAG Pipeline (S2)            │  │
│  │  parse → chunk → embed → idx  │  │
│  └───────────────┬───────────────┘  │
└──────────────────┼──────────────────┘
                   │
     ┌─────────────┼─────────────┐
     ▼             ▼             ▼
  Neon PG       OpenRouter    Cloudflare
  +pgvector     (AI gateway)  R2 + Pages
```

**Frontend:** Next.js 15 / React 19 / Tailwind 4 on Cloudflare Pages (tutor.ai.in)
**Backend:** Python 3.12 / FastAPI on Railway (backend.tutor.ai.in)
**Database:** Neon PostgreSQL + pgvector (shared with canvascbme)
**AI Gateway:** OpenRouter (300+ models, OpenAI-compatible API)
**Payments:** Razorpay (INR credit top-ups)

---

## Stages

### S1 — LTI + Chat ✅ DONE (14-04-2026)

**Goal:** Student launches from Canvas, chats with AI tutor, responses stream in real-time.

| Component | Status |
|-----------|--------|
| Manual OIDC (no pylti1p3) — 3 endpoints | ✅ Done |
| `lti_platforms` table + SBV seed | ✅ Done |
| Session JWT minting + validation | ✅ Done |
| LTI claim extraction + role mapping | ✅ Done |
| OpenRouter streaming via OpenAI SDK | ✅ Done |
| WebSocket chat with session auth | ✅ Done |
| Next.js chat UI with markdown rendering | ✅ Done |
| Deploy: Railway (backend) + Cloudflare Pages (frontend) | ✅ Done |
| Canvas Developer Key (SBV) — client_id 10000000000153 | ✅ Done |
| E2E test: Canvas → OIDC → chat → streamed response | ✅ Done |
| 19 backend tests passing | ✅ Done |

**Known gaps (not blockers):**
- Chat history not persisted (in-memory only)
- No session list / sidebar
- Santosh Developer Key not yet created
- `tutor.academe.org.in` CNAME not configured
- Canvas opens in iframe (should configure new-tab launch)

---

### S2 — RAG + Knowledge Base 🔲 NOT STARTED

**Goal:** Faculty uploads course materials, student gets grounded answers with citations.

| Component | Status |
|-----------|--------|
| Message persistence to `tutor_messages` | 🔲 |
| Chat history sidebar (session list) | 🔲 |
| Document parsers (PDF, DOCX, HTML, Markdown) | 🔲 |
| Semantic chunker (heading-aware, ~500 token target) | 🔲 |
| Embeddings: OpenAI text-embedding-3-large → pgvector | 🔲 |
| Retrieval: cosine similarity top-k (k=5) | 🔲 |
| Knowledge base API (CRUD + upload + capsule ingestion) | 🔲 |
| RAG context injection into system prompt | 🔲 |
| Citation display in frontend | 🔲 |

**Exit criteria:** Faculty uploads anatomy PDF → student asks question → answer cites specific pages.

---

### S3 — Agent Loop + Quotas + Profiles 🔲 NOT STARTED

**Goal:** Full autonomous tutor with competency awareness, usage tracking, and credit top-ups.

| Component | Status |
|-----------|--------|
| Agent loop with tool use (RAG search, web search) | 🔲 |
| Competency awareness (NMC codes from shared Neon tables) | 🔲 |
| Student profile evolution (knowledge gaps, strengths, style) | 🔲 |
| Opaque model routing (complexity-based via OpenRouter) | 🔲 |
| `tenant_provider_config` — per-institution AI config | 🔲 |
| `tutor_quotas` — per-user monthly allocation | 🔲 |
| `tutor_usage` — per-request cost logging | 🔲 |
| `tutor_wallets` — credit balance | 🔲 |
| Razorpay checkout for INR credit top-ups | 🔲 |
| `tutor_payment_log` — payment audit trail | 🔲 |
| Soul template: Socratic method, NMC-aligned | ✅ Done (SOUL.md exists) |

**Exit criteria:** Tutor adapts to student level, institution has budget cap, student can buy credits.

---

### S4 — Open Access (v2) 🔲 FUTURE

**Goal:** Non-LMS users can sign up directly at tutor.ai.in.

| Component | Status |
|-----------|--------|
| Direct signup (email/password or Google auth) | 🔲 |
| Landing page with login/signup | 🔲 |
| Dual session model (LTI-launched + direct-auth) | 🔲 |
| Self-serve credit top-ups without LMS context | 🔲 |
| Transparent model selection (user chooses tier) | 🔲 |

---

### S5 — Advanced Features 🔲 FUTURE

| Feature | Description |
|---------|------------|
| AGS grade passback | Push tutor engagement scores to Canvas gradebook |
| NRPS roster sync | Auto-provision students from Canvas enrollment |
| Multi-channel (Telegram, WhatsApp) | TutorBot on messaging platforms |
| Heartbeat system | Scheduled study reminders, autonomous check-ins |
| Team collaboration | Multi-agent coordination for complex topics |
| Analytics dashboard | Institution-wide usage, cost, engagement metrics |
| Content authoring | Faculty creates tutor knowledge bases from UI |

---

## Infrastructure

### Live URLs

| Service | URL | Platform |
|---------|-----|----------|
| Frontend | https://tutor.ai.in | Cloudflare Pages |
| Backend | https://backend.tutor.ai.in | Railway |
| Backend (Railway URL) | https://backend-production-8592.up.railway.app | Railway |
| Repository | https://github.com/academeio/academe-tutors | GitHub |

### Canvas LMS Installations

| Installation | URL | LTI Client ID | Status |
|-------------|-----|---------------|--------|
| SBV (MGMCRI + SSSMCRI) | sbvlms.cloudintegral.com | 10000000000153 | ✅ Active |
| Santosh | santosh.lms.net.in | — | 🔲 Pending |

### Database

Shared Neon PostgreSQL: `fragrant-sea-37321263` (Singapore, aws-ap-southeast-1)

**Tutor-owned tables (migration 001):**
- `tutor_bots` — per-course AI tutor configurations
- `tutor_knowledge_bases` — per-course document collections
- `tutor_documents` — source documents in a KB
- `tutor_embeddings` — pgvector chunks for RAG
- `tutor_sessions` — chat sessions with LTI context
- `tutor_messages` — conversation history
- `tutor_profiles` — evolving student learner models

**LTI table (migration 002):**
- `lti_platforms` — Canvas installation registry

**Pending tables (S3):**
- `tenant_provider_config` — per-institution AI provider config
- `tutor_quotas` — per-user monthly allocation
- `tutor_wallets` — credit balance
- `tutor_usage` — per-request cost logging
- `tutor_payment_log` — Razorpay payment audit

### AI Provider

All LLM calls route through **OpenRouter** (openrouter.ai) via the OpenAI SDK.
- No direct Anthropic/OpenAI API calls
- Model selection is opaque to users (Phase 1)
- Default model: `anthropic/claude-sonnet-4-6`
- Future: transparent model tiers with per-tier pricing

---

## Design Specs

| Spec | Date | Scope |
|------|------|-------|
| [Deployment & LTI Design](superpowers/specs/14-04-2026-deployment-and-lti-design.md) | 14-04-2026 | Deployment, LTI 1.3, AI provider, quotas, staged rollout |

## Implementation Plans

| Plan | Date | Scope | Status |
|------|------|-------|--------|
| [S1: LTI + Chat](superpowers/plans/14-04-2026-deployment-and-lti.md) | 14-04-2026 | 11 tasks: deps, LTI, OpenRouter, chat UI, deploy, Canvas | ✅ Done |

---

## Key Decisions

| Decision | Date | Rationale |
|----------|------|-----------|
| Separate repo from canvascbme | 14-04-2026 | Different tech stack (Python vs Node.js), independent deployment |
| Manual OIDC instead of pylti1p3 | 14-04-2026 | Avoids Django-centric storage, FastAPI-native, simpler |
| OpenRouter as AI gateway | 14-04-2026 | 300+ models, no vendor lock-in, built-in key management |
| pgvector in Neon (not Pinecone) | 14-04-2026 | Vectors alongside competencies, one DB, no extra service |
| Opaque model selection first | 14-04-2026 | Learn from usage data before exposing model choice to users |
| No student BYOK initially | 14-04-2026 | Simpler — credits via Razorpay instead of OpenRouter OAuth |
| Canvas issuer = canvas.instructure.com | 14-04-2026 | All Canvas Cloud instances use this, not instance-specific URL |
| Cloudflare Pages + Railway | 14-04-2026 | Same stack as other Academe projects, WebSockets fine at scale |
