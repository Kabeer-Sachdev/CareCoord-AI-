import os
import re
import json
from typing import Optional
from backend.schemas.workflow import WorkflowParseResult
from backend.services.llm_client import llm_client

SYSTEM_PROMPT = """You are a hospital workflow request parser for CareCoord.
You convert natural-language operational requests into structured workflow information.
You do NOT diagnose patients, prescribe medication, recommend treatment, or make clinical decisions.

Your task is to extract structured parameters from the user's operational query.
Valid request_type values: "doctor_search", "appointment", "patient_information", "policy", "forecast", "optimization", "mcp_integration", "unknown"
Valid urgency values: "normal", "urgent", "critical"

If mandatory information is missing for an action (such as booking an appointment without specifying a department or doctor), set clarification_needed = true and list missing fields in missing_info.
"""

def heuristic_parse_request(message: str) -> WorkflowParseResult:
    """Fallback rule-based natural language parser for offline / key-less operation."""
    msg = message.strip()
    msg_lower = msg.lower()

    # Identify departments / specializations
    dept_map = {
        "cardio": "Cardiology",
        "cardiologist": "Cardiology",
        "cardiology": "Cardiology",
        "neuro": "Neurology",
        "neurologist": "Neurology",
        "neurology": "Neurology",
        "ortho": "Orthopedics",
        "orthopedic": "Orthopedics",
        "orthopedics": "Orthopedics",
        "derma": "Dermatology",
        "dermatologist": "Dermatology",
        "dermatology": "Dermatology",
        "general medicine": "General Medicine",
        "general doctor": "General Medicine",
        "pedia": "Pediatrics",
        "pediatrician": "Pediatrics",
        "pediatrics": "Pediatrics",
        "emergency": "Emergency Medicine",
        "er doctor": "Emergency Medicine"
    }

    found_dept = None
    for kw, dept in dept_map.items():
        if kw in msg_lower:
            found_dept = dept
            break

    # Extract Patient ID (e.g. P001, P014)
    patient_id_match = re.search(r'\b(p\d{3,4})\b', msg_lower)
    found_patient_id = patient_id_match.group(1).upper() if patient_id_match else None

    # Extract Doctor ID (e.g. D001)
    doctor_id_match = re.search(r'\b(d\d{3,4})\b', msg_lower)
    found_doctor_id = doctor_id_match.group(1).upper() if doctor_id_match else None

    # Extract urgency
    urgency = "normal"
    if "emergency" in msg_lower or "critical" in msg_lower or "immediately" in msg_lower:
        urgency = "critical"
    elif "urgent" in msg_lower or "asap" in msg_lower:
        urgency = "urgent"

    # Extract date hints
    date_hint = None
    if "tomorrow" in msg_lower:
        date_hint = "tomorrow"
    elif "today" in msg_lower:
        date_hint = "today"
    elif "next week" in msg_lower:
        date_hint = "next week"

    # Classify Request Type
    # 0. Policy Question / Guidelines lookup
    policy_keywords = [
        "policy", "guideline", "guidelines", "protocol", "visiting hours",
        "discharge procedure", "admission procedure", "cancellation policy",
        "reschedule policy", "rules", "rule", "bed allocation guideline",
        "refund policy", "billing policy", "how do i admit", "how do i discharge",
        "what are the visiting hours", "what is the policy"
    ]
    if any(pk in msg_lower for pk in policy_keywords):
        return WorkflowParseResult(
            request_type="policy",
            department=found_dept,
            urgency=urgency,
            reason=msg
        )

    # 0.1 Forecast / Prediction Request
    forecast_keywords = [
        "forecast", "predict", "prediction", "how many beds", "expected arrivals",
        "expected emergency", "expected appointments", "resource demand", "future workload",
        "occupancy tomorrow", "arrivals tomorrow", "emergency tomorrow", "demand tomorrow"
    ]
    if any(fk in msg_lower for fk in forecast_keywords):
        return WorkflowParseResult(
            request_type="forecast",
            department=found_dept or "Cardiology",
            urgency=urgency,
            date=date_hint or "tomorrow",
            reason=msg
        )

    # 0.2 Resource Optimization / Allocation Request
    optimization_keywords = [
        "optimize", "optimization", "optimal schedule", "allocate beds", "allocate bed", "allocate doctor",
        "doctor scheduling", "schedule optimization", "resource allocation", "reallocate",
        "solve schedule", "optimal allocation", "shift assignment", "shift optimization",
        "bed allocation optimization", "appointment optimization"
    ]
    if any(ok in msg_lower for ok in optimization_keywords):
        return WorkflowParseResult(
            request_type="optimization",
            department=found_dept or "Cardiology",
            doctor_id=found_doctor_id,
            patient_id=found_patient_id,
            urgency=urgency,
            date=date_hint or "tomorrow",
            reason=msg
        )

    # 0.3 MCP External Tool Integration (Lab, Pharmacy, External HIS)
    mcp_keywords = [
        "laboratory", "lab service", "lab test", "lab availability", "specimen", "sample test",
        "sample status", "blood count", "troponin", "reagent", "pharmacy", "medication", "drug stock",
        "product availability", "amoxicillin", "atorvastatin", "metformin", "paracetamol", "pantoprazole",
        "salbutamol", "insulin", "dispensary", "formulary", "mcp tool", "external service", "his sandbox"
    ]
    if any(mk in msg_lower for mk in mcp_keywords):
        return WorkflowParseResult(
            request_type="mcp_integration",
            department=found_dept or "Laboratory",
            patient_id=found_patient_id,
            urgency=urgency,
            reason=msg
        )

    # 1. Ambiguous/incomplete appointment booking
    if msg_lower.strip() in ["book an appointment.", "book an appointment", "schedule appointment", "i want an appointment"]:
        return WorkflowParseResult(
            request_type="appointment",
            urgency=urgency,
            missing_info=["department", "doctor"],
            clarification_needed=True,
            clarification_prompt="Which department or doctor would you like to book an appointment with?"
        )

    # 2. Patient Information lookup (if patient ID or explicit patient lookup request is given)
    if found_patient_id or ("patient" in msg_lower and not ("book" in msg_lower or "schedule" in msg_lower)):
        return WorkflowParseResult(
            request_type="patient_information",
            patient_id=found_patient_id,
            urgency=urgency
        )

    # 3. Appointment scheduling request (e.g. "I need an appointment with a cardiologist")
    if "appointment" in msg_lower or "schedule" in msg_lower or "book" in msg_lower:
        return WorkflowParseResult(
            request_type="appointment",
            department=found_dept,
            specialization=found_dept,
            patient_id=found_patient_id,
            doctor_id=found_doctor_id,
            urgency=urgency,
            date=date_hint
        )

    # 4. Doctor Search request
    if "doctor" in msg_lower or "available" in msg_lower or "find" in msg_lower or found_dept or found_doctor_id:
        return WorkflowParseResult(
            request_type="doctor_search",
            department=found_dept,
            specialization=found_dept,
            doctor_id=found_doctor_id,
            urgency=urgency
        )

    # 5. Fallback unknown
    return WorkflowParseResult(
        request_type="unknown",
        missing_info=["request_type"],
        clarification_needed=True,
        clarification_prompt="I couldn't identify the hospital workflow action requested. Please specify if you need a doctor search, appointment scheduling, or patient information lookup."
    )


def parse_workflow_request(message: str) -> WorkflowParseResult:
    """
    Parses a natural-language request into a structured WorkflowParseResult model.
    Uses local Ollama (qwen2.5:3b) on the user's laptop, with graceful fallback to heuristic parser.
    """
    try:
        prompt = (
            f"Parse the following operational hospital request into a JSON object strictly matching these keys: "
            f"\"request_type\" (must be one of: \"doctor_search\", \"appointment\", \"patient_information\", \"policy\", \"forecast\", \"optimization\", \"unknown\"), "
            f"\"department\" (string or null), \"specialization\" (string or null), "
            f"\"patient_id\" (string or null), \"doctor_id\" (string or null), "
            f"\"urgency\" (\"normal\", \"urgent\", or \"critical\"), \"date\" (string or null), "
            f"\"missing_info\" (list of strings), \"clarification_needed\" (boolean), "
            f"\"clarification_prompt\" (string or null).\n\n"
            f"Request: \"{message}\"\n\nJSON Output:"
        )
        resp_text = llm_client.generate(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.1,
            json_mode=True,
            timeout=25
        )
        if resp_text:
            cleaned = resp_text.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1].lstrip("json").strip()
            data = json.loads(cleaned)
            # Ensure mandatory keys exist
            if "request_type" in data:
                return WorkflowParseResult(**data)
    except Exception:
        pass

    # High-accuracy heuristic fallback
    return heuristic_parse_request(message)
