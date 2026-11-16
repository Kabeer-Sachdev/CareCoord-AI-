from typing import TypedDict, List, Dict, Any, Optional

class CareCoordState(TypedDict):
    workflow_id: str
    original_request: str
    workflow_request: Dict[str, Any]  # Parsed request structure
    current_agent: Optional[str]
    required_agents: List[str]
    executed_agents: List[str]

    patient_result: Optional[Dict[str, Any]]
    doctor_result: Optional[Dict[str, Any]]
    appointment_result: Optional[Dict[str, Any]]
    validation_result: Optional[Dict[str, Any]]
    policy_result: Optional[Dict[str, Any]]
    prediction_result: Optional[Dict[str, Any]]
    optimization_result: Optional[Dict[str, Any]]
    mcp_result: Optional[Dict[str, Any]]

    messages: List[Dict[str, Any]]
    execution_log: List[Dict[str, Any]]

    requires_human_review: bool
    status: str  # RUNNING, NEEDS_CLARIFICATION, REQUIRES_HUMAN_APPROVAL, APPROVED, REJECTED, COMPLETED, FAILED
    final_recommendation: Optional[Dict[str, Any]]
    iteration_count: int
    error: Optional[str]
    db_session: Any  # Session object passed at execution runtime
