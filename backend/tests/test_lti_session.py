"""Tests for session JWT minting and validation."""
import pytest

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
