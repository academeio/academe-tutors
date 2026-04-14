"""Chat API — WebSocket and REST endpoints for tutor conversations."""

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
      Server sends: {"type": "done", "content": "..."} when complete
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
