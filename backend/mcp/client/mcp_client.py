"""
MCP Client Implementation.
Connects to configured MCP servers, discovers available tools and JSON schemas, validates input arguments,
safely executes tools with timeout guardrails, and returns structured execution responses.
"""

import time
import uuid
import asyncio
import logging
from typing import Dict, Any, List, Optional

from backend.mcp.schemas.mcp_schemas import (
    MCPToolDefinition,
    MCPToolExecutionResponse
)
from backend.mcp.registry.server_registry import server_registry
from backend.mcp.registry.server_config import ALLOWED_MCP_TOOLS
from backend.mcp.client.connection_manager import connection_manager

logger = logging.getLogger("CareCoord.MCPClient")

class MCPClient:
    def __init__(self):
        self.registry = server_registry
        self.default_timeout_seconds = 10.0

    def list_servers(self):
        """Lists all configured MCP servers."""
        return self.registry.list_servers()

    def discover_tools(self, server_id: Optional[str] = None) -> List[MCPToolDefinition]:
        """Discovers tools exposed by connected MCP servers."""
        if server_id:
            return self.registry.get_discovered_tools(server_id)
        return self.registry.get_discovered_tools()

    def get_tool(self, server_id: str, tool_name: str) -> Optional[MCPToolDefinition]:
        """Finds a discovered tool definition by server ID and tool name."""
        tools = self.registry.get_discovered_tools(server_id)
        return next((t for t in tools if t.name == tool_name), None)

    def execute_tool(
        self,
        server_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        timeout: Optional[float] = None
    ) -> MCPToolExecutionResponse:
        """
        Executes an MCP tool on the target server with schema validation and safety guardrails.
        """
        start_time = time.time()
        exec_id = f"MCP-EXEC-{uuid.uuid4().hex[:8].upper()}"
        timeout_val = timeout or self.default_timeout_seconds

        # 1. Validate server registration & connection status
        server_meta = self.registry.get_server(server_id)
        if not server_meta:
            duration = (time.time() - start_time) * 1000.0
            connection_manager.record_call(server_id, tool_name, duration, False, "Unknown server")
            return MCPToolExecutionResponse(
                execution_id=exec_id,
                server_id=server_id,
                tool_name=tool_name,
                status="FAILED",
                duration_ms=round(duration, 2),
                error=f"MCP Server '{server_id}' is not registered."
            )

        if server_meta.status != "CONNECTED":
            duration = (time.time() - start_time) * 1000.0
            connection_manager.record_call(server_id, tool_name, duration, False, "Server disconnected")
            return MCPToolExecutionResponse(
                execution_id=exec_id,
                server_id=server_id,
                tool_name=tool_name,
                status="FAILED",
                duration_ms=round(duration, 2),
                error=f"MCP Server '{server_id}' is currently {server_meta.status}. Connection required before execution."
            )

        # 2. Validate tool security allowlist
        allowed_list = ALLOWED_MCP_TOOLS.get(server_id, [])
        if tool_name not in allowed_list:
            duration = (time.time() - start_time) * 1000.0
            connection_manager.record_call(server_id, tool_name, duration, False, "Tool not in allowlist")
            return MCPToolExecutionResponse(
                execution_id=exec_id,
                server_id=server_id,
                tool_name=tool_name,
                status="BLOCKED",
                duration_ms=round(duration, 2),
                error=f"Tool '{tool_name}' is not in the authorized security allowlist for server '{server_id}'."
            )

        # 3. Retrieve server instance
        instance = self.registry.get_server_instance(server_id)
        if not instance:
            duration = (time.time() - start_time) * 1000.0
            connection_manager.record_call(server_id, tool_name, duration, False, "Server instance unavailable")
            return MCPToolExecutionResponse(
                execution_id=exec_id,
                server_id=server_id,
                tool_name=tool_name,
                status="FAILED",
                duration_ms=round(duration, 2),
                error=f"Active server instance for '{server_id}' is unavailable."
            )

        # 4. Retrieve tool from server tool manager
        tool = instance._tool_manager.get_tool(tool_name)
        if not tool:
            duration = (time.time() - start_time) * 1000.0
            connection_manager.record_call(server_id, tool_name, duration, False, "Tool not found on server")
            return MCPToolExecutionResponse(
                execution_id=exec_id,
                server_id=server_id,
                tool_name=tool_name,
                status="FAILED",
                duration_ms=round(duration, 2),
                error=f"Tool '{tool_name}' is not registered on server '{server_id}'."
            )

        # 5. Argument Validation against MCP schema
        try:
            validated_args = tool.fn_metadata.validate_arguments(arguments)
        except Exception as val_exc:
            duration = (time.time() - start_time) * 1000.0
            connection_manager.record_call(server_id, tool_name, duration, False, f"Validation: {str(val_exc)}")
            return MCPToolExecutionResponse(
                execution_id=exec_id,
                server_id=server_id,
                tool_name=tool_name,
                status="FAILED",
                duration_ms=round(duration, 2),
                error=f"Input validation error for tool '{tool_name}': {str(val_exc)}"
            )

        # 6. Execution
        try:
            if asyncio.iscoroutinefunction(tool.fn):
                result = asyncio.run(asyncio.wait_for(tool.fn(**validated_args), timeout=timeout_val))
            else:
                result = tool.fn(**validated_args)

            duration = (time.time() - start_time) * 1000.0
            connection_manager.record_call(server_id, tool_name, duration, True)

            return MCPToolExecutionResponse(
                execution_id=exec_id,
                server_id=server_id,
                tool_name=tool_name,
                status="SUCCESS",
                result=result if isinstance(result, dict) else {"data": result},
                duration_ms=round(duration, 2),
                error=None
            )

        except asyncio.TimeoutError:
            duration = (time.time() - start_time) * 1000.0
            connection_manager.record_call(server_id, tool_name, duration, False, "Timeout")
            return MCPToolExecutionResponse(
                execution_id=exec_id,
                server_id=server_id,
                tool_name=tool_name,
                status="FAILED",
                duration_ms=round(duration, 2),
                error=f"Tool execution timed out after {timeout_val} seconds."
            )
        except Exception as exec_exc:
            duration = (time.time() - start_time) * 1000.0
            connection_manager.record_call(server_id, tool_name, duration, False, str(exec_exc))
            return MCPToolExecutionResponse(
                execution_id=exec_id,
                server_id=server_id,
                tool_name=tool_name,
                status="FAILED",
                duration_ms=round(duration, 2),
                error=f"Error executing tool '{tool_name}': {str(exec_exc)}"
            )

    async def execute_tool_async(
        self,
        server_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        timeout: Optional[float] = None
    ) -> MCPToolExecutionResponse:
        """Asynchronous execution wrapper."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.execute_tool(server_id, tool_name, arguments, timeout)
        )

    def execute_tool_sync(
        self,
        server_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        timeout: Optional[float] = None
    ) -> MCPToolExecutionResponse:
        """Alias for synchronous tool execution."""
        return self.execute_tool(server_id, tool_name, arguments, timeout)

mcp_client = MCPClient()
