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
    original_request: str
    parsed_request: WorkflowParseResult
    agent_used: str
    status: str  # success, clarification_required, error
    recommendation: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    steps: List[str] = Field(default_factory=list)
