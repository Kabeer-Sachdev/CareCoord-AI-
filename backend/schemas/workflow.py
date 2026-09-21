from datetime import datetime
from typing import Optional, List, Any, Dict, Literal
from pydantic import BaseModel, Field

REQUEST_TYPES = Literal["doctor_search", "appointment", "patient_information", "unknown"]
URGENCY_LEVELS = Literal["normal", "urgent", "critical"]

class WorkflowRequest(BaseModel):
    message: str = Field(..., example="I need an appointment with a cardiologist tomorrow.")


class WorkflowParseResult(BaseModel):
    request_type: REQUEST_TYPES = Field(..., example="appointment")
    department: Optional[str] = Field(None, example="Cardiology")
    specialization: Optional[str] = Field(None, example="Cardiology")
    patient_id: Optional[str] = Field(None, example="P001")
    doctor_id: Optional[str] = Field(None, example="D001")
    urgency: URGENCY_LEVELS = Field(default="normal", example="normal")
    date: Optional[str] = Field(None, example="tomorrow")
    time: Optional[str] = Field(None)
    reason: Optional[str] = Field(None)
    missing_info: Optional[List[str]] = Field(default_factory=list)
    clarification_needed: bool = Field(default=False)
    clarification_prompt: Optional[str] = Field(None)


class WorkflowResponse(BaseModel):
    workflow_id: Optional[str] = None
    original_request: str
    parsed_request: WorkflowParseResult
    agent_used: str
    status: str  # success, clarification_required, error, REQUIRES_HUMAN_APPROVAL, COMPLETED
    requires_human_approval: bool = False
    recommendation: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    steps: List[str] = Field(default_factory=list)
    execution_events: Optional[List[Dict[str, Any]]] = Field(default_factory=list)


class WorkflowEventResponse(BaseModel):
    id: int
    workflow_id: str
    timestamp: str
    agent_name: str
    node_name: str
    event_type: str
    status: str
    tool_name: Optional[str] = None
    execution_time_ms: Optional[int] = None
    details: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class WorkflowRunResponse(BaseModel):
    id: int
    workflow_id: str
    original_request: str
    workflow_type: str
    status: str
    requires_human_approval: bool
    agent_used: Optional[str] = None
    recommendation: Optional[str] = None
    final_result: Optional[Dict[str, Any]] = None
    started_at: str
    completed_at: Optional[str] = None
    events: List[WorkflowEventResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class WorkflowApprovalRequest(BaseModel):
    action: Literal["approve", "reject"] = Field(..., example="approve")
    notes: Optional[str] = Field(None, example="Approved by shift supervisor")
