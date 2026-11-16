"""
MCP Connection Manager.
Manages connection lifecycles, health checks, round-trip latency statistics, and error tracking across servers.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
import time

class MCPConnectionManager:
    def __init__(self):
        self._execution_times: List[float] = []
        self._successful_calls: int = 0
        self._failed_calls: int = 0
        self._connection_events: List[Dict[str, Any]] = []

    def record_call(self, server_id: str, tool_name: str, duration_ms: float, success: bool, error: Optional[str] = None):
        """Records an execution call for latency and reliability analytics."""
        self._execution_times.append(duration_ms)
        if len(self._execution_times) > 500:
            self._execution_times.pop(0)

        if success:
            self._successful_calls += 1
        else:
            self._failed_calls += 1

        self._connection_events.append({
            "timestamp": datetime.utcnow().isoformat(),
            "server_id": server_id,
            "tool_name": tool_name,
            "duration_ms": round(duration_ms, 2),
            "success": success,
            "error": error
        })
        if len(self._connection_events) > 100:
            self._connection_events.pop(0)

    def get_health_stats(self, total_servers: int, connected_servers: int, total_tools: int) -> Dict[str, Any]:
        """Calculates global MCP operational health metrics."""
        total_calls = self._successful_calls + self._failed_calls
        success_rate = round((self._successful_calls / total_calls * 100.0), 1) if total_calls > 0 else 100.0
        avg_latency = round(sum(self._execution_times) / len(self._execution_times), 2) if self._execution_times else 0.0

        status = "HEALTHY"
        if connected_servers == 0:
            status = "CRITICAL_OFFLINE"
        elif connected_servers < total_servers or success_rate < 90.0:
            status = "DEGRADED"

        return {
            "status": status,
            "total_servers": total_servers,
            "connected_servers": connected_servers,
            "total_tools": total_tools,
            "avg_response_time_ms": avg_latency,
            "success_rate": success_rate,
            "total_calls_monitored": total_calls
        }

    def get_recent_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Returns recent execution events."""
        return self._connection_events[-limit:]

connection_manager = MCPConnectionManager()
