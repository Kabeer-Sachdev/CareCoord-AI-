from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.database.models import WorkflowRun, WorkflowEvent, User
from backend.schemas.workflow import WorkflowRequest, WorkflowResponse, WorkflowParseResult
from backend.agents.state import CareCoordState
from backend.agents.graph import carecoord_graph
from backend.tools import appointment_tools
from backend.realtime.connection_manager import connection_manager
from backend.realtime.events import EventType
from backend.services.notification_service import (
    notify_workflow_approval_required,
    create_notification,
)

class WorkflowService:
    """Service layer managing LangGraph state executions and SQLite workflow audit records."""

    def generate_workflow_id(self, db: Session) -> str:
        """Generate next sequential human-readable workflow ID like WF-000001, WF-000002..."""
        count = db.query(WorkflowRun).count()
        return f"WF-{count + 1:06d}"

    def process_workflow(self, db: Session, request: WorkflowRequest, user: Optional[User] = None) -> WorkflowResponse:
        raw_msg = request.message.strip()
        wf_id = self.generate_workflow_id(db)

        # 1. Create DB WorkflowRun audit entry
        run = WorkflowRun(
            workflow_id=wf_id,
            original_request=raw_msg,
            workflow_type="pending",
            status="RUNNING",
            requires_human_approval=False,
            requested_by=user.username if user else None,
            requested_role=user.role if user else None,
            started_at=datetime.utcnow()
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        # Broadcast started event
        connection_manager.broadcast_sync(
            event_type=EventType.WORKFLOW_STARTED,
            payload={
                "workflow_id": wf_id,
                "request": raw_msg,
                "requested_by": run.requested_by,
                "requested_role": run.requested_role
            }
        )

        # 2. Build initial CareCoordState
        initial_state: CareCoordState = {
            "workflow_id": wf_id,
            "original_request": raw_msg,
            "workflow_request": {},
            "current_agent": "Orchestrator",
            "required_agents": [],
            "executed_agents": [],
            "patient_result": None,
            "doctor_result": None,
            "appointment_result": None,
            "validation_result": None,
            "messages": [],
            "execution_log": [],
            "requires_human_review": False,
            "status": "RUNNING",
            "final_recommendation": None,
            "iteration_count": 0,
            "error": None,
            "db_session": db
        }

        # 3. Execute LangGraph Workflow Engine
        final_state = carecoord_graph.invoke(initial_state)

        parsed_dict = final_state.get("workflow_request", {})
        parsed_model = WorkflowParseResult(**parsed_dict) if parsed_dict else WorkflowParseResult(
            request_type="unknown",
            urgency="normal"
        )

        final_rec = final_state.get("final_recommendation") or {}
        agent_used = final_rec.get("agent_used", "Coordinator Agent")
        status_str = final_state.get("status", "COMPLETED")

        # Normalize status string for backward compatibility
        legacy_status = status_str.lower()
        if status_str == "NEEDS_CLARIFICATION":
            legacy_status = "clarification_required"
        elif status_str in ["COMPLETED", "APPROVED", "REQUIRES_HUMAN_APPROVAL"]:
            legacy_status = "success"

        # 4. Save Execution Log Events to DB
        execution_events = []
        for log in final_state.get("execution_log", []):
            event = WorkflowEvent(
                workflow_id=wf_id,
                timestamp=datetime.utcnow(),
                agent_name=log.get("agent_name", "Agent"),
                node_name=log.get("node_name", "node"),
                event_type=log.get("event_type", "event"),
                status=log.get("status", "success"),
                tool_name=log.get("tool_name"),
                execution_time_ms=log.get("execution_time_ms", 0),
                details=log.get("details")
            )
            db.add(event)
            execution_events.append({
                "timestamp": log.get("timestamp", ""),
                "agent_name": log.get("agent_name"),
                "node_name": log.get("node_name"),
                "event_type": log.get("event_type"),
                "status": log.get("status"),
                "tool_name": log.get("tool_name"),
                "execution_time_ms": log.get("execution_time_ms"),
                "details": log.get("details")
            })

        # 5. Update WorkflowRun state in DB
        run.workflow_type = parsed_model.request_type
        run.status = status_str
        run.requires_human_approval = final_state.get("requires_human_review", False)
        run.agent_used = agent_used
        run.recommendation = final_rec.get("recommendation")
        run.final_result = final_rec
        if status_str != "REQUIRES_HUMAN_APPROVAL":
            run.completed_at = datetime.utcnow()

        db.commit()
        db.refresh(run)

        # Broadcast status and trigger notifications
        if status_str == "REQUIRES_HUMAN_APPROVAL":
            notify_workflow_approval_required(db, run)

        connection_manager.broadcast_sync(
            event_type=EventType.WORKFLOW_STATUS_CHANGED,
            payload={
                "workflow_id": wf_id,
                "status": run.status,
                "requires_human_approval": run.requires_human_approval,
                "workflow_type": run.workflow_type,
                "recommendation": run.recommendation
            }
        )

        # 6. Extract step list for UI display
        steps = []
        for log in final_state.get("execution_log", []):
            summary = log.get("details", {}).get("summary")
            if summary:
                steps.append(summary)

        return WorkflowResponse(
            workflow_id=wf_id,
            original_request=raw_msg,
            parsed_request=parsed_model,
            agent_used=agent_used,
            status=legacy_status,
            requires_human_approval=final_state.get("requires_human_review", False),
            recommendation=final_rec.get("recommendation"),
            data=final_rec.get("data"),
            steps=steps,
            execution_events=execution_events
        )

    def get_workflow_runs(self, db: Session) -> List[WorkflowRun]:
        """Retrieve all historical workflow runs."""
        return db.query(WorkflowRun).order_by(WorkflowRun.id.desc()).all()

    def get_workflow_by_id(self, db: Session, workflow_id: str) -> Optional[WorkflowRun]:
        """Retrieve specific workflow run by string ID."""
        return db.query(WorkflowRun).filter(WorkflowRun.workflow_id == workflow_id).first()

    def get_workflow_events(self, db: Session, workflow_id: str) -> List[WorkflowEvent]:
        """Retrieve event execution log for a specific workflow."""
        return db.query(WorkflowEvent).filter(WorkflowEvent.workflow_id == workflow_id).order_by(WorkflowEvent.id.asc()).all()

    def approve_workflow(self, db: Session, workflow_id: str, notes: Optional[str] = None) -> WorkflowRun:
        """Human-in-the-Loop Approval Action: Triggers database mutation."""
        run = self.get_workflow_by_id(db, workflow_id)
        if not run:
            raise ValueError(f"Workflow '{workflow_id}' not found.")
        if run.status != "REQUIRES_HUMAN_APPROVAL":
            raise ValueError(f"Workflow '{workflow_id}' is in status '{run.status}' and does not require approval.")

        final_res = run.final_result or {}
        rec_data = final_res.get("data", {})

        patient_id = rec_data.get("patient_id", "P001")
        doctor_id = rec_data.get("doctor_id")
        dept = rec_data.get("department", "Cardiology")
        appt_date = rec_data.get("appointment_date", "tomorrow")
        appt_time = rec_data.get("appointment_time", "10:30 AM")

        # Perform actual database mutation
        created_appt = None
        if doctor_id:
            created_appt = appointment_tools.create_appointment_in_db(
                db=db,
                patient_id=patient_id,
                doctor_id=doctor_id,
                appointment_date=appt_date,
                appointment_time=appt_time,
                department=dept,
                reason=f"Approved AI workflow {workflow_id}"
            )

        # Update Workflow Run state
        run.status = "COMPLETED"
        run.requires_human_approval = False
        run.completed_at = datetime.utcnow()
        if rec_data:
            rec_data["created_appointment"] = created_appt
            run.final_result["data"] = rec_data
            run.recommendation += f" [APPROVED & CREATED: Appointment ID {created_appt.get('appointment_id') if created_appt else 'N/A'}]"

        # Log Approval Event
        event = WorkflowEvent(
            workflow_id=workflow_id,
            timestamp=datetime.utcnow(),
            agent_name="Hospital Staff",
            node_name="human_approval",
            event_type="approval_granted",
            status="approved",
            execution_time_ms=0,
            details={
                "summary": f"Human staff approved appointment creation for patient {patient_id} with doctor {doctor_id}.",
                "notes": notes,
                "created_appointment": created_appt
            }
        )
        db.add(event)
        db.commit()
        db.refresh(run)

        # Broadcast real-time notifications and events
        if created_appt:
            connection_manager.broadcast_sync(
                event_type=EventType.APPOINTMENT_CREATED,
                payload=created_appt
            )
        connection_manager.broadcast_sync(
            event_type=EventType.WORKFLOW_STATUS_CHANGED,
            payload={
                "workflow_id": workflow_id,
                "status": run.status,
                "recommendation": run.recommendation
            }
        )
        return run

    def reject_workflow(self, db: Session, workflow_id: str, notes: Optional[str] = None) -> WorkflowRun:
        """Human-in-the-Loop Rejection Action."""
        run = self.get_workflow_by_id(db, workflow_id)
        if not run:
            raise ValueError(f"Workflow '{workflow_id}' not found.")
        if run.status != "REQUIRES_HUMAN_APPROVAL":
            raise ValueError(f"Workflow '{workflow_id}' is in status '{run.status}' and cannot be rejected.")

        run.status = "REJECTED"
        run.requires_human_approval = False
        run.completed_at = datetime.utcnow()

        event = WorkflowEvent(
            workflow_id=workflow_id,
            timestamp=datetime.utcnow(),
            agent_name="Hospital Staff",
            node_name="human_approval",
            event_type="approval_rejected",
            status="rejected",
            execution_time_ms=0,
            details={
                "summary": f"Human staff rejected the proposed workflow recommendation.",
                "notes": notes
            }
        )
        db.add(event)
        db.commit()
        db.refresh(run)

        connection_manager.broadcast_sync(
            event_type=EventType.WORKFLOW_STATUS_CHANGED,
            payload={
                "workflow_id": workflow_id,
                "status": run.status
            }
        )
        return run

workflow_service = WorkflowService()
