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
            SET jwks_cache = cast(:jwks as jsonb), jwks_cached_at = now()
            WHERE id = :id
        """),
        {"jwks": __import__("json").dumps(jwks), "id": str(platform["id"])},
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
