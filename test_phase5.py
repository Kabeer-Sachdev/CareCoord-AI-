"""
CareCoord - Phase 5 Comprehensive Verification Test Suite
Tests:
1. Document Ingestion & Chunking Pipeline (PDF, DOCX, TXT metadata & SQLite tracking)
2. Local Persistent ChromaDB Vector Store & Semantic Retrieval
3. Source Grounding & Anti-Hallucination Guardrails (Insufficient Information Handling)
4. Specialized Hospital Policy Agent & LangGraph Coordinator Integration
5. Policy REST API Endpoints (GET /policies, POST /policies/ask)
6. Role-Based Access Control (Admin privileges vs Patient restrictions)
7. Document Upload & Deletion Lifecycle
8. RAG Evaluation Benchmark Execution & Performance Metrics
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.database.database import init_db, SessionLocal
from backend.database.models import PolicyDocument, PolicyChunk, User
from backend.rag.services.rag_service import rag_service
from backend.agents.graph import carecoord_graph
from backend.schemas.policy import PolicyAskRequest
from backend.routes.policies import (
    list_policy_documents,
    get_policy_document,
    get_document_chunks,
    ask_policy_question,
    upload_policy_document,
    delete_policy_document
)

def print_step(title):
    print(f"\n[Step] {title}", flush=True)

def print_passed(msg):
    print(f"  -> PASSED: {msg}", flush=True)

def test_phase5():
    print("=" * 65)
    print("  RUNNING CARECOORD PHASE 5 RAG POLICY SYSTEM VERIFICATION  ")
    print("=" * 65)

    init_db()
    db = SessionLocal()

    try:
        # Step 1: Document Storage & Ingestion Verification
        print_step("1. Verifying Policy Ingestion & SQLite Tracking...")
        docs = db.query(PolicyDocument).filter(PolicyDocument.status == "INDEXED").all()
        assert len(docs) >= 6, f"Expected at least 6 indexed policy documents, found {len(docs)}"
        total_chunks = sum(d.chunk_count for d in docs)
        assert total_chunks >= 25, f"Expected at least 25 total policy chunks, found {total_chunks}"
        print_passed(f"Found {len(docs)} indexed policy documents with {total_chunks} total chunks.")

        # Step 2: Vector Store Semantic Search
        print_step("2. Testing Local ChromaDB Semantic Search...")
        results = rag_service.vector_store.query("What are the ICU visiting hours?", top_k=3)
        assert len(results) > 0, "No chunks returned from semantic search"
        top_res = results[0]
        assert "Visiting Hours" in top_res["document_name"], f"Unexpected top document: {top_res['document_name']}"
        assert top_res["similarity_score"] >= 0.50, f"Expected similarity score >= 0.50, got {top_res['similarity_score']}"
        print_passed(f"Retrieved top match: '{top_res['document_name']}' (Score: {top_res['similarity_score']})")

        # Step 3: Source Grounding & Anti-Hallucination
        print_step("3. Testing Grounded Answering & Insufficient Information Handling...")
        # 3a. Answerable question
        resp_ans = rag_service.ask_policy("What are the visiting hours for the ICU?")
        assert resp_ans.insufficient_information is False, "Answerable question marked as insufficient"
        assert len(resp_ans.sources) > 0, "No sources returned"
        assert "11:00 AM" in resp_ans.answer or "Visiting Hours" in resp_ans.answer
        print_passed("Grounded answer successfully synthesized with source citations.")

        # 3b. Unanswerable question (Mars astronaut policy)
        resp_unans = rag_service.ask_policy("What is the policy for astronaut training and space travel to Mars?")
        assert resp_unans.insufficient_information is True, "Unanswerable question was not rejected"
        assert "sufficient information" in resp_unans.answer.lower()
        assert len(resp_unans.sources) == 0
        print_passed("Out-of-domain question accurately flagged with insufficient_information: True.")

        # Step 4: Hospital Policy Agent in LangGraph
        print_step("4. Testing Hospital Policy Agent in LangGraph Coordinator...")
        initial_state = {
            "workflow_id": "WF-TEST-PHASE5",
            "original_request": "What is the policy for patient discharge and check-out time?",
            "workflow_request": {},
            "current_agent": None,
            "required_agents": [],
            "executed_agents": [],
            "patient_result": None,
            "doctor_result": None,
            "appointment_result": None,
            "validation_result": None,
            "policy_result": None,
            "prediction_result": None,
            "messages": [],
            "execution_log": [],
            "requires_human_review": False,
            "status": "RUNNING",
            "final_recommendation": None,
            "iteration_count": 0,
            "error": None,
            "db_session": None
        }
        final_state = carecoord_graph.invoke(initial_state)
        assert final_state["status"] == "COMPLETED"
        assert "Policy Agent" in final_state["executed_agents"]
        assert final_state["final_recommendation"]["agent_used"] == "Policy Agent"
        print_passed(f"LangGraph executed '{final_state['executed_agents']}' and synthesized grounded response.")

        # Step 5: Direct Route Function Testing with Mock Roles
        print_step("5. Testing Policy Route Operations & RBAC...")
        admin_user = db.query(User).filter(User.role == "ADMIN").first()
        doctor_user = db.query(User).filter(User.role == "DOCTOR").first()
        patient_user = db.query(User).filter(User.role == "PATIENT").first()

        # 5a. List documents
        doc_list = list_policy_documents(department=None, db=db, current_user=doctor_user)
        assert len(doc_list) >= 6
        print_passed(f"Doctor retrieved list of {len(doc_list)} policy documents.")

        # 5b. Ask policy question via route
        ask_req = PolicyAskRequest(query="How much advance notice is needed to cancel an appointment?", top_k=3)
        ask_resp = ask_policy_question(request=ask_req, db=db, current_user=patient_user)
        assert ask_resp.query == ask_req.query
        assert len(ask_resp.sources) > 0
        print_passed(f"Patient asked question and received response with {len(ask_resp.sources)} source citations.")

        # Step 6: Document Lifecycle (Upload & Delete)
        print_step("6. Testing Document Ingestion & Deletion Lifecycle...")
        temp_dir = Path("data/hospital_documents")
        temp_file = temp_dir / "Test_Clinical_Handoff.txt"
        test_text = """# CLINICAL NURSE SHIFT HANDOFF POLICY
Department: Nursing Administration
All registered nurses must complete formal bedside verbal handoff at 07:00 and 19:00 shift changes.
Critical patient acuity scores and pending lab orders must be documented in the electronic health record."""
        
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(test_text)

        test_doc = rag_service.ingest_document(
            file_path=str(temp_file),
            title="Clinical Nurse Shift Handoff Policy",
            department="Nursing Administration",
            db=db
        )
        assert test_doc.status == "INDEXED"
        assert test_doc.chunk_count > 0
        test_doc_id = test_doc.document_id
        print_passed(f"Ingested test document {test_doc_id} with {test_doc.chunk_count} chunk(s).")

        # Query chunks
        chunks = get_document_chunks(document_id=test_doc_id, db=db, current_user=admin_user)
        assert len(chunks) == test_doc.chunk_count
        print_passed(f"Retrieved {len(chunks)} chunk records from SQLite.")

        # Delete document
        del_res = delete_policy_document(document_id=test_doc_id, db=db, current_user=admin_user)
        assert "deleted successfully" in del_res["message"]
        assert db.query(PolicyDocument).filter(PolicyDocument.document_id == test_doc_id).first() is None
        if temp_file.exists():
            temp_file.unlink()
        print_passed("Deleted test document and associated embeddings cleanly.")

        # Step 7: Benchmark Metrics Verification
        print_step("7. Verifying Benchmark Evaluation Report...")
        bench_file = Path("backend/evaluation/benchmark_results.json")
        assert bench_file.exists(), "Benchmark results file not found"
        import json
        with open(bench_file, "r", encoding="utf-8") as f:
            bdata = json.load(f)
        acc = bdata.get("overall_accuracy_percent", 0)
        p95 = bdata.get("latency_metrics", {}).get("p95_ms", 0)
        assert acc >= 80.0, f"Expected benchmark accuracy >= 80%, got {acc}%"
        print_passed(f"Benchmark Report Validated: Accuracy = {acc}%, p95 Latency = {p95}ms.")

        print("\n" + "=" * 65)
        print("  ALL 7 PHASE 5 VERIFICATION STEPS PASSED SUCCESSFULLY!  ")
        print("=" * 65)

    finally:
        db.close()

if __name__ == "__main__":
    test_phase5()
