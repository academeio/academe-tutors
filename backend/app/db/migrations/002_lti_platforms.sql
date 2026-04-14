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
