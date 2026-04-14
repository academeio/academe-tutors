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
