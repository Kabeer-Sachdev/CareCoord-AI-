import os
import sys
from pathlib import Path

# Add project root to python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.database.database import SessionLocal, init_db
from backend.database.models import PolicyDocument
from backend.rag.services.rag_service import rag_service

DEFAULT_DOCUMENTS = [
    {
        "filename": "Patient_Admission_Policy.txt",
        "title": "Patient Admission Procedures Policy",
        "department": "Patient Admissions"
    },
    {
        "filename": "Appointment_Cancellation_Policy.txt",
        "title": "Appointment Cancellation & Rescheduling Rules",
        "department": "Outpatient Services"
    },
    {
        "filename": "Emergency_Admission_Workflow.txt",
        "title": "Emergency Admission & Trauma Center Workflow",
        "department": "Emergency Medicine"
    },
    {
        "filename": "Bed_Allocation_Guidelines.txt",
        "title": "Inpatient Bed Allocation & Utilization Guidelines",
        "department": "Bed Management"
    },
    {
        "filename": "Hospital_Visiting_Hours.txt",
        "title": "Hospital Visiting Hours & Visitor Code of Conduct",
        "department": "Hospital Administration"
    },
    {
        "filename": "Patient_Discharge_Procedure.txt",
        "title": "Patient Discharge & Transition of Care Procedure",
        "department": "Clinical Quality"
    }
]

def seed_policies(db=None):
    """
    Ingests all default policy documents in data/hospital_documents into SQLite and ChromaDB.
    """
    init_db()
    close_db_on_exit = False
    if db is None:
        db = SessionLocal()
        close_db_on_exit = True

    docs_dir = Path(__file__).resolve().parent.parent.parent / "data" / "hospital_documents"
    print(f"Scanning for policy documents in: {docs_dir}")

    ingested_count = 0
    try:
        for item in DEFAULT_DOCUMENTS:
            file_path = docs_dir / item["filename"]
            if not file_path.exists():
                print(f"File not found: {file_path}")
                continue

            # Check if already indexed
            existing = db.query(PolicyDocument).filter(
                PolicyDocument.filename == item["filename"],
                PolicyDocument.status == "INDEXED"
            ).first()

            if existing:
                print(f"Policy already indexed: {item['title']} ({existing.chunk_count} chunks)")
                continue

            print(f"Ingesting: {item['title']}...")
            doc = rag_service.ingest_document(
                file_path=str(file_path),
                title=item["title"],
                department=item["department"],
                db=db
            )
            print(f"Indexed: {doc.title} -> {doc.chunk_count} chunks (ID: {doc.document_id})")
            ingested_count += 1

        print(f"Policy ingestion completed. Newly indexed: {ingested_count} documents.")
        return ingested_count
    finally:
        if close_db_on_exit:
            db.close()

if __name__ == "__main__":
    seed_policies()
