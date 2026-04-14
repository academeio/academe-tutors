"""Chat API — WebSocket and REST endpoints for tutor conversations."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

router = APIRouter()


@router.websocket("/ws/{session_id}")
async def chat_websocket(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time tutor chat.

    Protocol:
    1. Client connects with session token in query params
    2. Server validates session and loads context
    3. Client sends: {"type": "message", "content": "..."}
    4. Server streams: {"type": "delta", "content": "..."} chunks
    5. Server sends: {"type": "done", "citations": [...], "message_id": "..."}
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            # TODO: Route to TutorBot agent loop
            # 1. Load session context (history, profile, knowledge base)
            # 2. Build RAG context (retrieve relevant chunks)
            # 3. Run agent loop (Claude API with tools)
            # 4. Stream response deltas via WebSocket
            # 5. Persist message and update profile
            await websocket.send_json({
                "type": "done",
                "content": f"[TutorBot not yet implemented] Received: {data.get('content', '')}",
                "citations": [],
            })
    except WebSocketDisconnect:
        pass


@router.get("/sessions/{session_id}/history")
async def get_history(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get message history for a session."""
    # TODO: Query tutor_messages by session_id
    return {"session_id": session_id, "messages": []}
