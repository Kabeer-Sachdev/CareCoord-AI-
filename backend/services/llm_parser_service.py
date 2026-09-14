import os
import re
import json
from typing import Optional
from backend.schemas.workflow import WorkflowParseResult

SYSTEM_PROMPT = """You are a hospital workflow request parser for CareCoord.
You convert natural-language operational requests into structured workflow information.
You do NOT diagnose patients, prescribe medication, recommend treatment, or make clinical decisions.

Your task is to extract structured parameters from the user's operational query.
Valid request_type values: "doctor_search", "appointment", "patient_information", "unknown"
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
    Attempts LLM parsing if GEMINI_API_KEY / OPENAI_API_KEY is configured,
    otherwise uses high-accuracy fallback parser.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        # Use clean rule-based parser when API key is absent
        return heuristic_parse_request(message)

    try:
        # If Gemini API key is present, attempt SDK call
        import google.genai as genai
        client = genai.Client(api_key=api_key)
        prompt = f"{SYSTEM_PROMPT}\n\nParse this hospital request into JSON format strictly matching keys (request_type, department, specialization, patient_id, doctor_id, urgency, date, missing_info, clarification_needed, clarification_prompt):\n'{message}'"
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        text_resp = response.text.strip()
        # Clean JSON markdown fences if any
        if text_resp.startswith("```"):
            text_resp = text_resp.split("```")[1].lstrip("json").strip()
        data = json.loads(text_resp)
        return WorkflowParseResult(**data)
    except Exception:
        # Graceful fallback on LLM error or format error
        return heuristic_parse_request(message)
