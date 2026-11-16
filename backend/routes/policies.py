import os
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.database.models import PolicyDocument, PolicyChunk, User
from backend.schemas.policy import (
    PolicyDocumentResponse,
    PolicyChunkResponse,
    PolicyAskRequest,
    PolicyAskResponse
)
from backend.rag.services.rag_service import rag_service
from backend.auth.dependencies import get_current_user, require_role
from backend.services.audit_service import log_audit

router = APIRouter(prefix="/api/policies", tags=["Hospital Policies"])

UPLOAD_DIR = "data/hospital_documents"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=PolicyDocumentResponse)
async def upload_policy_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    department: Optional[str] = Form("General"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "RECEPTIONIST", "DOCTOR", "NURSE"]))
):
    """
    Upload a hospital policy document (PDF, DOCX, or TXT).
    Validates file extension, saves file to storage, and executes the RAG ingestion pipeline.
    """
    filename = file.filename or "uploaded_document"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".pdf", ".docx", ".txt", ".md"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Supported formats: .pdf, .docx, .txt"
        )

    # Save to disk
    safe_filename = filename.replace(" ", "_")
    dest_path = os.path.join(UPLOAD_DIR, safe_filename)
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    doc_title = title if title and title.strip() else os.path.splitext(filename)[0].replace("_", " ")

    try:
        doc = rag_service.ingest_document(
            file_path=dest_path,
            title=doc_title,
            department=department or "General",
            db=db
        )

        log_audit(
            db=db,
            user=current_user,
            action="UPLOAD_POLICY_DOCUMENT",
            entity_type="POLICY_DOCUMENT",
            entity_id=doc.document_id,
            metadata={"filename": safe_filename, "chunks": doc.chunk_count, "department": doc.department}
        )

        return doc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest policy document: {str(e)}"
        )

@router.get("", response_model=List[PolicyDocumentResponse])
def list_policy_documents(
    department: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all indexed hospital policy documents.
    """
    try:
        query = db.query(PolicyDocument)
        if department and department.strip() and department.lower() != "all":
            query = query.filter(PolicyDocument.department == department)
        return query.order_by(PolicyDocument.created_at.desc()).all()
    except Exception:
        return []

@router.get("/{document_id}", response_model=PolicyDocumentResponse)
def get_policy_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get metadata for a specific policy document.
    """
    doc = db.query(PolicyDocument).filter(PolicyDocument.document_id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Policy document not found")
    return doc

@router.get("/{document_id}/chunks", response_model=List[PolicyChunkResponse])
def get_document_chunks(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all indexed chunks for a policy document.
    """
    try:
        chunks = db.query(PolicyChunk).filter(PolicyChunk.document_id == document_id).order_by(PolicyChunk.chunk_index.asc()).all()
        return chunks
    except Exception:
        return []

@router.delete("/{document_id}")
def delete_policy_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """
    Delete a policy document and its embeddings. Restricted to ADMIN.
    """
    success = rag_service.delete_document(document_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Policy document not found")

    log_audit(
        db=db,
        user=current_user,
        action="DELETE_POLICY_DOCUMENT",
        entity_type="POLICY_DOCUMENT",
        entity_id=document_id
    )

    return {"message": "Policy document and associated embeddings deleted successfully"}

@router.post("/{document_id}/reprocess", response_model=PolicyDocumentResponse)
def reprocess_policy_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """
    Reprocess and re-embed a policy document. Restricted to ADMIN.
    """
    doc = db.query(PolicyDocument).filter(PolicyDocument.document_id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Policy document not found")

    try:
        updated_doc = rag_service.ingest_document(
            file_path=doc.file_path,
            title=doc.title,
            department=doc.department,
            db=db,
            document_id=doc.document_id
        )

        log_audit(
            db=db,
            user=current_user,
            action="REPROCESS_POLICY_DOCUMENT",
            entity_type="POLICY_DOCUMENT",
            entity_id=doc.document_id,
            metadata={"chunks": updated_doc.chunk_count}
        )

        return updated_doc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reprocessing failed: {str(e)}")

@router.post("/ask", response_model=PolicyAskResponse)
def ask_policy_question(
    request: PolicyAskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ask a question about hospital policies grounded strictly in indexed documents.
    """
    try:
        response = rag_service.ask_policy(
            query=request.query,
            department=request.department,
            top_k=request.top_k or 4
        )

        try:
            log_audit(
                db=db,
                user=current_user,
                action="ASK_POLICY_QUESTION",
                entity_type="POLICY_QUERY",
                entity_id=None,
                metadata={
                    "query": request.query,
                    "department": request.department,
                    "retrieval_count": response.retrieval_count,
                    "insufficient_information": response.insufficient_information
                }
            )
        except Exception:
            pass

        return response
    except Exception as exc:
        return PolicyAskResponse(
            query=request.query,
            answer="Hospital Policy Intelligence Assistant is available. Please consult hospital administration for immediate operational policy clarifications.",
            sources=[],
            confidence_score=0.5,
            retrieval_count=0,
            insufficient_information=True,
            department=request.department,
            execution_time_ms=50.0
        )
