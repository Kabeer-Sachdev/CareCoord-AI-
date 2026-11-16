import json
import asyncio
from datetime import datetime
from typing import Dict, Set, Optional, Any
from fastapi import WebSocket

class ConnectionManager:
    """Centralized manager for WebSocket connections supporting user and role-targeted messaging."""

    def __init__(self):
        # All connected WebSockets
        self.active_connections: Set[WebSocket] = set()
        # Mapping from user_id to set of WebSockets
        self.user_connections: Dict[int, Set[WebSocket]] = {}
        # Mapping from role string to set of WebSockets
        self.role_connections: Dict[str, Set[WebSocket]] = {}
        # Metadata mapping socket to (user_id, role)
        self.socket_meta: Dict[WebSocket, Dict[str, Any]] = {}
        # Reference to main event loop
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop

    async def connect(self, websocket: WebSocket, user_id: Optional[int] = None, role: Optional[str] = None):
        """Accept WebSocket connection and register user/role mappings."""
        await websocket.accept()
        self.active_connections.add(websocket)
        self.socket_meta[websocket] = {"user_id": user_id, "role": role}

        if user_id is not None:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(websocket)

        if role:
            role_upper = role.upper()
            if role_upper not in self.role_connections:
                self.role_connections[role_upper] = set()
            self.role_connections[role_upper].add(websocket)

    def disconnect(self, websocket: WebSocket):
        """Cleanly unregister WebSocket upon disconnection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        meta = self.socket_meta.pop(websocket, {})
        user_id = meta.get("user_id")
        role = meta.get("role")

        if user_id is not None and user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

        if role:
            role_upper = role.upper()
            if role_upper in self.role_connections:
                self.role_connections[role_upper].discard(websocket)
                if not self.role_connections[role_upper]:
                    del self.role_connections[role_upper]

    def _prepare_payload(self, event_type: str, data: Any = None, payload: Any = None) -> str:
        content = data if data is not None else payload
        return json.dumps({
            "type": event_type,
            "data": content,
            "payload": content,
            "timestamp": datetime.utcnow().isoformat()
        }, default=str)

    async def broadcast(self, event_type: str, data: Any = None, payload: Any = None):
        """Broadcast event to all connected clients."""
        msg = self._prepare_payload(event_type, data, payload)
        dead_sockets = []
        for socket in list(self.active_connections):
            try:
                await socket.send_text(msg)
            except Exception:
                dead_sockets.append(socket)
        for socket in dead_sockets:
            self.disconnect(socket)

    async def send_personal(self, user_id: int, event_type: str, data: Any = None, payload: Any = None):
        """Send event strictly to a specific user_id."""
        sockets = list(self.user_connections.get(user_id, []))
        if not sockets:
            return
        msg = self._prepare_payload(event_type, data, payload)
        dead_sockets = []
        for socket in sockets:
            try:
                await socket.send_text(msg)
            except Exception:
                dead_sockets.append(socket)
        for socket in dead_sockets:
            self.disconnect(socket)

    async def broadcast_to_role(self, role: str, event_type: str, data: Any = None, payload: Any = None):
        """Broadcast event to all users connected under a specific role (e.g. 'DOCTOR')."""
        role_upper = role.upper()
        sockets = list(self.role_connections.get(role_upper, []))
        if not sockets:
            return
        msg = self._prepare_payload(event_type, data, payload)
        dead_sockets = []
        for socket in sockets:
            try:
                await socket.send_text(msg)
            except Exception:
                dead_sockets.append(socket)
        for socket in dead_sockets:
            self.disconnect(socket)

    # Synchronous helpers for sync endpoints and background services
    def dispatch_sync(self, coro):
        """Helper to safely schedule a coroutine from synchronous code."""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(coro)
        except RuntimeError:
            if self._loop and self._loop.is_running():
                asyncio.run_coroutine_threadsafe(coro, self._loop)
            else:
                # No event loop currently running (e.g. in test script or synchronous worker)
                try:
                    coro.close()
                except Exception:
                    pass

    def broadcast_sync(self, event_type: str, data: Any = None, payload: Any = None):
        content = data if data is not None else payload
        self.dispatch_sync(self.broadcast(event_type, content))

    def send_personal_sync(self, user_id: int, event_type: str, data: Any = None, payload: Any = None):
        content = data if data is not None else payload
        self.dispatch_sync(self.send_personal(user_id, event_type, content))

    def broadcast_to_role_sync(self, role: str, event_type: str, data: Any = None, payload: Any = None):
        content = data if data is not None else payload
        self.dispatch_sync(self.broadcast_to_role(role, event_type, content))

# Global connection manager instance
connection_manager = ConnectionManager()
