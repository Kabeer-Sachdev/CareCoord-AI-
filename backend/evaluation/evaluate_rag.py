import time
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.rag.services.rag_service import rag_service
from backend.evaluation.benchmark_dataset import BENCHMARK_QUESTIONS

DOC_TITLE_MAP = {
    "Patient_Admission_Policy.txt": "Admission",
    "Appointment_Cancellation_Policy.txt": "Appointment Cancellation",
    "Emergency_Admission_Workflow.txt": "Emergency Admission",
    "Bed_Allocation_Guidelines.txt": "Bed Allocation",
    "Hospital_Visiting_Hours.txt": "Visiting Hours",
    "Patient_Discharge_Procedure.txt": "Discharge"
}

def run_rag_evaluation():
    print("=" * 70)
    print("CareCoord RAG Policy Intelligence - Benchmark Evaluation Suite")
    print(f"Total Questions: {len(BENCHMARK_QUESTIONS)}")
    print("=" * 70)

    results = []
    latencies = []
    retrieval_hits = 0
    answerable_count = 0
    correct_insufficient_count = 0
    unanswerable_count = 0

    for item in BENCHMARK_QUESTIONS:
        qid = item["id"]
        qtext = item["question"]
        is_ans = item["is_answerable"]
        expected_doc = item.get("expected_doc")
        keywords = item.get("expected_answer_keywords", [])

        start_t = time.time()
        response = rag_service.ask_policy(query=qtext, top_k=4)
        elapsed_ms = round((time.time() - start_t) * 1000, 2)
        latencies.append(elapsed_ms)

        retrieved_docs = [s.document_name for s in response.sources]
        answer_text = response.answer

        # Evaluation checks
        doc_hit = False
        if is_ans:
            answerable_count += 1
            # Check if expected document was retrieved
            if expected_doc:
                keyword = DOC_TITLE_MAP.get(expected_doc, expected_doc.lower())
                doc_hit = any(keyword.lower() in d.lower() for d in retrieved_docs)
                if doc_hit:
                    retrieval_hits += 1

            # Check keyword presence in answer
            keyword_matches = sum(1 for kw in keywords if kw.lower() in answer_text.lower())
            grounding_score = round(keyword_matches / max(len(keywords), 1), 2)
            passed = (not response.insufficient_information) and (doc_hit or grounding_score >= 0.3)
        else:
            unanswerable_count += 1
            # Should correctly detect insufficient information
            passed = response.insufficient_information
            if passed:
                correct_insufficient_count += 1
            grounding_score = 1.0 if passed else 0.0

        res_entry = {
            "id": qid,
            "category": item["category"],
            "question": qtext,
            "is_answerable": is_ans,
            "insufficient_flag": response.insufficient_information,
            "retrieved_sources_count": response.retrieval_count,
            "top_source": retrieved_docs[0] if retrieved_docs else None,
            "doc_hit": doc_hit if is_ans else None,
            "confidence_score": response.confidence_score,
            "passed": passed,
            "latency_ms": elapsed_ms
        }
        results.append(res_entry)

        status_sym = "[PASS]" if passed else "[FAIL]"
        print(f"{status_sym} {qid} ({item['category']}): {elapsed_ms}ms | Ans: {not response.insufficient_information} | Hit: {doc_hit if is_ans else 'N/A'}")

    # Summary Metrics
    latencies.sort()
    p50_latency = latencies[len(latencies) // 2]
    p95_latency = latencies[int(len(latencies) * 0.95)]
    mean_latency = round(sum(latencies) / len(latencies), 2)
    total_passed = sum(1 for r in results if r["passed"])

    retrieval_precision = round((retrieval_hits / max(answerable_count, 1)) * 100, 1)
    insufficient_accuracy = round((correct_insufficient_count / max(unanswerable_count, 1)) * 100, 1)
    overall_accuracy = round((total_passed / len(BENCHMARK_QUESTIONS)) * 100, 1)

    print("\n" + "=" * 70)
    print("EVALUATION SUMMARY REPORT:")
    print("=" * 70)
    print(f"Total Evaluated Questions: {len(BENCHMARK_QUESTIONS)}")
    print(f"Overall Benchmark Accuracy: {overall_accuracy}% ({total_passed}/{len(BENCHMARK_QUESTIONS)})")
    print(f"Retrieval Precision (Answerable): {retrieval_precision}% ({retrieval_hits}/{answerable_count})")
    print(f"Insufficient Info Accuracy (Negative): {insufficient_accuracy}% ({correct_insufficient_count}/{unanswerable_count})")
    print(f"Mean Latency: {mean_latency} ms | p50: {p50_latency} ms | p95: {p95_latency} ms")
    print("=" * 70)

    # Save results to JSON
    report_path = Path(__file__).resolve().parent / "benchmark_results.json"
    report_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_questions": len(BENCHMARK_QUESTIONS),
        "overall_accuracy_percent": overall_accuracy,
        "retrieval_precision_percent": retrieval_precision,
        "insufficient_accuracy_percent": insufficient_accuracy,
        "latency_metrics": {
            "mean_ms": mean_latency,
            "p50_ms": p50_latency,
            "p95_ms": p95_latency
        },
        "results": results
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)
    print(f"Detailed benchmark metrics saved to: {report_path}")

    return report_data

if __name__ == "__main__":
    run_rag_evaluation()
