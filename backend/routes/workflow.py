from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.schemas.workflow import WorkflowRequest, WorkflowResponse
from backend.services.workflow_service import workflow_router

router = APIRouter(prefix="/workflow", tags=["AI Workflow Execution"])

@router.post("/request", response_model=WorkflowResponse, summary="Process natural-language hospital workflow request")
def handle_workflow_request(request: WorkflowRequest, db: Session = Depends(get_db)):
    """
    Receives a natural-language operational query, parses it into structured parameters via LLM,
    routes it to the appropriate specialized AI agent, and returns database-backed results.
    """
    try:
        return workflow_router.process_workflow(db, request)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow processing error: {str(exc)}"
        )
