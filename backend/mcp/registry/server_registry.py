"""
MCP Server Registry.
Tracks configured MCP servers, active connection states, discovered tools, and persists status to SQLite.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

from backend.mcp.schemas.mcp_schemas import MCPServerInfo, MCPToolDefinition
from backend.mcp.registry.server_config import DEFAULT_MCP_SERVERS, ALLOWED_MCP_TOOLS, TOOL_ROLE_PERMISSIONS
from backend.mcp.servers.hospital_server import hospital_mcp_server
from backend.mcp.servers.laboratory_server import laboratory_mcp_server
from backend.mcp.servers.pharmacy_server import pharmacy_mcp_server

logger = logging.getLogger("CareCoord.MCPRegistry")

class MCPServerRegistry:
    def __init__(self):
        self._servers: Dict[str, Dict[str, Any]] = {}
        self._instances: Dict[str, Any] = {
            "hospital-his": hospital_mcp_server,
            "laboratory-lis": laboratory_mcp_server,
            "pharmacy-rx": pharmacy_mcp_server
        }
        self._discovered_tools: Dict[str, List[MCPToolDefinition]] = {}
        self._initialize_registry()

    def _initialize_registry(self):
        """Initializes server registry from default configurations and syncs with database."""
        for s_id, conf in DEFAULT_MCP_SERVERS.items():
            self._servers[s_id] = {
                **conf,
                "status": "CONNECTED",  # Demonstrators are instantly connected and ready
                "tool_count": 0,
                "last_connected_at": datetime.utcnow()
            }
        
        # Populate initial tools through MCP discovery
        self.discover_all_tools()
        self.sync_to_db()

    def get_server_instance(self, server_id: str) -> Optional[Any]:
        """Returns the active MCPServer instance for a given server ID."""
        return self._instances.get(server_id)

    def list_servers(self) -> List[MCPServerInfo]:
        """Lists all registered MCP servers with active status and tool counts."""
        return [
            MCPServerInfo(
                server_id=s["server_id"],
                name=s["name"],
                description=s.get("description"),
                transport_type=s.get("transport_type", "in-memory"),
                endpoint=s.get("endpoint"),
                status=s["status"],
                is_enabled=s.get("is_enabled", True),
                tool_count=len(self._discovered_tools.get(s["server_id"], [])),
                last_connected_at=s.get("last_connected_at")
            )
            for s in self._servers.values()
        ]

    def get_server(self, server_id: str) -> Optional[MCPServerInfo]:
        """Retrieves metadata for a specific registered MCP server."""
        s = self._servers.get(server_id)
        if not s:
            return None
        return MCPServerInfo(
            server_id=s["server_id"],
            name=s["name"],
            description=s.get("description"),
            transport_type=s.get("transport_type", "in-memory"),
            endpoint=s.get("endpoint"),
            status=s["status"],
            is_enabled=s.get("is_enabled", True),
            tool_count=len(self._discovered_tools.get(s["server_id"], [])),
            last_connected_at=s.get("last_connected_at")
        )

    def connect_server(self, server_id: str) -> bool:
        """Connects a configured MCP server and triggers dynamic tool discovery."""
        if server_id not in self._servers:
            return False
        
        server_meta = self._servers[server_id]
        server_meta["status"] = "CONNECTED"
        server_meta["last_connected_at"] = datetime.utcnow()
        self.discover_tools_for_server(server_id)
        self.sync_to_db()
        return True

    def disconnect_server(self, server_id: str) -> bool:
        """Disconnects a configured MCP server and clears active tool access."""
        if server_id not in self._servers:
            return False
        
        server_meta = self._servers[server_id]
        server_meta["status"] = "DISCONNECTED"
        self._discovered_tools[server_id] = []
        self.sync_to_db()
        return True

    def discover_tools_for_server(self, server_id: str) -> List[MCPToolDefinition]:
        """
        Executes dynamic tool discovery against an MCPServer instance using protocol APIs.
        Applies server and tool allowlists.
        """
        instance = self._instances.get(server_id)
        server_meta = self._servers.get(server_id)
        if not instance or not server_meta or server_meta.get("status") != "CONNECTED":
            self._discovered_tools[server_id] = []
            return []

        allowed_names = set(ALLOWED_MCP_TOOLS.get(server_id, []))
        discovered = []

        # Use MCPServer tool manager protocol introspection
        raw_tools = instance._tool_manager.list_tools()
        for t in raw_tools:
            if t.name in allowed_names:
                role_req = TOOL_ROLE_PERMISSIONS.get(t.name, "PATIENT")
                discovered.append(MCPToolDefinition(
                    name=t.name,
                    server_id=server_id,
                    server_name=server_meta["name"],
                    description=t.description,
                    input_schema=t.parameters if hasattr(t, "parameters") else {},
                    required_role=role_req,
                    read_only=True
                ))

        self._discovered_tools[server_id] = discovered
        server_meta["tool_count"] = len(discovered)
        return discovered

    def discover_all_tools(self) -> Dict[str, List[MCPToolDefinition]]:
        """Discovers tools across all connected MCP servers."""
        for s_id in self._servers:
            if self._servers[s_id].get("status") == "CONNECTED":
                self.discover_tools_for_server(s_id)
        return self._discovered_tools

    def get_discovered_tools(self, server_id: Optional[str] = None) -> List[MCPToolDefinition]:
        """Returns discovered tools for a specific server or across all servers."""
        if server_id:
            return self._discovered_tools.get(server_id, [])
        all_tools = []
        for tools in self._discovered_tools.values():
            all_tools.extend(tools)
        return all_tools

    def sync_to_db(self):
        """Persists server registration records into SQLite database."""
        try:
            from backend.database.database import SessionLocal
            from backend.database.models import MCPServerRecord
            
            db = SessionLocal()
            try:
                for s_id, data in self._servers.items():
                    rec = db.query(MCPServerRecord).filter(MCPServerRecord.server_id == s_id).first()
                    tools_count = len(self._discovered_tools.get(s_id, []))
                    if not rec:
                        rec = MCPServerRecord(
                            server_id=s_id,
                            name=data["name"],
                            description=data.get("description"),
                            transport_type=data.get("transport_type", "in-memory"),
                            endpoint=data.get("endpoint"),
                            status=data["status"],
                            is_enabled=data.get("is_enabled", True),
                            tool_count=tools_count,
                            last_connected_at=data.get("last_connected_at")
                        )
                        db.add(rec)
                    else:
                        rec.name = data["name"]
                        rec.description = data.get("description")
                        rec.status = data["status"]
                        rec.tool_count = tools_count
                        rec.last_connected_at = data.get("last_connected_at")
                db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"MCP Server Registry DB sync warning: {e}")

server_registry = MCPServerRegistry()
