"""Tests for LTI OIDC flow."""
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
