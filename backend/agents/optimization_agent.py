from typing import Dict, Any, List
import time
from datetime import datetime, timedelta
from backend.agents.state import CareCoordState

class OptimizationAgent:
    """
    Hospital Resource Optimization Agent for CareCoord LangGraph Orchestration.
    Leverages Google OR-Tools Mixed Integer Linear Programming (MIP) to solve:
    1. Appointment scheduling (minimizing wait time, avoiding conflicts, balancing workload)
    2. Doctor shift scheduling (using ML demand forecasts, respecting working hours)
    3. Bed allocation (prioritizing critical/urgent triage, ward matching, factoring occupancy)
    
    Generates proposed allocation plans that require human review and approval
    before committing to operational database tables.
    """

    def __init__(self, name: str = "Optimization Agent"):
        self.name = name

    def process_node(self, state: CareCoordState) -> CareCoordState:
        """LangGraph node execution handler."""
        from backend.tools import optimization_tools
        state["current_agent"] = self.name
        start_time = time.time()

        parsed = state.get("workflow_request", {})
        query = (parsed.get("reason") or state.get("original_request", "")).lower()
        dept = parsed.get("department") or "Cardiology"
        target_date = parsed.get("date")
        if not target_date or target_date in ["tomorrow", "today", "next week"]:
            target_date = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")

        db = state.get("db_session")

        # Determine optimization type
        if "bed" in query or "ward" in query or "occupancy" in query:
            res = optimization_tools.recommend_bed_allocation(
                department=dept,
                target_date=target_date,
                db=db
            )
            tool_name = "optimization_tools.recommend_bed_allocation"
            summary = (
                f"Generated bed allocation plan for {dept} on {target_date}: "
                f"Status: {res['solver_status']}, Allocated: {res['allocated_count']}/{res['total_requests']} requests. "
                f"Requires human approval ({res['optimization_id']})."
            )
        elif "doctor" in query or "shift" in query or "staff" in query:
            res = optimization_tools.optimize_doctor_schedule(
                department=dept,
                target_date=target_date,
                db=db
            )
            tool_name = "optimization_tools.optimize_doctor_schedule"
            summary = (
                f"Generated doctor shift schedule for {dept} on {target_date}: "
                f"Status: {res['solver_status']}, Allocated: {res['allocated_count']}/{res['total_requests']} shifts. "
                f"Requires human approval ({res['optimization_id']})."
            )
        else:
            # Default to appointment schedule optimization
            res = optimization_tools.optimize_appointment_schedule(
                department=dept,
                target_date=target_date,
                db=db
            )
            tool_name = "optimization_tools.optimize_appointment_schedule"
            summary = (
                f"Generated appointment schedule optimization for {dept} on {target_date}: "
                f"Status: {res['solver_status']}, Allocated: {res['allocated_count']}/{res['total_requests']} appointments. "
                f"Requires human approval ({res['optimization_id']})."
            )

        elapsed_ms = int((time.time() - start_time) * 1000)

        state["optimization_result"] = {
            "agent": self.name,
            "status": "REQUIRES_HUMAN_APPROVAL",
            "summary": summary,
            "data": res
        }
        state["requires_human_review"] = True

        # Track execution in state
        if "executed_agents" not in state or state["executed_agents"] is None:
            state["executed_agents"] = []
        if self.name not in state["executed_agents"]:
            state["executed_agents"].append(self.name)

        # Append execution event log
        log_entry = {
            "timestamp": time.strftime("%H:%M:%S"),
            "agent_name": self.name,
            "node_name": "resource_optimization",
            "event_type": "or_tools_optimization",
            "status": "REQUIRES_HUMAN_APPROVAL",
            "tool_name": tool_name,
            "execution_time_ms": elapsed_ms,
            "details": {
                "summary": summary,
                "optimization_id": res.get("optimization_id"),
                "solver_status": res.get("solver_status"),
                "department": dept,
                "target_date": target_date
            }
        }
        if "execution_log" not in state or state["execution_log"] is None:
            state["execution_log"] = []
        state["execution_log"].append(log_entry)

        return state
