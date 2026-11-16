from typing import Dict, Any, Literal
import time
from langgraph.graph import StateGraph, START, END
from backend.agents.state import CareCoordState
from backend.agents.coordinator_agent import CoordinatorAgent
from backend.agents.patient_agent import PatientAgent
from backend.agents.doctor_agent import DoctorAgent
from backend.agents.appointment_agent import AppointmentAgent
from backend.agents.validation_agent import ValidationAgent
from backend.agents.policy_agent import PolicyAgent
from backend.agents.prediction_agent import PredictionAgent
from backend.agents.optimization_agent import OptimizationAgent
from backend.agents.mcp_agent import MCPAgent
from backend.services.llm_parser_service import parse_workflow_request

coordinator_agent = CoordinatorAgent()
patient_agent_node = PatientAgent()
doctor_agent_node = DoctorAgent()
appointment_agent_node = AppointmentAgent()
validation_agent_node = ValidationAgent()
policy_agent_node = PolicyAgent()
prediction_agent_node = PredictionAgent()
optimization_agent_node = OptimizationAgent()
mcp_agent_node = MCPAgent()

def parse_request_node(state: CareCoordState) -> CareCoordState:
    """Graph Node: Parses original natural language request into structured JSON parameters."""
    start_time = time.time()
    state["current_agent"] = "Request Parser"
    state["iteration_count"] = state.get("iteration_count", 0) + 1

    parsed = parse_workflow_request(state["original_request"])
    state["workflow_request"] = parsed.model_dump()

    elapsed_ms = int((time.time() - start_time) * 1000)
    log_entry = {
        "timestamp": time.strftime("%H:%M:%S"),
        "agent_name": "Request Parser",
        "node_name": "parse_request",
        "event_type": "parse_request",
        "status": "success",
        "execution_time_ms": elapsed_ms,
        "details": {
            "summary": f"Parsed query into request_type '{parsed.request_type}' (Urgency: {parsed.urgency}).",
            "parsed": parsed.model_dump()
        }
    }
    if "execution_log" not in state or state["execution_log"] is None:
        state["execution_log"] = []
    state["execution_log"].append(log_entry)
    return state

def coordinator_node(state: CareCoordState) -> CareCoordState:
    """Graph Node: Coordinator Agent decision engine."""
    return coordinator_agent.process(state)

def patient_agent_graph_node(state: CareCoordState) -> CareCoordState:
    """Graph Node: Patient Agent."""
    return patient_agent_node.process_node(state)

def doctor_agent_graph_node(state: CareCoordState) -> CareCoordState:
    """Graph Node: Doctor Agent."""
    return doctor_agent_node.process_node(state)

def appointment_agent_graph_node(state: CareCoordState) -> CareCoordState:
    """Graph Node: Appointment Agent."""
    return appointment_agent_node.process_node(state)

def policy_agent_graph_node(state: CareCoordState) -> CareCoordState:
    """Graph Node: Hospital Policy Agent."""
    return policy_agent_node.process_node(state)

def prediction_agent_graph_node(state: CareCoordState) -> CareCoordState:
    """Graph Node: ML Resource Prediction Agent."""
    return prediction_agent_node.process_node(state)

def optimization_agent_graph_node(state: CareCoordState) -> CareCoordState:
    """Graph Node: Resource Allocation and Optimization Agent."""
    return optimization_agent_node.process_node(state)

def mcp_agent_graph_node(state: CareCoordState) -> CareCoordState:
    """Graph Node: MCP External Hospital Interoperability Agent."""
    return mcp_agent_node.process_node(state)

def validation_graph_node(state: CareCoordState) -> CareCoordState:
    """Graph Node: Operational Validation Agent."""
    res = validation_agent_node.process(state)
    if "validation" not in res.get("executed_agents", []):
        res.setdefault("executed_agents", []).append("validation")
    return res

def final_response_node(state: CareCoordState) -> CareCoordState:
    """Graph Node: Formats final operational recommendation and completes execution."""
    start_time = time.time()
    state["current_agent"] = "Orchestrator"

    if not state.get("final_recommendation"):
        req_type = state.get("workflow_request", {}).get("request_type", "workflow")
        state["final_recommendation"] = {
            "agent_used": state.get("current_agent", "Coordinator Agent"),
            "status": state.get("status", "COMPLETED"),
            "recommendation": f"Completed operational {req_type} processing.",
            "data": {},
            "steps": [e.get("details", {}).get("summary", e["event_type"]) for e in state.get("execution_log", [])]
        }

    elapsed_ms = int((time.time() - start_time) * 1000)
    log_entry = {
        "timestamp": time.strftime("%H:%M:%S"),
        "agent_name": "Orchestrator",
        "node_name": "final_response",
        "event_type": "workflow_completed",
        "status": state.get("status", "COMPLETED"),
        "execution_time_ms": elapsed_ms,
        "details": {"summary": f"Workflow finished with status '{state.get('status')}'."}
    }
    state["execution_log"].append(log_entry)
    return state


def route_next_node(state: CareCoordState) -> str:
    """Conditional Edge Routing Logic for LangGraph."""
    status = state.get("status")
    iteration = state.get("iteration_count", 0)

    # 1. Safety Limit: Infinite loop prevention
    if iteration >= 10:
        state["status"] = "FAILED"
        state["error"] = "Maximum execution iteration depth reached."
        return "final_response"

    # 2. Early Termination States
    if status in ["NEEDS_CLARIFICATION", "FAILED", "REQUIRES_HUMAN_APPROVAL"]:
        return "final_response"

    required = state.get("required_agents", [])
    executed = state.get("executed_agents", [])

    # 3. If required agents not calculated yet, go to Coordinator
    if not required:
        return "coordinator"

    # 4. Route to next unexecuted required agent
    if "Doctor Agent" in required and "Doctor Agent" not in executed:
        return "doctor_agent"

    if "Appointment Agent" in required and "Appointment Agent" not in executed:
        # Doctor Agent should execute first if present
        if "Doctor Agent" in required and "Doctor Agent" not in executed:
            return "doctor_agent"
        return "appointment_agent"

    if "Patient Agent" in required and "Patient Agent" not in executed:
        return "patient_agent"

    if "Policy Agent" in required and "Policy Agent" not in executed:
        return "policy_agent"

    if "Prediction Agent" in required and "Prediction Agent" not in executed:
        return "prediction_agent"

    if "Optimization Agent" in required and "Optimization Agent" not in executed:
        return "optimization_agent"

    if "MCP Agent" in required and "MCP Agent" not in executed:
        return "mcp_agent"

    # 5. Validation Node execution for appointments
    req_type = state.get("workflow_request", {}).get("request_type")
    if req_type == "appointment" and "validation" not in executed:
        return "validation"

    # 6. Return to Coordinator for final recommendation compilation if not completed
    if status != "COMPLETED":
        return "coordinator"

    return "final_response"


def build_carecoord_graph() -> StateGraph:
    """Build and compile the CareCoord LangGraph StateGraph."""
    builder = StateGraph(CareCoordState)

    # Add Nodes
    builder.add_node("parse_request", parse_request_node)
    builder.add_node("coordinator", coordinator_node)
    builder.add_node("patient_agent", patient_agent_graph_node)
    builder.add_node("doctor_agent", doctor_agent_graph_node)
    builder.add_node("appointment_agent", appointment_agent_graph_node)
    builder.add_node("policy_agent", policy_agent_graph_node)
    builder.add_node("prediction_agent", prediction_agent_graph_node)
    builder.add_node("optimization_agent", optimization_agent_graph_node)
    builder.add_node("mcp_agent", mcp_agent_graph_node)
    builder.add_node("validation", validation_graph_node)
    builder.add_node("final_response", final_response_node)

    # Entrypoint
    builder.set_entry_point("parse_request")

    # Edges from parse_request to coordinator
    builder.add_edge("parse_request", "coordinator")

    # Conditional Edges from coordinator
    builder.add_conditional_edges(
        "coordinator",
        route_next_node,
        {
            "doctor_agent": "doctor_agent",
            "appointment_agent": "appointment_agent",
            "patient_agent": "patient_agent",
            "policy_agent": "policy_agent",
            "prediction_agent": "prediction_agent",
            "optimization_agent": "optimization_agent",
            "mcp_agent": "mcp_agent",
            "validation": "validation",
            "coordinator": "coordinator",
            "final_response": "final_response"
        }
    )

    # Agent nodes return back to conditional router via coordinator
    builder.add_edge("patient_agent", "coordinator")
    builder.add_edge("doctor_agent", "coordinator")
    builder.add_edge("appointment_agent", "coordinator")
    builder.add_edge("policy_agent", "coordinator")
    builder.add_edge("prediction_agent", "coordinator")
    builder.add_edge("optimization_agent", "coordinator")
    builder.add_edge("mcp_agent", "coordinator")
    builder.add_edge("validation", "coordinator")

    # Final response finishes graph
    builder.add_edge("final_response", END)

    return builder.compile()

# Global compiled graph engine instance
carecoord_graph = build_carecoord_graph()
