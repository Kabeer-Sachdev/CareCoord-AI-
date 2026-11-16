from typing import Dict, Any, List
import time
from backend.agents.state import CareCoordState
from backend.rag.services.rag_service import rag_service

class PolicyAgent:
    """
    Hospital Policy Agent for CareCoord LangGraph Orchestration.
    Answers administrative and operational questions grounded strictly
    in hospital documents via RAG retrieval pipeline.
    """

    def __init__(self, name: str = "Policy Agent"):
        self.name = name

    def process_node(self, state: CareCoordState) -> CareCoordState:
        """LangGraph node execution handler."""
        state["current_agent"] = self.name
        start_time = time.time()

        parsed = state.get("workflow_request", {})
        query = parsed.get("reason") or state.get("original_request", "")
        department = parsed.get("department")

        # Query RAG service
        rag_response = rag_service.ask_policy(query=query, department=department, top_k=4)

        elapsed_ms = int((time.time() - start_time) * 1000)

        result_data = {
            "query": rag_response.query,
            "answer": rag_response.answer,
            "sources": [s.model_dump() for s in rag_response.sources],
            "confidence_score": rag_response.confidence_score,
            "retrieval_count": rag_response.retrieval_count,
            "insufficient_information": rag_response.insufficient_information,
            "department": rag_response.department,
            "execution_time_ms": rag_response.execution_time_ms
        }

        state["policy_result"] = {
            "agent": self.name,
            "status": "insufficient_information" if rag_response.insufficient_information else "success",
            "data": result_data
        }

        # Track execution in state
        if "executed_agents" not in state or state["executed_agents"] is None:
            state["executed_agents"] = []
        if self.name not in state["executed_agents"]:
            state["executed_agents"].append(self.name)

        # Append execution event log
        log_entry = {
            "timestamp": time.strftime("%H:%M:%S"),
            "agent_name": self.name,
            "node_name": "policy_retrieval",
            "event_type": "rag_policy_search",
            "status": "success",
            "tool_name": "rag_service.ask_policy",
            "execution_time_ms": elapsed_ms,
            "details": {
                "summary": f"Retrieved {rag_response.retrieval_count} grounded chunk(s) (Confidence: {rag_response.confidence_score}).",
                "retrieval_count": rag_response.retrieval_count,
                "confidence_score": rag_response.confidence_score,
                "insufficient_info": rag_response.insufficient_information
            }
        }
        if "execution_log" not in state or state["execution_log"] is None:
            state["execution_log"] = []
        state["execution_log"].append(log_entry)

        return state
