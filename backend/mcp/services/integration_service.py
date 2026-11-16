"""
MCP External Integration Service.
Coordinates tool execution with role-based access control (RBAC), input/output sanitization,
safety guardrails, and persistent database audit logging.
"""

from typing import Dict, Any, Optional, List
import logging

from backend.mcp.client.mcp_client import mcp_client
from backend.mcp.schemas.mcp_schemas import MCPToolExecutionResponse, MCPHealthResponse
from backend.mcp.registry.server_config import TOOL_ROLE_PERMISSIONS
from backend.mcp.client.connection_manager import connection_manager

logger = logging.getLogger("CareCoord.IntegrationService")

ROLE_HIERARCHY = {
    "PATIENT": 1,
    "RECEPTIONIST": 2,
    "NURSE": 3,
    "DOCTOR": 4,
    "ADMIN": 5
}

class IntegrationService:
    def __init__(self):
        self.client = mcp_client

    def can_user_access_tool(self, user_role: str, tool_name: str) -> bool:
        """Evaluates whether the user's role meets the minimum required permission for an MCP tool."""
        required_role = TOOL_ROLE_PERMISSIONS.get(tool_name, "PATIENT")
        user_level = ROLE_HIERARCHY.get(user_role.upper(), 1)
        req_level = ROLE_HIERARCHY.get(required_role.upper(), 1)
        return user_level >= req_level

    def execute_tool_with_security(
        self,
        server_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        user: Optional[Any] = None,
        workflow_id: Optional[str] = None,
        db_session: Optional[Any] = None
    ) -> MCPToolExecutionResponse:
        """
        Executes an MCP tool with RBAC enforcement, timeout safety, and atomic SQLite audit logging.
        """
        user_role = getattr(user, "role", "PATIENT") if user else "PATIENT"
        user_id = str(getattr(user, "id", "anonymous")) if user else "SYSTEM"

        # 1. RBAC Guardrail
        if not self.can_user_access_tool(user_role, tool_name):
            required_role = TOOL_ROLE_PERMISSIONS.get(tool_name, "PATIENT")
            logger.warning(f"Access denied: User {user_id} ({user_role}) attempted unauthorized MCP tool '{tool_name}' (requires {required_role})")
            return MCPToolExecutionResponse(
                execution_id=f"MCP-DENIED-{tool_name}",
                server_id=server_id,
                tool_name=tool_name,
                status="BLOCKED",
                duration_ms=0.0,
                error=f"Permission Denied: Tool '{tool_name}' requires minimum role '{required_role}'. Your role is '{user_role}'."
            )

        # 2. Invoke via MCP Client
        response = self.client.execute_tool(
            server_id=server_id,
            tool_name=tool_name,
            arguments=arguments
        )

        # 3. Persistent Database Audit Logging
        self._log_execution_to_db(
            response=response,
            user_id=user_id,
            workflow_id=workflow_id,
            arguments=arguments,
            db_session=db_session
        )

        return response

    def _log_execution_to_db(
        self,
        response: MCPToolExecutionResponse,
        user_id: str,
        workflow_id: Optional[str],
        arguments: Dict[str, Any],
        db_session: Optional[Any]
    ):
        """Persists the tool execution into the SQLite mcp_tool_executions table."""
        from backend.database.database import SessionLocal
        from backend.database.models import MCPToolExecution
        
        # Avoid logging sensitive argument values (passwords, tokens)
        sanitized_args = {k: ("***" if "token" in k.lower() or "password" in k.lower() else v) for k, v in arguments.items()}

        db = db_session if db_session else SessionLocal()
        close_after = db_session is None
        try:
            record = MCPToolExecution(
                execution_id=response.execution_id,
                server_id=response.server_id,
                tool_name=response.tool_name,
                user_id=user_id,
                workflow_id=workflow_id,
                arguments=sanitized_args,
                result=response.result or {},
                status=response.status,
                duration_ms=response.duration_ms,
                error_summary=response.error
            )
            db.add(record)
            db.commit()
        except Exception as e:
            logger.warning(f"Failed to record MCP tool execution log: {e}")
            if close_after:
                db.rollback()
        finally:
            if close_after:
                db.close()

    def get_health(self) -> MCPHealthResponse:
        """Retrieves global MCP system health and response metrics."""
        servers = self.client.list_servers()
        total_servers = len(servers)
        connected_servers = len([s for s in servers if s.status == "CONNECTED"])
        total_tools = len(self.client.discover_tools())
        
        stats = connection_manager.get_health_stats(
            total_servers=total_servers,
            connected_servers=connected_servers,
            total_tools=total_tools
        )
        return MCPHealthResponse(
            status=stats["status"],
            total_servers=stats["total_servers"],
            connected_servers=stats["connected_servers"],
            total_tools=stats["total_tools"],
            avg_response_time_ms=stats["avg_response_time_ms"],
            success_rate=stats["success_rate"]
        )

    def get_audit_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves recent external MCP tool execution records from database."""
        from backend.database.database import SessionLocal
        from backend.database.models import MCPToolExecution

        db = SessionLocal()
        try:
            records = db.query(MCPToolExecution).order_by(MCPToolExecution.created_at.desc()).limit(limit).all()
            return [
                {
                    "execution_id": r.execution_id,
                    "server_id": r.server_id,
                    "tool_name": r.tool_name,
                    "user_id": r.user_id,
                    "workflow_id": r.workflow_id,
                    "status": r.status,
                    "duration_ms": r.duration_ms,
                    "error_summary": r.error_summary,
                    "created_at": r.created_at.isoformat()
                }
                for r in records
            ]
        finally:
            db.close()

integration_service = IntegrationService()
