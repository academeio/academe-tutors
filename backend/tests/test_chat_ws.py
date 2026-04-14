"""Tests for chat WebSocket endpoint."""
import pytest
from unittest.mock import patch
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.lti.session import create_session_token


SECRET = "test-secret-key-for-testing-only"


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
        secret=SECRET,
    )

    with patch("app.api.routers.chat.settings") as mock_settings:
        mock_settings.secret_key = SECRET
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/api/chat/sessions/sess-123/history",
                headers={"Authorization": f"Bearer {token}"},
            )
    assert resp.status_code == 200
