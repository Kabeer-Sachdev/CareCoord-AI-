from typing import Dict, Any, List
import time
from backend.agents.state import CareCoordState

class CoordinatorAgent:
    """
    Coordinator Agent for CareCoord LangGraph Orchestration.
    Responsible for operational decision-making, handoffs between specialized agents,
    missing parameter detection, conflict resolution, and final recommendation compilation.
    """

    def process(self, state: CareCoordState) -> CareCoordState:
        state["current_agent"] = "Coordinator Agent"
        state["iteration_count"] = state.get("iteration_count", 0) + 1
        start_time = time.time()

        parsed = state.get("workflow_request", {})
        request_type = parsed.get("request_type", "unknown")
        clarification_needed = parsed.get("clarification_needed", False)

        # 1. Missing Information Detection
        if clarification_needed or request_type == "unknown":
            state["status"] = "NEEDS_CLARIFICATION"
            prompt = parsed.get("clarification_prompt") or "Please provide more details regarding your request."
            steps_list = [e.get("details", {}).get("summary", e.get("event_type", "step")) for e in state.get("execution_log", [])]
            steps_list.append("Requested clarification for missing operational parameters")
            state["final_recommendation"] = {
                "agent_used": "Coordinator Agent",
                "status": "clarification_required",
                "recommendation": prompt,
                "data": {"missing_info": parsed.get("missing_info", [])},
                "steps": steps_list
            }
            self._log_event(state, "coordinator", "clarification_required", "success", "Missing required operational parameters", start_time)
            return state

        # 2. Determine Required Agents if not already populated
        if not state.get("required_agents"):
            if request_type == "appointment":
                state["required_agents"] = ["Doctor Agent", "Appointment Agent"]
            elif request_type == "doctor_search":
                state["required_agents"] = ["Doctor Agent"]
            elif request_type == "patient_information":
                state["required_agents"] = ["Patient Agent"]
            else:
                state["required_agents"] = []

        executed = state.get("executed_agents", [])
        required = state.get("required_agents", [])

        self._log_event(
            state,
            "coordinator",
            "plan_workflow",
            "success",
            f"Request Type: {request_type} | Required Agents: {', '.join(required)}",
            start_time
        )

        # 3. Check if all required agents have executed
        all_executed = all(agent in executed for agent in required)

        if not all_executed:
            # Routing decision happens via graph conditional edge
            return state

        steps_summary = [e.get("details", {}).get("summary", e.get("event_type", "step")) for e in state.get("execution_log", [])]

        # 4. Synthesize Final Recommendations from Tool Results
        if request_type == "doctor_search":
            doc_res = state.get("doctor_result") or {}
            doctors = doc_res.get("data", {}).get("doctors", [])
            spec = parsed.get("specialization") or parsed.get("department") or "all departments"

            if not doctors:
                rec_text = f"No available {spec} doctors were found in the hospital database for the requested criteria. Alternative options may be explored by hospital staff."
            else:
                doc_list_str = ", ".join([f"{d['name']} ({d['doctor_id']})" for d in doctors])
                rec_text = f"Found {len(doctors)} available doctor(s) in {spec}: {doc_list_str}."

            state["final_recommendation"] = {
                "agent_used": "Doctor Agent",
                "status": "success",
                "recommendation": rec_text,
                "data": doc_res.get("data"),
                "steps": steps_summary
            }
            state["status"] = "COMPLETED"

        elif request_type == "patient_information":
            pat_res = state.get("patient_result") or {}
            patient = pat_res.get("data", {}).get("patient")
            appts = pat_res.get("data", {}).get("appointments", [])
            pid = parsed.get("patient_id", "P001")

            if not patient:
                rec_text = f"Patient record for ID {pid} was not found in the database."
            else:
                rec_text = f"Retrieved record and {len(appts)} appointment(s) for patient {patient['name']} ({patient['patient_id']})."

            state["final_recommendation"] = {
                "agent_used": "Patient Agent",
                "status": "success",
                "recommendation": rec_text,
                "data": pat_res.get("data"),
                "steps": steps_summary
            }
            state["status"] = "COMPLETED"

        elif request_type == "appointment":
            # Appointment workflow requires validation and human approval
            doc_res = state.get("doctor_result") or {}
            appt_res = state.get("appointment_result") or {}

            doctors = doc_res.get("data", {}).get("doctors", [])
            slot_check = appt_res.get("data", {}).get("slot_check", {})
            available_slots = appt_res.get("data", {}).get("available_slots", [])

            if not doctors:
                spec = parsed.get("specialization") or parsed.get("department") or "requested department"
                state["final_recommendation"] = {
                    "agent_used": "Appointment Agent",
                    "status": "no_availability",
                    "recommendation": f"No available {spec} doctor was found for the requested period. Alternative options may be explored by hospital staff.",
                    "data": {"available_doctors": [], "available_slots": []},
                    "steps": steps_summary
                }
                state["status"] = "COMPLETED"
            elif slot_check.get("available") is False:
                reason = slot_check.get("reason", "Requested slot is unavailable.")
                alt_str = ", ".join(available_slots) if available_slots else "None"
                state["final_recommendation"] = {
                    "agent_used": "Appointment Agent",
                    "status": "conflict_detected",
                    "recommendation": f"Requested appointment slot unavailable. Reason: {reason}. Alternative available slots: {alt_str}.",
                    "data": {"slot_check": slot_check, "alternative_slots": available_slots},
                    "steps": steps_summary
                }
                state["status"] = "COMPLETED"

        return state

    def _log_event(self, state: CareCoordState, node: str, event: str, status: str, summary: str, start_time: float):
        elapsed_ms = int((time.time() - start_time) * 1000)
        log_entry = {
            "timestamp": time.strftime("%H:%M:%S"),
            "agent_name": "Coordinator Agent",
            "node_name": node,
            "event_type": event,
            "status": status,
            "execution_time_ms": elapsed_ms,
            "details": {"summary": summary}
        }
        state["execution_log"].append(log_entry)
