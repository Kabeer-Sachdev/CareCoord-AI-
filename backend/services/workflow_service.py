from typing import Dict, Any
from sqlalchemy.orm import Session
from backend.schemas.workflow import WorkflowRequest, WorkflowResponse
from backend.services.llm_parser_service import parse_workflow_request
from backend.agents.patient_agent import PatientAgent
from backend.agents.doctor_agent import DoctorAgent
from backend.agents.appointment_agent import AppointmentAgent

class WorkflowRouter:
    """Deterministic request router for CareCoord Phase 2."""

    def __init__(self):
        self.patient_agent = PatientAgent()
        self.doctor_agent = DoctorAgent()
        self.appointment_agent = AppointmentAgent()

    def process_workflow(self, db: Session, request: WorkflowRequest) -> WorkflowResponse:
        raw_msg = request.message
        
        # Step 1: Parse natural language via LLM / Fallback parser
        parsed = parse_workflow_request(raw_msg)

        # Handle explicit clarification requirement
        if parsed.clarification_needed:
            return WorkflowResponse(
                original_request=raw_msg,
                parsed_request=parsed,
                agent_used="System Router",
                status="clarification_required",
                recommendation=parsed.clarification_prompt or "Please provide more details regarding your request.",
                data={"missing_info": parsed.missing_info},
                steps=["Parsed request", "Identified missing mandatory parameters", "Requested clarification"]
            )

        # Step 2: Route to appropriate Agent based on request_type
        if parsed.request_type == "appointment":
            agent_result = self.appointment_agent.process(db, parsed)
        elif parsed.request_type == "doctor_search":
            agent_result = self.doctor_agent.process(db, parsed)
        elif parsed.request_type == "patient_information":
            agent_result = self.patient_agent.process(db, parsed)
        else:
            return WorkflowResponse(
                original_request=raw_msg,
                parsed_request=parsed,
                agent_used="System Router",
                status="clarification_required",
                recommendation="I could not determine the specific hospital workflow requested. Please specify if you need doctor availability, appointment booking, or patient records.",
                steps=["Parsed request", "Unrecognized request type", "Prompted for request clarification"]
            )

        return WorkflowResponse(
            original_request=raw_msg,
            parsed_request=parsed,
            agent_used=agent_result["agent"],
            status=agent_result["status"],
            recommendation=agent_result["recommendation"],
            data=agent_result.get("data"),
            steps=agent_result.get("steps", [])
        )

workflow_router = WorkflowRouter()
