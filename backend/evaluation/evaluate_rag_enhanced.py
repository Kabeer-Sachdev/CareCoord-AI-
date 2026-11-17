"""
Phase 9 RAG Information Retrieval Evaluation Suite
Evaluates ChromaDB Vector Search and Grounded Policy Synthesis using standard IR metrics:
- Recall@1, Recall@3, Recall@5
- Precision@1, Precision@3, Precision@5
- Mean Reciprocal Rank (MRR)
- Insufficient Information Rejection Accuracy (Anti-Hallucination Rate)
- Semantic Retrieval Latency (p50, p95, p99)
"""

import time
from typing import Dict, Any, List
from backend.rag.services.rag_service import rag_service
from backend.evaluation.benchmark_dataset import BENCHMARK_QUESTIONS

DOC_KEYWORD_MAP = {
    "Patient_Admission_Policy.txt": ["admission", "identification", "consent", "intake"],
    "Appointment_Cancellation_Policy.txt": ["cancellation", "reschedul", "no-show", "fee"],
    "Emergency_Admission_Workflow.txt": ["emergency", "triage", "trauma", "stabilization"],
    "Bed_Allocation_Guidelines.txt": ["bed", "ward", "icu", "transfer"],
    "Hospital_Visiting_Hours.txt": ["visiting", "visitor", "hours", "icu visiting"],
    "Patient_Discharge_Procedure.txt": ["discharge", "medication reconciliation", "checkout", "summary"]
}


def evaluate_rag_retrieval() -> Dict[str, Any]:
    total_q = len(BENCHMARK_QUESTIONS)
    answerable_items = [q for q in BENCHMARK_QUESTIONS if q["is_answerable"]]
    unanswerable_items = [q for q in BENCHMARK_QUESTIONS if not q["is_answerable"]]

    recalls = {1: 0, 3: 0, 5: 0}
    precisions = {1: 0, 3: 0, 5: 0}
    reciprocal_ranks = []
    latencies = []
    grounded_correct = 0
    insufficient_correct = 0

    for item in BENCHMARK_QUESTIONS:
        q = item["question"]
        is_ans = item["is_answerable"]
        exp_doc = item.get("expected_doc")

        t0 = time.time()
        # Retrieve top 5 chunks
        response = rag_service.ask_policy(query=q, top_k=5)
        elapsed_ms = round((time.time() - t0) * 1000, 2)
        latencies.append(elapsed_ms)

        retrieved_docs = [s.document_name for s in response.sources]

        if is_ans:
            target_keywords = DOC_KEYWORD_MAP.get(exp_doc, [exp_doc.replace(".txt", "").replace("_", " ").lower()])

            # Rank of first relevant document chunk
            first_rank = None
            for idx, doc_name in enumerate(retrieved_docs):
                if any(kw.lower() in doc_name.lower() for kw in target_keywords):
                    if first_rank is None:
                        first_rank = idx + 1

            if first_rank is not None:
                reciprocal_ranks.append(1.0 / first_rank)
            else:
                reciprocal_ranks.append(0.0)

            # Evaluate Recall@K and Precision@K
            for k in [1, 3, 5]:
                sub_retrieved = retrieved_docs[:k]
                relevant_in_k = sum(1 for d in sub_retrieved if any(kw.lower() in d.lower() for kw in target_keywords))

                # Recall@K (since 1 relevant ground-truth doc exists per benchmark question)
                if relevant_in_k > 0:
                    recalls[k] += 1

                # Precision@K
                precisions[k] += (relevant_in_k / k)

            # Groundedness: checked if response is non-empty and cites sources
            if len(response.sources) > 0 and not response.insufficient_information:
                grounded_correct += 1

        else:
            # Unanswerable / out-of-domain question
            if response.insufficient_information or len(response.sources) == 0:
                insufficient_correct += 1

    ans_len = max(len(answerable_items), 1)
    unans_len = max(len(unanswerable_items), 1)

    mrr = round(sum(reciprocal_ranks) / ans_len, 4)
    recall_at_1 = round((recalls[1] / ans_len) * 100, 2)
    recall_at_3 = round((recalls[3] / ans_len) * 100, 2)
    recall_at_5 = round((recalls[5] / ans_len) * 100, 2)

    precision_at_1 = round((precisions[1] / ans_len) * 100, 2)
    precision_at_3 = round((precisions[3] / ans_len) * 100, 2)
    precision_at_5 = round((precisions[5] / ans_len) * 100, 2)

    insufficient_acc = round((insufficient_correct / unans_len) * 100, 2)
    overall_accuracy = round(((grounded_correct + insufficient_correct) / total_q) * 100, 2)

    latencies.sort()
    p50 = latencies[int(len(latencies) * 0.50)]
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)]

    return {
        "total_benchmark_questions": total_q,
        "answerable_questions": len(answerable_items),
        "unanswerable_questions": len(unanswerable_items),
        "recall_at_1_pct": recall_at_1,
        "recall_at_3_pct": recall_at_3,
        "recall_at_5_pct": recall_at_5,
        "precision_at_1_pct": precision_at_1,
        "precision_at_3_pct": precision_at_3,
        "precision_at_5_pct": precision_at_5,
        "mean_reciprocal_rank_mrr": mrr,
        "anti_hallucination_accuracy_pct": insufficient_acc,
        "overall_groundedness_accuracy_pct": overall_accuracy,
        "latency_p50_ms": p50,
        "latency_p95_ms": p95,
        "latency_p99_ms": p99
    }


if __name__ == "__main__":
    res = evaluate_rag_retrieval()
    print("\n=======================================================")
    print("  PHASE 9 RAG RETRIEVAL & POLICY EVALUATION RESULTS")
    print("=======================================================")
    print(f"  Total Questions Evaluated:       {res['total_benchmark_questions']}")
    print(f"  Recall@1 / Recall@3 / Recall@5:  {res['recall_at_1_pct']}% / {res['recall_at_3_pct']}% / {res['recall_at_5_pct']}%")
    print(f"  Precision@1 / Precision@3:       {res['precision_at_1_pct']}% / {res['precision_at_3_pct']}%")
    print(f"  Mean Reciprocal Rank (MRR):      {res['mean_reciprocal_rank_mrr']}")
    print(f"  Anti-Hallucination Rejection:    {res['anti_hallucination_accuracy_pct']}%")
    print(f"  Overall Groundedness Accuracy:   {res['overall_groundedness_accuracy_pct']}%")
    print(f"  Latency (p50 / p95 / p99):       {res['latency_p50_ms']}ms / {res['latency_p95_ms']}ms / {res['latency_p99_ms']}ms")
    print("=======================================================")
