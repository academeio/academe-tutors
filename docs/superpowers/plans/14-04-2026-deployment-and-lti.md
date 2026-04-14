# Academe Tutors — Deployment & LTI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy Academe Tutors to Railway + Cloudflare Pages, connect to Canvas LMS via LTI 1.3, and deliver a working AI tutor chat in three stages.

**Architecture:** Manual OIDC implementation (no pylti1p3) for LTI 1.3. OpenRouter as unified AI gateway via OpenAI SDK. Neon PostgreSQL with pgvector shared with canvascbme. Session JWTs for auth (no cookies in iframes).

**Tech Stack:** Python 3.12, FastAPI, asyncpg/SQLAlchemy, python-jose, httpx, OpenAI SDK (→ OpenRouter), Next.js 15, React 19, Tailwind 4, Cloudflare Pages, Railway.

**Spec:** `docs/superpowers/specs/14-04-2026-deployment-and-lti-design.md`

---

## File Map

### Files to create (S1)

| File | Responsibility |
|------|---------------|
| `backend/app/db/migrations/002_lti_platforms.sql` | LTI platform registration table |
| `backend/app/lti/oidc.py` | OIDC login initiation + JWT validation + JWKS caching |
| `backend/app/lti/session.py` | Session JWT minting + validation (FastAPI dependency) |
| `backend/app/lti/claims.py` | LTI claim extraction + role mapping |
| `backend/app/services/openrouter.py` | OpenRouter client (replaces direct anthropic/openai) |
| `backend/tests/test_lti_oidc.py` | Tests for OIDC flow |
| `backend/tests/test_lti_session.py` | Tests for session JWT |
| `backend/tests/test_lti_claims.py` | Tests for claim extraction |
| `backend/tests/test_openrouter.py` | Tests for OpenRouter streaming |
| `backend/tests/test_chat_ws.py` | Tests for WebSocket chat |
| `web/src/lib/api.ts` | Backend API client + WebSocket manager |
| `web/src/hooks/useChat.ts` | Chat state hook (messages, streaming, send) |
| `web/src/components/chat/MessageList.tsx` | Message display with markdown rendering |
| `web/src/components/chat/ChatInput.tsx` | Message input with send button |
| `web/src/components/chat/StreamingMessage.tsx` | Live streaming text display |
| `scripts/seed_lti_platform.py` | Seed lti_platforms table for SBV |

### Files to modify (S1)

| File | Changes |
|------|---------|
| `backend/pyproject.toml` | Remove `PyLTI1p3`, `anthropic`; add `cryptography` |
| `backend/app/core/config.py` | Remove single-platform LTI vars; add `frontend_url`, `openrouter_api_key` |
| `backend/app/api/routers/lti.py` | Replace stubs with real OIDC flow |
| `backend/app/api/routers/chat.py` | Wire WebSocket to OpenRouter streaming |
| `backend/app/services/llm.py` | Replace anthropic client with OpenRouter |
| `backend/app/main.py` | No changes needed (routers already registered) |
| `backend/.env.example` | Update env vars |
| `web/src/app/chat/page.tsx` | Wire to useChat hook, real UI |
| `web/src/app/page.tsx` | Update landing copy |

---

## Phase S1: LTI + Chat

### Task 1: Update dependencies and config

**Files:**
- Modify: `backend/pyproject.toml`
- Modify: `backend/app/core/config.py`
- Modify: `backend/.env.example`

- [ ] **Step 1: Update pyproject.toml dependencies**

Comment out `PyLTI1p3` and `anthropic` (keep for potential future use). The OpenAI SDK talks to OpenRouter. Keep `python-jose` for JWT.

```toml
dependencies = [
    # Web framework
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.34.0",
    "websockets>=14.0",
    "python-multipart>=0.0.18",

    # LTI 1.3 (disabled — using manual OIDC for now)
    # "PyLTI1p3>=2.0.0",

    # Database
    "asyncpg>=0.30.0",
    "sqlalchemy[asyncio]>=2.0.36",
    "alembic>=1.14.0",
    "pgvector>=0.3.6",

    # AI (via OpenRouter)
    "openai>=1.60.0",
    "tiktoken>=0.8.0",
    # "anthropic>=0.49.0",  # disabled — using OpenRouter gateway instead

    # Document parsing (S2, but install now)
    "pymupdf>=1.25.0",
    "python-docx>=1.1.0",
    "beautifulsoup4>=4.12.0",
    "markdownify>=0.14.0",

    # Auth & Security
    "python-jose[cryptography]>=3.3.0",
    "cryptography>=44.0.0",
    "httpx>=0.28.0",

    # Utilities
    "pydantic>=2.10.0",
    "pydantic-settings>=2.7.0",
    "tenacity>=9.0.0",
    "structlog>=24.4.0",
]
```

- [ ] **Step 2: Update config.py**

Replace the single-platform LTI vars with dynamic platform lookup. Add OpenRouter and frontend URL.

```python
"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Academe Tutors configuration. All values from .env or environment."""

    # Database
    database_url: str = "postgresql+asyncpg://localhost/academe_tutors"

    # AI (OpenRouter)
    openrouter_api_key: str = ""
    default_model: str = "anthropic/claude-sonnet-4-6"

    # Embedding
    embedding_model: str = "text-embedding-3-large"
    embedding_dimension: int = 3072

    # Application
    backend_port: int = 8001
    frontend_url: str = "http://localhost:3782"
    secret_key: str = "change-me-in-production"
    allowed_origins: list[str] = ["http://localhost:3782"]

    # Optional
    brave_api_key: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
```

- [ ] **Step 3: Update .env.example**

```
# --- Database (Shared Neon PostgreSQL) ---
DATABASE_URL=postgresql+asyncpg://user:pass@ep-xxx.ap-southeast-1.aws.neon.tech/neondb?sslmode=require

# --- AI (OpenRouter) ---
OPENROUTER_API_KEY=
DEFAULT_MODEL=anthropic/claude-sonnet-4-6

# --- Embedding ---
EMBEDDING_MODEL=text-embedding-3-large
EMBEDDING_DIMENSION=3072

# --- Application ---
BACKEND_PORT=8001
FRONTEND_URL=https://tutor.ai.in
SECRET_KEY=
ALLOWED_ORIGINS=https://tutor.ai.in,https://sbvlms.cloudintegral.com

# --- Optional ---
BRAVE_API_KEY=
```

- [ ] **Step 4: Commit**

```bash
git add backend/pyproject.toml backend/app/core/config.py backend/.env.example
git commit -m "chore: update deps — remove pylti1p3/anthropic, add openrouter via openai sdk"
```

---

### Task 2: LTI platforms migration

**Files:**
- Create: `backend/app/db/migrations/002_lti_platforms.sql`
- Create: `scripts/seed_lti_platform.py`

- [ ] **Step 1: Write the migration**

```sql
-- 002: LTI platform registration
-- Each Canvas installation gets one row. Platform lookup by issuer URL.

CREATE TABLE IF NOT EXISTS lti_platforms (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    issuer          TEXT NOT NULL UNIQUE,
    client_id       TEXT NOT NULL,
    deployment_id   TEXT,
    auth_url        TEXT NOT NULL,
    jwks_url        TEXT NOT NULL,
    token_url       TEXT NOT NULL,
    jwks_cache      JSONB,
    jwks_cached_at  TIMESTAMPTZ,
    tenant_id       INTEGER REFERENCES tenants(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

- [ ] **Step 2: Write the seed script**

```python
"""Seed lti_platforms for SBV Canvas installation."""
import asyncio
import os

import asyncpg


async def main():
    conn = await asyncpg.connect(os.environ["DATABASE_URL"].replace("+asyncpg", ""))
    await conn.execute("""
        INSERT INTO lti_platforms (issuer, client_id, auth_url, jwks_url, token_url, tenant_id)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (issuer) DO UPDATE SET
            client_id = EXCLUDED.client_id,
            auth_url = EXCLUDED.auth_url,
            jwks_url = EXCLUDED.jwks_url,
            token_url = EXCLUDED.token_url
    """,
        "https://sbvlms.cloudintegral.com",
        os.environ.get("LTI_CLIENT_ID", "FILL_AFTER_DEV_KEY_CREATED"),
        "https://sbvlms.cloudintegral.com/api/lti/authorize_redirect",
        "https://sbvlms.cloudintegral.com/api/lti/security/jwks",
        "https://sbvlms.cloudintegral.com/login/oauth2/token",
        1,  # SBV tenant_id
    )
    print("Seeded SBV LTI platform")
    await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 3: Run migration against Neon**

Run: `psql $DATABASE_URL -f backend/app/db/migrations/002_lti_platforms.sql`
Expected: `CREATE TABLE` (or no error if exists)

- [ ] **Step 4: Commit**

```bash
git add backend/app/db/migrations/002_lti_platforms.sql scripts/seed_lti_platform.py
git commit -m "sql: migration 002 — lti_platforms table + SBV seed script"
```

---

### Task 3: LTI claim extraction and role mapping

**Files:**
- Create: `backend/app/lti/claims.py`
- Create: `backend/tests/test_lti_claims.py`

- [ ] **Step 1: Write the failing test**

```python
"""Tests for LTI claim extraction and role mapping."""
import pytest

from app.lti.claims import extract_lti_claims, map_lti_role


class TestMapLtiRole:
    def test_instructor_maps_to_faculty(self):
        roles = ["http://purl.imsglobal.org/vocab/lis/v2/membership#Instructor"]
        assert map_lti_role(roles) == "faculty"

    def test_learner_maps_to_student(self):
        roles = ["http://purl.imsglobal.org/vocab/lis/v2/membership#Learner"]
        assert map_lti_role(roles) == "student"

    def test_admin_maps_to_admin(self):
        roles = [
            "http://purl.imsglobal.org/vocab/lis/v2/institution/person#Administrator"
        ]
        assert map_lti_role(roles) == "admin"

    def test_multiple_roles_highest_wins(self):
        roles = [
            "http://purl.imsglobal.org/vocab/lis/v2/membership#Learner",
            "http://purl.imsglobal.org/vocab/lis/v2/membership#Instructor",
        ]
        assert map_lti_role(roles) == "faculty"

    def test_unknown_role_defaults_to_student(self):
        roles = ["http://purl.imsglobal.org/vocab/lis/v2/membership#ContentDeveloper"]
        assert map_lti_role(roles) == "student"

    def test_empty_roles_defaults_to_student(self):
        assert map_lti_role([]) == "student"


class TestExtractLtiClaims:
    def test_extracts_standard_claims(self):
        token_payload = {
            "sub": "user-123",
            "name": "Test Student",
            "email": "test@mgmcri.ac.in",
            "https://purl.imsglobal.org/spec/lti/claim/roles": [
                "http://purl.imsglobal.org/vocab/lis/v2/membership#Learner"
            ],
            "https://purl.imsglobal.org/spec/lti/claim/context": {
                "id": "834",
                "label": "AN-MBBS1",
                "title": "Anatomy MBBS Phase 1",
            },
            "https://purl.imsglobal.org/spec/lti/claim/resource_link": {
                "id": "link-456",
                "title": "Academe Tutor",
            },
        }
        claims = extract_lti_claims(token_payload)
        assert claims.lti_user_id == "user-123"
        assert claims.user_name == "Test Student"
        assert claims.user_email == "test@mgmcri.ac.in"
        assert claims.role == "student"
        assert claims.course_id == "834"
        assert claims.course_title == "Anatomy MBBS Phase 1"
        assert claims.resource_link_id == "link-456"

    def test_handles_missing_optional_claims(self):
        token_payload = {
            "sub": "user-789",
            "https://purl.imsglobal.org/spec/lti/claim/roles": [],
        }
        claims = extract_lti_claims(token_payload)
        assert claims.lti_user_id == "user-789"
        assert claims.user_name is None
        assert claims.user_email is None
        assert claims.role == "student"
        assert claims.course_id is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_lti_claims.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.lti.claims'`

- [ ] **Step 3: Write the implementation**

```python
"""LTI 1.3 claim extraction and role mapping."""

from dataclasses import dataclass

LTI_CLAIM_ROLES = "https://purl.imsglobal.org/spec/lti/claim/roles"
LTI_CLAIM_CONTEXT = "https://purl.imsglobal.org/spec/lti/claim/context"
LTI_CLAIM_RESOURCE_LINK = "https://purl.imsglobal.org/spec/lti/claim/resource_link"

# Priority order: admin > faculty > student
_ROLE_MAP = [
    ("institution/person#Administrator", "admin"),
    ("membership#Instructor", "faculty"),
    ("membership#Learner", "student"),
]


def map_lti_role(roles: list[str]) -> str:
    """Map LTI role URNs to internal role. Highest priority wins."""
    for pattern, internal_role in _ROLE_MAP:
        if any(pattern in r for r in roles):
            return internal_role
    return "student"


@dataclass
class LtiClaims:
    """Parsed LTI 1.3 launch claims."""

    lti_user_id: str
    user_name: str | None
    user_email: str | None
    role: str
    course_id: str | None
    course_label: str | None
    course_title: str | None
    resource_link_id: str | None


def extract_lti_claims(payload: dict) -> LtiClaims:
    """Extract structured claims from a validated LTI id_token payload."""
    roles = payload.get(LTI_CLAIM_ROLES, [])
    context = payload.get(LTI_CLAIM_CONTEXT, {})
    resource_link = payload.get(LTI_CLAIM_RESOURCE_LINK, {})

    return LtiClaims(
        lti_user_id=payload["sub"],
        user_name=payload.get("name"),
        user_email=payload.get("email"),
        role=map_lti_role(roles),
        course_id=context.get("id"),
        course_label=context.get("label"),
        course_title=context.get("title"),
        resource_link_id=resource_link.get("id"),
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_lti_claims.py -v`
Expected: All 8 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/lti/claims.py backend/tests/test_lti_claims.py
git commit -m "feat(lti): claim extraction and role mapping with tests"
```

---

### Task 4: Session JWT minting and validation

**Files:**
- Create: `backend/app/lti/session.py`
- Create: `backend/tests/test_lti_session.py`

- [ ] **Step 1: Write the failing test**

```python
"""Tests for session JWT minting and validation."""
import pytest
from datetime import datetime, timezone, timedelta

from app.lti.session import create_session_token, validate_session_token, SessionPayload


class TestCreateSessionToken:
    def test_creates_valid_jwt(self):
        token = create_session_token(
            session_id="sess-123",
            user_email="student@mgmcri.ac.in",
            tenant_id=1,
            course_id=834,
            role="student",
            secret="test-secret",
        )
        assert isinstance(token, str)
        assert len(token.split(".")) == 3  # JWT has 3 parts


class TestValidateSessionToken:
    def test_validates_good_token(self):
        token = create_session_token(
            session_id="sess-123",
            user_email="student@mgmcri.ac.in",
            tenant_id=1,
            course_id=834,
            role="student",
            secret="test-secret",
        )
        payload = validate_session_token(token, secret="test-secret")
        assert payload.session_id == "sess-123"
        assert payload.user_email == "student@mgmcri.ac.in"
        assert payload.tenant_id == 1
        assert payload.course_id == 834
        assert payload.role == "student"

    def test_rejects_wrong_secret(self):
        token = create_session_token(
            session_id="sess-123",
            user_email="x@x.com",
            tenant_id=1,
            course_id=834,
            role="student",
            secret="real-secret",
        )
        with pytest.raises(ValueError, match="Invalid session token"):
            validate_session_token(token, secret="wrong-secret")

    def test_rejects_expired_token(self):
        token = create_session_token(
            session_id="sess-123",
            user_email="x@x.com",
            tenant_id=1,
            course_id=834,
            role="student",
            secret="test-secret",
            expires_hours=-1,  # Already expired
        )
        with pytest.raises(ValueError, match="Invalid session token"):
            validate_session_token(token, secret="test-secret")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_lti_session.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write the implementation**

```python
"""Session JWT creation and validation for LTI launches."""

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta

from jose import jwt, JWTError


@dataclass
class SessionPayload:
    """Decoded session JWT payload."""

    session_id: str
    user_email: str
    tenant_id: int
    course_id: int | None
    role: str


def create_session_token(
    session_id: str,
    user_email: str,
    tenant_id: int,
    course_id: int | None,
    role: str,
    secret: str,
    expires_hours: int = 8,
) -> str:
    """Mint a session JWT after successful LTI launch."""
    now = datetime.now(timezone.utc)
    payload = {
        "session_id": session_id,
        "user_email": user_email,
        "tenant_id": tenant_id,
        "course_id": course_id,
        "role": role,
        "iat": now,
        "exp": now + timedelta(hours=expires_hours),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def validate_session_token(token: str, secret: str) -> SessionPayload:
    """Validate and decode a session JWT. Raises ValueError on failure."""
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
    except JWTError as e:
        raise ValueError(f"Invalid session token: {e}")
    return SessionPayload(
        session_id=payload["session_id"],
        user_email=payload["user_email"],
        tenant_id=payload["tenant_id"],
        course_id=payload.get("course_id"),
        role=payload["role"],
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_lti_session.py -v`
Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/lti/session.py backend/tests/test_lti_session.py
git commit -m "feat(lti): session JWT minting and validation with tests"
```

---

### Task 5: OIDC login and launch endpoints

**Files:**
- Create: `backend/app/lti/oidc.py`
- Modify: `backend/app/api/routers/lti.py`
- Create: `backend/tests/test_lti_oidc.py`

- [ ] **Step 1: Write the failing test**

```python
"""Tests for LTI OIDC flow."""
import json
import pytest
from unittest.mock import AsyncMock, patch
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_login_redirects_to_canvas():
    """OIDC login should look up the platform and redirect to Canvas auth."""
    mock_platform = {
        "issuer": "https://sbvlms.cloudintegral.com",
        "client_id": "10000000000042",
        "auth_url": "https://sbvlms.cloudintegral.com/api/lti/authorize_redirect",
    }

    with patch("app.api.routers.lti.get_platform_by_issuer", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_platform
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/lti/login",
                params={
                    "iss": "https://sbvlms.cloudintegral.com",
                    "login_hint": "user-hint-123",
                    "target_link_uri": "https://api.tutor.ai.in/lti/launch",
                    "lti_message_hint": "msg-hint-456",
                    "client_id": "10000000000042",
                },
                follow_redirects=False,
            )

    assert resp.status_code == 302
    location = resp.headers["location"]
    assert "sbvlms.cloudintegral.com/api/lti/authorize_redirect" in location
    assert "response_type=id_token" in location
    assert "login_hint=user-hint-123" in location
    assert "client_id=10000000000042" in location
    # State cookie should be set
    assert "lti_state" in resp.headers.get("set-cookie", "")


@pytest.mark.asyncio
async def test_login_rejects_unknown_platform():
    """OIDC login should 400 for unknown issuer."""
    with patch("app.api.routers.lti.get_platform_by_issuer", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/lti/login",
                params={
                    "iss": "https://unknown.example.com",
                    "login_hint": "hint",
                    "target_link_uri": "https://api.tutor.ai.in/lti/launch",
                },
                follow_redirects=False,
            )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_jwks_returns_empty_keyset():
    """JWKS endpoint should return empty keyset for S1."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/lti/jwks")
    assert resp.status_code == 200
    assert resp.json() == {"keys": []}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_lti_oidc.py -v`
Expected: FAIL — existing stubs return JSON, not redirects

- [ ] **Step 3: Write the OIDC helper module**

```python
"""LTI 1.3 OIDC helpers — platform lookup and JWKS caching."""

import secrets
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_platform_by_issuer(db: AsyncSession, issuer: str) -> dict | None:
    """Look up an LTI platform by its issuer URL."""
    result = await db.execute(
        text("SELECT * FROM lti_platforms WHERE issuer = :issuer"),
        {"issuer": issuer},
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def get_platform_jwks(db: AsyncSession, platform: dict) -> dict:
    """Fetch and cache the platform's JWKS. Cached for 24h in lti_platforms."""
    cached_at = platform.get("jwks_cached_at")
    if cached_at and (datetime.now(timezone.utc) - cached_at) < timedelta(hours=24):
        return platform["jwks_cache"]

    async with httpx.AsyncClient() as client:
        resp = await client.get(platform["jwks_url"])
        resp.raise_for_status()
        jwks = resp.json()

    await db.execute(
        text("""
            UPDATE lti_platforms
            SET jwks_cache = :jwks, jwks_cached_at = now()
            WHERE id = :id
        """),
        {"jwks": jwks, "id": str(platform["id"])},
    )
    await db.commit()
    return jwks


def generate_state_nonce() -> tuple[str, str]:
    """Generate random state and nonce for OIDC flow."""
    return secrets.token_urlsafe(32), secrets.token_urlsafe(32)


def build_auth_redirect_url(
    platform: dict,
    redirect_uri: str,
    login_hint: str,
    state: str,
    nonce: str,
    lti_message_hint: str | None = None,
) -> str:
    """Build the Canvas OIDC authorization redirect URL."""
    params = {
        "response_type": "id_token",
        "redirect_uri": redirect_uri,
        "client_id": platform["client_id"],
        "login_hint": login_hint,
        "state": state,
        "nonce": nonce,
        "scope": "openid",
        "response_mode": "form_post",
        "prompt": "none",
    }
    if lti_message_hint:
        params["lti_message_hint"] = lti_message_hint
    return f"{platform['auth_url']}?{urlencode(params)}"
```

- [ ] **Step 4: Rewrite the LTI router**

```python
"""LTI 1.3 launch and service endpoints."""

import json
import uuid

from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from jose import jwt as jose_jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.lti.oidc import (
    get_platform_by_issuer,
    get_platform_jwks,
    generate_state_nonce,
    build_auth_redirect_url,
)
from app.lti.claims import extract_lti_claims
from app.lti.session import create_session_token

router = APIRouter()

REDIRECT_URI = None  # Set dynamically from request


@router.get("/login")
async def oidc_login(
    request: Request,
    iss: str | None = None,
    login_hint: str | None = None,
    target_link_uri: str | None = None,
    lti_message_hint: str | None = None,
    client_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """OIDC login initiation — Canvas redirects here first."""
    if not iss or not login_hint:
        raise HTTPException(400, "Missing iss or login_hint")

    platform = await get_platform_by_issuer(db, iss)
    if not platform:
        raise HTTPException(400, f"Unknown platform: {iss}")

    state, nonce = generate_state_nonce()
    redirect_uri = str(request.url_for("lti_launch"))

    auth_url = build_auth_redirect_url(
        platform=platform,
        redirect_uri=redirect_uri,
        login_hint=login_hint,
        state=state,
        nonce=nonce,
        lti_message_hint=lti_message_hint,
    )

    response = RedirectResponse(url=auth_url, status_code=302)
    response.set_cookie(
        key="lti_state",
        value=json.dumps({"state": state, "nonce": nonce}),
        max_age=300,
        httponly=True,
        secure=True,
        samesite="none",
    )
    return response


@router.post("/launch")
async def lti_launch(
    request: Request,
    id_token: str = Form(...),
    state: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """LTI 1.3 resource link launch — Canvas POST after OIDC completes."""
    # 1. Verify state from cookie
    state_cookie = request.cookies.get("lti_state")
    if not state_cookie:
        raise HTTPException(400, "Missing state cookie")
    try:
        saved = json.loads(state_cookie)
    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid state cookie")
    if saved.get("state") != state:
        raise HTTPException(400, "State mismatch")

    # 2. Decode JWT header to get kid, then find issuer from unverified payload
    try:
        unverified = jose_jwt.get_unverified_claims(id_token)
        header = jose_jwt.get_unverified_header(id_token)
    except JWTError:
        raise HTTPException(400, "Malformed id_token")

    issuer = unverified.get("iss")
    platform = await get_platform_by_issuer(db, issuer)
    if not platform:
        raise HTTPException(400, f"Unknown issuer: {issuer}")

    # 3. Fetch JWKS and validate
    jwks = await get_platform_jwks(db, platform)
    kid = header.get("kid")
    matching_keys = [k for k in jwks.get("keys", []) if k.get("kid") == kid]
    if not matching_keys:
        raise HTTPException(400, "No matching key in JWKS")

    try:
        payload = jose_jwt.decode(
            id_token,
            matching_keys[0],
            algorithms=["RS256"],
            audience=platform["client_id"],
            issuer=platform["issuer"],
        )
    except JWTError as e:
        raise HTTPException(400, f"JWT validation failed: {e}")

    # 4. Verify nonce
    if payload.get("nonce") != saved.get("nonce"):
        raise HTTPException(400, "Nonce mismatch")

    # 5. Extract claims
    claims = extract_lti_claims(payload)

    # 6. Create session
    session_id = str(uuid.uuid4())
    # TODO (Task 6): persist session to tutor_sessions table

    # 7. Mint session JWT
    token = create_session_token(
        session_id=session_id,
        user_email=claims.user_email or f"{claims.lti_user_id}@lti",
        tenant_id=platform.get("tenant_id", 1),
        course_id=int(claims.course_id) if claims.course_id else None,
        role=claims.role,
        secret=settings.secret_key,
    )

    # 8. Redirect to frontend
    response = RedirectResponse(
        url=f"{settings.frontend_url}/chat?token={token}",
        status_code=302,
    )
    response.delete_cookie("lti_state")
    return response


@router.get("/jwks")
async def jwks():
    """Public JWKS endpoint — empty for S1, needed for AGS in S3."""
    return {"keys": []}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_lti_oidc.py -v`
Expected: All 3 tests PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/lti/oidc.py backend/app/api/routers/lti.py backend/tests/test_lti_oidc.py
git commit -m "feat(lti): OIDC login, launch callback, and JWKS endpoints"
```

---

### Task 6: OpenRouter streaming service

**Files:**
- Create: `backend/app/services/openrouter.py`
- Modify: `backend/app/services/llm.py`
- Create: `backend/tests/test_openrouter.py`

- [ ] **Step 1: Write the failing test**

```python
"""Tests for OpenRouter LLM service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.openrouter import stream_chat_response


@pytest.mark.asyncio
async def test_stream_chat_response_yields_deltas():
    """Should yield text deltas from OpenRouter streaming response."""
    # Mock the OpenAI streaming response
    mock_chunk_1 = MagicMock()
    mock_chunk_1.choices = [MagicMock()]
    mock_chunk_1.choices[0].delta.content = "Hello"

    mock_chunk_2 = MagicMock()
    mock_chunk_2.choices = [MagicMock()]
    mock_chunk_2.choices[0].delta.content = " world"

    mock_chunk_3 = MagicMock()
    mock_chunk_3.choices = [MagicMock()]
    mock_chunk_3.choices[0].delta.content = None  # End of stream

    async def mock_stream():
        for chunk in [mock_chunk_1, mock_chunk_2, mock_chunk_3]:
            yield chunk

    mock_response = MagicMock()
    mock_response.__aiter__ = lambda self: mock_stream()

    with patch("app.services.openrouter.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        deltas = []
        async for delta in stream_chat_response(
            messages=[{"role": "user", "content": "Hi"}],
            system_prompt="You are a tutor.",
            api_key="test-key",
        ):
            deltas.append(delta)

    assert deltas == ["Hello", " world"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_openrouter.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write the OpenRouter service**

```python
"""OpenRouter LLM service — unified AI gateway via OpenAI-compatible API."""

from openai import AsyncOpenAI

from app.core.config import settings


def get_client(api_key: str | None = None) -> AsyncOpenAI:
    """Get an async OpenAI client pointed at OpenRouter."""
    return AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key or settings.openrouter_api_key,
        default_headers={
            "HTTP-Referer": "https://tutor.ai.in",
            "X-Title": "Academe Tutors",
        },
    )


async def stream_chat_response(
    messages: list[dict],
    system_prompt: str,
    api_key: str | None = None,
    model: str | None = None,
    max_tokens: int = 4096,
):
    """Stream a chat response from OpenRouter.

    Yields text deltas as they arrive.
    """
    client = get_client(api_key)
    full_messages = [{"role": "system", "content": system_prompt}] + messages

    response = await client.chat.completions.create(
        model=model or settings.default_model,
        messages=full_messages,
        max_tokens=max_tokens,
        stream=True,
    )

    async for chunk in response:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
```

- [ ] **Step 4: Delete the old llm.py (replaced by openrouter.py)**

```python
"""LLM service — delegates to OpenRouter. See openrouter.py."""

# This module is kept for backwards compatibility.
# All LLM calls should use app.services.openrouter directly.
from app.services.openrouter import stream_chat_response, get_client  # noqa: F401
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_openrouter.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/openrouter.py backend/app/services/llm.py backend/tests/test_openrouter.py
git commit -m "feat: OpenRouter streaming service via OpenAI SDK"
```

---

### Task 7: WebSocket chat endpoint

**Files:**
- Modify: `backend/app/api/routers/chat.py`
- Create: `backend/tests/test_chat_ws.py`

- [ ] **Step 1: Write the failing test**

```python
"""Tests for chat WebSocket endpoint."""
import pytest
from unittest.mock import patch, AsyncMock
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.lti.session import create_session_token


@pytest.mark.asyncio
async def test_chat_history_requires_auth():
    """History endpoint should 401 without a valid token."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/chat/sessions/fake-id/history")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_chat_history_with_valid_token():
    """History endpoint should 200 with a valid session token."""
    token = create_session_token(
        session_id="sess-123",
        user_email="test@test.com",
        tenant_id=1,
        course_id=834,
        role="student",
        secret="test-secret-key-for-testing-only",
    )

    with patch("app.api.routers.chat.settings") as mock_settings:
        mock_settings.secret_key = "test-secret-key-for-testing-only"
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/api/chat/sessions/sess-123/history",
                headers={"Authorization": f"Bearer {token}"},
            )
    assert resp.status_code == 200
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_chat_ws.py -v`
Expected: FAIL — current chat.py has no auth

- [ ] **Step 3: Rewrite the chat router**

```python
"""Chat API — WebSocket and REST endpoints for tutor conversations."""

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.lti.session import validate_session_token, SessionPayload
from app.services.openrouter import stream_chat_response
from app.tutorbot.templates import SOUL_TEMPLATE

router = APIRouter()


def get_current_user(authorization: str = Header(None)) -> SessionPayload:
    """FastAPI dependency — extract and validate session JWT from Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing or invalid Authorization header")
    token = authorization.removeprefix("Bearer ")
    try:
        return validate_session_token(token, settings.secret_key)
    except ValueError:
        raise HTTPException(401, "Invalid session token")


@router.websocket("/ws/{session_id}")
async def chat_websocket(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time tutor chat.

    Auth: token passed as query param ?token=...
    Protocol:
      Client sends: {"type": "message", "content": "..."}
      Server streams: {"type": "delta", "content": "..."} per chunk
      Server sends: {"type": "done", "message_id": "..."} when complete
    """
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return
    try:
        user = validate_session_token(token, settings.secret_key)
    except ValueError:
        await websocket.close(code=4001, reason="Invalid token")
        return

    await websocket.accept()

    # In-memory message history for this session (S2 will persist to DB)
    history: list[dict] = []

    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") != "message" or not data.get("content"):
                continue

            user_message = data["content"]
            history.append({"role": "user", "content": user_message})

            # Stream response from OpenRouter
            full_response = ""
            async for delta in stream_chat_response(
                messages=history,
                system_prompt=SOUL_TEMPLATE,
            ):
                full_response += delta
                await websocket.send_json({"type": "delta", "content": delta})

            history.append({"role": "assistant", "content": full_response})

            await websocket.send_json({"type": "done", "content": full_response})

    except WebSocketDisconnect:
        pass


@router.get("/sessions/{session_id}/history")
async def get_history(
    session_id: str,
    user: SessionPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get message history for a session."""
    # TODO (S2): Query tutor_messages by session_id
    return {"session_id": session_id, "messages": []}
```

- [ ] **Step 4: Create the soul template loader**

Create `backend/app/tutorbot/templates/__init__.py`:

```python
"""TutorBot soul templates."""

from pathlib import Path

_TEMPLATE_DIR = Path(__file__).parent

SOUL_TEMPLATE = (_TEMPLATE_DIR / "SOUL.md").read_text()
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_chat_ws.py -v`
Expected: All 2 tests PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/routers/chat.py backend/app/tutorbot/templates/__init__.py backend/tests/test_chat_ws.py
git commit -m "feat: WebSocket chat with OpenRouter streaming and session auth"
```

---

### Task 8: Next.js chat frontend

**Files:**
- Create: `web/src/lib/api.ts`
- Create: `web/src/hooks/useChat.ts`
- Create: `web/src/components/chat/MessageList.tsx`
- Create: `web/src/components/chat/ChatInput.tsx`
- Create: `web/src/components/chat/StreamingMessage.tsx`
- Modify: `web/src/app/chat/page.tsx`

- [ ] **Step 1: Create the API client and WebSocket manager**

`web/src/lib/api.ts`:

```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8001";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  streaming?: boolean;
}

export function createChatSocket(
  sessionId: string,
  token: string,
  onDelta: (delta: string) => void,
  onDone: (content: string) => void,
  onError: (error: string) => void,
): WebSocket {
  const ws = new WebSocket(`${WS_URL}/api/chat/ws/${sessionId}?token=${token}`);

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === "delta") {
      onDelta(data.content);
    } else if (data.type === "done") {
      onDone(data.content);
    } else if (data.type === "error") {
      onError(data.content || "Unknown error");
    }
  };

  ws.onerror = () => onError("WebSocket connection error");

  return ws;
}

export async function fetchHistory(sessionId: string, token: string): Promise<ChatMessage[]> {
  const resp = await fetch(`${API_URL}/api/chat/sessions/${sessionId}/history`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!resp.ok) return [];
  const data = await resp.json();
  return data.messages || [];
}
```

- [ ] **Step 2: Create the useChat hook**

`web/src/hooks/useChat.ts`:

```typescript
"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { ChatMessage, createChatSocket } from "@/lib/api";

export function useChat(sessionId: string | null, token: string | null) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [streaming, setStreaming] = useState(false);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const streamBufferRef = useRef("");
  const messageIdRef = useRef(0);

  useEffect(() => {
    if (!sessionId || !token) return;

    const ws = createChatSocket(
      sessionId,
      token,
      // onDelta
      (delta) => {
        streamBufferRef.current += delta;
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (last?.streaming) {
            return [...prev.slice(0, -1), { ...last, content: streamBufferRef.current }];
          }
          return prev;
        });
      },
      // onDone
      (content) => {
        streamBufferRef.current = "";
        setStreaming(false);
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (last?.streaming) {
            return [...prev.slice(0, -1), { ...last, content, streaming: false }];
          }
          return prev;
        });
      },
      // onError
      (error) => {
        setStreaming(false);
        console.error("Chat error:", error);
      },
    );

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    wsRef.current = ws;

    return () => ws.close();
  }, [sessionId, token]);

  const sendMessage = useCallback(
    (content: string) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN || streaming) return;

      const userMsg: ChatMessage = {
        id: `msg-${++messageIdRef.current}`,
        role: "user",
        content,
      };
      const assistantMsg: ChatMessage = {
        id: `msg-${++messageIdRef.current}`,
        role: "assistant",
        content: "",
        streaming: true,
      };

      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setStreaming(true);
      streamBufferRef.current = "";

      wsRef.current.send(JSON.stringify({ type: "message", content }));
    },
    [streaming],
  );

  return { messages, streaming, connected, sendMessage };
}
```

- [ ] **Step 3: Create chat components**

`web/src/components/chat/MessageList.tsx`:

```tsx
import { ChatMessage } from "@/lib/api";
import { StreamingMessage } from "./StreamingMessage";

export function MessageList({ messages }: { messages: ChatMessage[] }) {
  return (
    <div className="space-y-4">
      {messages.map((msg) => (
        <div
          key={msg.id}
          className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
        >
          <div
            className={`max-w-[80%] rounded-lg px-4 py-2 text-sm ${
              msg.role === "user"
                ? "bg-blue-600 text-white"
                : "bg-white text-slate-800 border border-slate-200"
            }`}
          >
            {msg.streaming ? (
              <StreamingMessage content={msg.content} />
            ) : (
              <div className="whitespace-pre-wrap">{msg.content}</div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
```

`web/src/components/chat/StreamingMessage.tsx`:

```tsx
export function StreamingMessage({ content }: { content: string }) {
  return (
    <div className="whitespace-pre-wrap">
      {content}
      <span className="inline-block w-1.5 h-4 bg-blue-500 animate-pulse ml-0.5" />
    </div>
  );
}
```

`web/src/components/chat/ChatInput.tsx`:

```tsx
"use client";

import { useState, useRef } from "react";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [input, setInput] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setInput("");
    inputRef.current?.focus();
  };

  return (
    <div className="flex gap-3">
      <input
        ref={inputRef}
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && handleSend()}
        placeholder="Ask your tutor a question..."
        disabled={disabled}
        className="flex-1 rounded-lg border border-slate-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none disabled:opacity-50"
      />
      <button
        onClick={handleSend}
        disabled={disabled || !input.trim()}
        className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
      >
        Send
      </button>
    </div>
  );
}
```

- [ ] **Step 4: Wire up the chat page**

`web/src/app/chat/page.tsx`:

```tsx
"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useMemo, useEffect, useRef } from "react";
import { useChat } from "@/hooks/useChat";
import { MessageList } from "@/components/chat/MessageList";
import { ChatInput } from "@/components/chat/ChatInput";

function ChatContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Decode session_id from the JWT payload (base64 middle segment)
  const sessionId = useMemo(() => {
    if (!token) return null;
    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      return payload.session_id;
    } catch {
      return null;
    }
  }, [token]);

  const { messages, streaming, connected, sendMessage } = useChat(sessionId, token);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (!token) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-slate-800">Academe Tutor</h1>
          <p className="mt-2 text-slate-500">Please launch from Canvas LMS.</p>
        </div>
      </main>
    );
  }

  return (
    <main className="flex h-screen flex-col">
      <header className="border-b border-slate-200 bg-white px-6 py-3">
        <div className="flex items-center justify-between">
          <h1 className="text-lg font-semibold text-slate-800">Academe Tutor</h1>
          <span
            className={`text-xs ${connected ? "text-green-600" : "text-red-500"}`}
          >
            {connected ? "Connected" : "Disconnected"}
          </span>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="mx-auto max-w-3xl">
          {messages.length === 0 && (
            <div className="text-center text-slate-400 mt-20">
              <p className="text-lg">Welcome to Academe Tutor</p>
              <p className="text-sm mt-1">Ask me anything about your course materials.</p>
            </div>
          )}
          <MessageList messages={messages} />
          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="border-t border-slate-200 bg-white p-4">
        <div className="mx-auto max-w-3xl">
          <ChatInput onSend={sendMessage} disabled={!connected || streaming} />
        </div>
      </div>
    </main>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={<div className="flex h-screen items-center justify-center">Loading...</div>}>
      <ChatContent />
    </Suspense>
  );
}
```

- [ ] **Step 5: Commit**

```bash
git add web/src/lib/api.ts web/src/hooks/useChat.ts web/src/components/chat/ web/src/app/chat/page.tsx
git commit -m "feat: chat UI with WebSocket streaming, message list, and session auth"
```

---

### Task 9: Deploy backend to Railway

**Files:**
- Modify: `docker/Dockerfile.backend`

- [ ] **Step 1: Create a Railway project**

Go to railway.app → New Project → Deploy from GitHub → select `academeio/academe-tutors`.

Configure:
- **Root directory:** `backend`
- **Builder:** Dockerfile at `../docker/Dockerfile.backend`
- **Port:** 8001
- **Custom domain:** `api.tutor.ai.in`

- [ ] **Step 2: Set environment variables in Railway**

```
DATABASE_URL=postgresql+asyncpg://...  (from Neon)
OPENROUTER_API_KEY=...
DEFAULT_MODEL=anthropic/claude-sonnet-4-6
SECRET_KEY=...  (generate: python -c "import secrets; print(secrets.token_hex(32))")
FRONTEND_URL=https://tutor.ai.in
ALLOWED_ORIGINS=https://tutor.ai.in,https://sbvlms.cloudintegral.com
```

- [ ] **Step 3: Verify deployment**

Run: `curl https://api.tutor.ai.in/health`
Expected: `{"status":"ok","service":"academe-tutors","version":"0.1.0"}`

- [ ] **Step 4: Commit any Dockerfile adjustments**

```bash
git add docker/Dockerfile.backend
git commit -m "deploy: Railway backend config"
```

---

### Task 10: Deploy frontend to Cloudflare Pages

- [ ] **Step 1: Connect Cloudflare Pages to GitHub**

Go to Cloudflare Dashboard → Pages → Create → Connect to Git → select `academeio/academe-tutors`.

Configure:
- **Build command:** `cd web && npm install && npm run build`
- **Build output directory:** `web/.next`
- **Root directory:** `/`
- **Framework preset:** Next.js
- **Environment variables:**
  - `NEXT_PUBLIC_API_URL=https://api.tutor.ai.in`
  - `NEXT_PUBLIC_WS_URL=wss://api.tutor.ai.in`

- [ ] **Step 2: Configure custom domains**

Add custom domains:
- `tutor.ai.in` → Cloudflare Pages
- `tutor.academe.org.in` → CNAME to `tutor.ai.in`

- [ ] **Step 3: Verify deployment**

Open `https://tutor.ai.in` in browser.
Expected: Landing page saying "Please launch from Canvas LMS."

---

### Task 11: Register LTI tool in Canvas and end-to-end test

- [ ] **Step 1: Create Canvas Developer Key (SBV)**

Go to Canvas Admin → Developer Keys → + Developer Key → LTI Key:

| Field | Value |
|-------|-------|
| Key Name | Academe Tutor |
| Redirect URIs | `https://api.tutor.ai.in/lti/launch` |
| Target Link URI | `https://api.tutor.ai.in/lti/launch` |
| OpenID Connect Initiation URL | `https://api.tutor.ai.in/lti/login` |
| JWK Method | Public JWK URL |
| Public JWK URL | `https://api.tutor.ai.in/lti/jwks` |

Enable the key. Note the `client_id` (numeric, e.g., `10000000000042`).

- [ ] **Step 2: Seed the platform**

```bash
LTI_CLIENT_ID=<from step 1> DATABASE_URL=<neon_url> python scripts/seed_lti_platform.py
```

- [ ] **Step 3: Add External Tool to test course**

Canvas → Course 374 (test course) → Settings → Apps → + App:
- Configuration Type: By Client ID
- Client ID: `<from step 1>`

- [ ] **Step 4: End-to-end test**

1. Open Canvas course 374
2. Navigate to a module or use the External Tool link
3. Click "Academe Tutor"
4. Should redirect through OIDC → land on `tutor.ai.in/chat?token=...`
5. Type a message → should stream a response from Claude via OpenRouter

- [ ] **Step 5: Commit any fixes from E2E testing**

```bash
git add -A
git commit -m "fix: adjustments from LTI end-to-end testing"
```

---

## Phase S2: RAG + Knowledge Base

> Tasks 12-17 to be planned after S1 is deployed and validated.
> Scope: document parsers, semantic chunker, pgvector embeddings, retrieval, knowledge base API, citation display.

---

## Phase S3: Agent Loop + Quotas + Profiles

> Tasks 18-25 to be planned after S2 is complete.
> Scope: agent loop with tools, competency awareness, student profiles, OpenRouter routing, quota enforcement, Razorpay checkout.
