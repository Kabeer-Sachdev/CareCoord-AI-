from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.database.models import User
from backend.auth.dependencies import get_optional_current_user
from backend.schemas.workflow import (
    WorkflowRequest,
    WorkflowResponse,
    WorkflowRunResponse,
    WorkflowEventResponse,
    WorkflowApprovalRequest
)
from backend.services.workflow_service import workflow_service
from backend.services.audit_service import log_audit

router = APIRouter(tags=["AI Workflow Orchestration"])

@router.post("/workflow/request", response_model=WorkflowResponse, summary="Process natural-language hospital request (Phase 2 & 3 Compatible)")
def handle_workflow_request(
    request: WorkflowRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Receives a natural-language operational query, parses it into structured parameters via LLM/Heuristic parser,
    orchestrates execution via LangGraph multi-agent graph engine, and returns database-backed results.
    """
    try:
        resp = workflow_service.process_workflow(db, request, user=current_user)
        log_audit(
            db,
            user=current_user,
            action="EXECUTE_WORKFLOW",
            entity_type="WorkflowRun",
            entity_id=resp.workflow_id,
            meta_data={"status": resp.status, "agent_used": resp.agent_used}
        )
        return resp
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow processing error: {str(exc)}"
        )


@router.post("/workflows", response_model=WorkflowResponse, summary="Start a new LangGraph workflow execution")
def create_workflow_run(
    request: WorkflowRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Starts a new stateful multi-agent workflow execution."""
    try:
        resp = workflow_service.process_workflow(db, request, user=current_user)
        log_audit(
            db,
            user=current_user,
            action="EXECUTE_WORKFLOW",
            entity_type="WorkflowRun",
            entity_id=resp.workflow_id
        )
        return resp
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow execution failed: {str(exc)}"
        )


@router.get("/workflows", summary="List historical workflow runs")
def get_workflow_runs(db: Session = Depends(get_db)):
    """Retrieve list of all historical workflow execution runs."""
    runs = workflow_service.get_workflow_runs(db)
    return [
        {
            "id": r.id,
            "workflow_id": r.workflow_id,
            "original_request": r.original_request,
            "workflow_type": r.workflow_type,
            "status": r.status,
            "requires_human_approval": r.requires_human_approval,
            "agent_used": r.agent_used,
            "recommendation": r.recommendation,
            "final_result": r.final_result,
            "started_at": str(r.started_at),
            "completed_at": str(r.completed_at) if r.completed_at else None
        }
        for r in runs
    ]


@router.get("/workflows/{workflow_id}", summary="Get details of a specific workflow run")
def get_workflow_details(workflow_id: str, db: Session = Depends(get_db)):
    """Retrieve details and execution results of a specific workflow by workflow_id."""
    run = workflow_service.get_workflow_by_id(db, workflow_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' not found."
        )

    events = workflow_service.get_workflow_events(db, workflow_id)

    return {
        "id": run.id,
        "workflow_id": run.workflow_id,
        "original_request": run.original_request,
        "workflow_type": run.workflow_type,
        "status": run.status,
        "requires_human_approval": run.requires_human_approval,
        "agent_used": run.agent_used,
        "recommendation": run.recommendation,
        "final_result": run.final_result,
        "started_at": str(run.started_at),
        "completed_at": str(run.completed_at) if run.completed_at else None,
        "events": [
            {
                "id": e.id,
                "workflow_id": e.workflow_id,
                "timestamp": str(e.timestamp),
                "agent_name": e.agent_name,
                "node_name": e.node_name,
                "event_type": e.event_type,
                "status": e.status,
                "tool_name": e.tool_name,
                "execution_time_ms": e.execution_time_ms,
                "details": e.details
            }
            for e in events
        ]
    }


@router.get("/workflows/{workflow_id}/events", summary="Get live execution event logs for a workflow")
def get_workflow_events(workflow_id: str, db: Session = Depends(get_db)):
    """Retrieve execution log events for a workflow run."""
    events = workflow_service.get_workflow_events(db, workflow_id)
    return [
        {
            "id": e.id,
            "workflow_id": e.workflow_id,
            "timestamp": str(e.timestamp),
            "agent_name": e.agent_name,
            "node_name": e.node_name,
            "event_type": e.event_type,
            "status": e.status,
            "tool_name": e.tool_name,
            "execution_time_ms": e.execution_time_ms,
            "details": e.details
        }
        for e in events
    ]


@router.post("/workflows/{workflow_id}/approve", summary="Human Staff Approval for pending workflow")
def approve_workflow(
    workflow_id: str,
    req: Optional[WorkflowApprovalRequest] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Approves a pending workflow and executes the actual appointment creation database mutation."""
    notes = req.notes if req else None
    try:
        updated_run = workflow_service.approve_workflow(db, workflow_id, notes=notes)
        log_audit(
            db,
            user=current_user,
            action="APPROVE_WORKFLOW",
            entity_type="WorkflowRun",
            entity_id=workflow_id,
            meta_data={"notes": notes}
        )
        return {
            "status": "success",
            "message": f"Workflow {workflow_id} approved successfully and committed to database.",
            "workflow_id": updated_run.workflow_id,
            "workflow_status": updated_run.status,
            "recommendation": updated_run.recommendation
        }
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post("/workflows/{workflow_id}/reject", summary="Human Staff Rejection for pending workflow")
def reject_workflow(
    workflow_id: str,
    req: Optional[WorkflowApprovalRequest] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Rejects a pending workflow without performing database mutations."""
    notes = req.notes if req else None
    try:
        updated_run = workflow_service.reject_workflow(db, workflow_id, notes=notes)
        log_audit(
            db,
            user=current_user,
            action="REJECT_WORKFLOW",
            entity_type="WorkflowRun",
            entity_id=workflow_id,
            meta_data={"notes": notes}
        )
        return {
            "status": "success",
            "message": f"Workflow {workflow_id} rejected.",
            "workflow_id": updated_run.workflow_id,
            "workflow_status": updated_run.status
        }
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
