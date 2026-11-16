from typing import List, Dict, Any

POLICY_SYSTEM_PROMPT = """You are the CareCoord Hospital Policy Intelligence Assistant.
Your sole role is to answer questions regarding hospital operational policies, administrative guidelines, admission/discharge procedures, emergency workflows, visiting hours, and resource allocation rules based EXCLUSIVELY on the provided hospital policy excerpts.

CRITICAL RULES:
1. Grounding: Answer ONLY using the facts directly stated in the excerpts below. Do NOT assume, extrapolate, or bring in outside medical or policy knowledge.
2. Insufficient Information: If the provided excerpts do not contain the answer, you MUST state: "The available hospital policy documents do not contain sufficient information to answer this question." Do not attempt to guess or invent rules.
3. Medical Disclaimer: Never provide clinical advice, medical diagnoses, treatment recommendations, or drug prescriptions. Always remind users to consult clinical staff for patient medical care.
4. Citations: Reference the policy document title and relevant section or page number when providing the answer.
"""

def build_policy_prompt(query: str, chunks: List[Dict[str, Any]]) -> str:
    """
    Constructs a concise, grounded RAG prompt with the top retrieved context excerpts.
    """
    if not chunks:
        context_str = "No relevant policy documents were retrieved."
    else:
        context_items = []
        # Keep top 2 most relevant chunks to keep local Ollama generation fast (<5s)
        for i, c in enumerate(chunks[:2], 1):
            doc_name = c.get("document_name", "Unknown Document")
            page = f"Page {c.get('page_number')}" if c.get('page_number') else "General Section"
            dept = c.get("department", "General")
            content = c.get("content", "").strip()
            if len(content) > 400:
                content = content[:400] + "..."
            context_items.append(
                f"[Source {i}: {doc_name} ({dept}) - {page}]\n{content}"
            )
        context_str = "\n\n".join(context_items)

    prompt = f"""{POLICY_SYSTEM_PROMPT}

EXCERPTS FROM HOSPITAL POLICY DOCUMENTS:
----------------------------------------
{context_str}
----------------------------------------

QUESTION:
{query}

GROUNDED ANSWER (Include source document citations):"""

    return prompt
