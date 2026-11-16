import json
import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session

from backend.database.database import SessionLocal
from backend.database.models import User
from backend.auth.security import decode_access_token
from backend.realtime.connection_manager import connection_manager

logger = logging.getLogger("carecoord.websocket")
router = APIRouter(tags=["Real-Time WebSockets"])

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """
    Central real-time WebSocket connection endpoint.
    Pass ?token=<jwt_token> to authenticate and bind user_id and role for targeted broadcasts.
    """
    user_id = None
    role = "GUEST"

    if token:
        payload = decode_access_token(token)
        if payload:
            user_id = payload.get("user_id")
            role = payload.get("role", "GUEST")

    await connection_manager.connect(websocket, user_id=user_id, role=role)
    try:
        # Initial greeting / connection acknowledgment
        await websocket.send_text(json.dumps({
            "type": "CONNECTION_ESTABLISHED",
            "data": {
                "user_id": user_id,
                "role": role,
                "status": "connected"
            }
        }))

        # Keep connection open and respond to client heartbeats
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except Exception:
                pass

    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
    except Exception as exc:
        logger.error(f"WebSocket error: {exc}")
        connection_manager.disconnect(websocket)

