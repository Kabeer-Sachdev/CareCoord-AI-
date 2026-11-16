"""
CareCoord MCP Agent.
Executes external healthcare interoperability tools exposed via Model Context Protocol (MCP) servers,
supporting single-server invocations as well as multi-server cross-system federated queries.
"""

from typing import Dict, Any, List, Optional
import time
import re
import logging

from backend.agents.state import CareCoordState
from backend.mcp.services.integration_service import integration_service

logger = logging.getLogger("CareCoord.MCPAgent")

class MCPAgent:
    def __init__(self):
        self.service = integration_service

    def process_node(self, state: CareCoordState) -> CareCoordState:
        """LangGraph node execution for MCP Agent."""
        state["current_agent"] = "MCP Agent"
        state["iteration_count"] = state.get("iteration_count", 0) + 1
        start_time = time.time()

        orig_query = state.get("original_request", "").strip()
        orig_lower = orig_query.lower()
        parsed = state.get("workflow_request", {})

        # Extract potential patient ID (e.g. P001) or Sample ID (e.g. SMP-1001)
        pat_match = re.search(r'\b(p\d{3,4})\b', orig_lower)
        patient_id = pat_match.group(1).upper() if pat_match else parsed.get("patient_id", "P001")

        smp_match = re.search(r'\b(smp-\d{4})\b', orig_lower)
        sample_id = smp_match.group(1).upper() if smp_match else "SMP-1001"

        # Extract lab code if present
        lab_code_match = re.search(r'\b(lab-[a-z0-9\-]+)\b', orig_lower)
        lab_code = lab_code_match.group(1).upper() if lab_code_match else "LAB-CBC"

        # Extract medication code or name
        med_code_match = re.search(r'\b(med-[a-z0-9\-]+)\b', orig_lower)
        med_code = med_code_match.group(1).upper() if med_code_match else None

        executed_tools = []
        combined_data: Dict[str, Any] = {}
        summary_lines = []

        # ------------------------------------------------------------------
        # Scenario A: Multi-Service Workflow (e.g. Patient Appointments + Lab Status)
        # ------------------------------------------------------------------
        is_multi_service = (
            ("appointment" in orig_lower or "record" in orig_lower) and
            ("lab" in orig_lower or "sample" in orig_lower or "test" in orig_lower)
        )

        if is_multi_service:
            # 1. Hospital MCP Call: get_patient_appointments
            hosp_resp = self.service.execute_tool_with_security(
                server_id="hospital-his",
                tool_name="get_patient_appointments",
                arguments={"patient_id": patient_id},
                workflow_id=state.get("workflow_id")
            )
            executed_tools.append("hospital-his.get_patient_appointments")
            combined_data["hospital_appointments"] = hosp_resp.result

            # 2. Laboratory MCP Call: get_sample_test_status
            lab_resp = self.service.execute_tool_with_security(
                server_id="laboratory-lis",
                tool_name="get_sample_test_status",
                arguments={"sample_id": sample_id},
                workflow_id=state.get("workflow_id")
            )
            executed_tools.append("laboratory-lis.get_sample_test_status")
            combined_data["laboratory_sample"] = lab_resp.result

            appts = hosp_resp.result.get("appointments", []) if hosp_resp.result else []
            lab_stage = lab_resp.result.get("processing_stage", "NOT_FOUND") if lab_resp.result else "UNKNOWN"
            summary_lines.append(
                f"Multi-Service Federated Query: Found {len(appts)} appointment(s) for patient {patient_id} via Hospital HIS, "
                f"and laboratory specimen {sample_id} status is '{lab_stage}' via Laboratory LIS."
            )

        # ------------------------------------------------------------------
        # Scenario B: Single-Server Laboratory Queries
        # ------------------------------------------------------------------
        elif any(k in orig_lower for k in ["lab", "sample", "specimen", "test availability", "blood count", "troponin"]):
            if "status" in orig_lower or "sample" in orig_lower or "specimen" in orig_lower:
                resp = self.service.execute_tool_with_security(
                    server_id="laboratory-lis",
                    tool_name="get_sample_test_status",
                    arguments={"sample_id": sample_id},
                    workflow_id=state.get("workflow_id")
                )
                executed_tools.append("laboratory-lis.get_sample_test_status")
                combined_data["lab_sample"] = resp.result
                status_label = resp.result.get("processing_stage") if resp.result else "NOT_FOUND"
                test_name = resp.result.get("test_name", "Test") if resp.result else "Diagnostic Test"
                summary_lines.append(f"Laboratory Sample {sample_id} ({test_name}) current status: {status_label}.")
            elif "catalog" in orig_lower or "list" in orig_lower:
                resp = self.service.execute_tool_with_security(
                    server_id="laboratory-lis",
                    tool_name="get_lab_service_catalog",
                    arguments={"category": None},
                    workflow_id=state.get("workflow_id")
                )
                executed_tools.append("laboratory-lis.get_lab_service_catalog")
                combined_data["lab_catalog"] = resp.result
                count = resp.result.get("total_catalog_items", 0) if resp.result else 0
                summary_lines.append(f"Laboratory catalog contains {count} active diagnostic service panels.")
            else:
                resp = self.service.execute_tool_with_security(
                    server_id="laboratory-lis",
                    tool_name="check_lab_service_availability",
                    arguments={"test_code": lab_code},
                    workflow_id=state.get("workflow_id")
                )
                executed_tools.append("laboratory-lis.check_lab_service_availability")
                combined_data["lab_availability"] = resp.result
                avail = resp.result.get("is_currently_available") if resp.result else False
                test_name = resp.result.get("name", lab_code) if resp.result else lab_code
                summary_lines.append(
                    f"Diagnostic test '{test_name}' ({lab_code}) is {'AVAILABLE' if avail else 'UNAVAILABLE'} "
                    f"with standard turnaround time of {resp.result.get('standard_turnaround_hours', 2)} hours."
                )

        # ------------------------------------------------------------------
        # Scenario C: Single-Server Pharmacy Queries
        # ------------------------------------------------------------------
        elif any(k in orig_lower for k in ["pharmacy", "medication", "drug", "stock", "amoxicillin", "paracetamol", "inhaler", "insulin"]):
            if "hours" in orig_lower or "operating" in orig_lower:
                resp = self.service.execute_tool_with_security(
                    server_id="pharmacy-rx",
                    tool_name="get_pharmacy_operating_hours",
                    arguments={},
                    workflow_id=state.get("workflow_id")
                )
                executed_tools.append("pharmacy-rx.get_pharmacy_operating_hours")
                combined_data["pharmacy_hours"] = resp.result
                central = resp.result.get("central_dispensary", {}).get("hours", "08:00 - 22:00") if resp.result else ""
                summary_lines.append(f"Hospital Pharmacy Operating Schedule: Outpatient dispensary is open {central}; inpatient satellite is open 24/7.")
            elif "catalog" in orig_lower:
                resp = self.service.execute_tool_with_security(
                    server_id="pharmacy-rx",
                    tool_name="get_pharmacy_catalog",
                    arguments={"category": None},
                    workflow_id=state.get("workflow_id")
                )
                executed_tools.append("pharmacy-rx.get_pharmacy_catalog")
                combined_data["pharmacy_catalog"] = resp.result
                count = resp.result.get("catalog_size", 0) if resp.result else 0
                summary_lines.append(f"Hospital pharmacy formulary catalog contains {count} registered medication formulations.")
            else:
                code_to_check = med_code or "MED-AMOX-500"
                if "paracetamol" in orig_lower:
                    code_to_check = "MED-PARA-650"
                elif "atorvastatin" in orig_lower:
                    code_to_check = "MED-ATOR-20"
                elif "metformin" in orig_lower:
                    code_to_check = "MED-METF-500"

                resp = self.service.execute_tool_with_security(
                    server_id="pharmacy-rx",
                    tool_name="check_product_availability",
                    arguments={"medication_code": code_to_check, "required_units": 10},
                    workflow_id=state.get("workflow_id")
                )
                executed_tools.append("pharmacy-rx.check_product_availability")
                combined_data["pharmacy_availability"] = resp.result
                units = resp.result.get("available_units", 0) if resp.result else 0
                name = resp.result.get("generic_name", code_to_check) if resp.result else code_to_check
                fulfill = resp.result.get("fulfillable", False) if resp.result else False
                summary_lines.append(f"Medication {name} ({code_to_check}): Stock on hand is {units} units (Request fulfillable: {fulfill}).")

        # ------------------------------------------------------------------
        # Scenario D: Fallback Hospital HIS Queries via MCP
        # ------------------------------------------------------------------
        else:
            resp = self.service.execute_tool_with_security(
                server_id="hospital-his",
                tool_name="get_patient_record",
                arguments={"patient_id": patient_id},
                workflow_id=state.get("workflow_id")
            )
            executed_tools.append("hospital-his.get_patient_record")
            combined_data["patient_record"] = resp.result
            p_name = resp.result.get("name", patient_id) if resp.result else patient_id
            summary_lines.append(f"Retrieved patient summary for {p_name} ({patient_id}) from Hospital Information System.")

        # Update State
        state["mcp_result"] = {
            "summary": " ".join(summary_lines),
            "executed_tools": executed_tools,
            "data": combined_data
        }

        if "executed_agents" not in state or state["executed_agents"] is None:
            state["executed_agents"] = []
        if "MCP Agent" not in state["executed_agents"]:
            state["executed_agents"].append("MCP Agent")

        elapsed_ms = int((time.time() - start_time) * 1000)
        log_entry = {
            "timestamp": time.strftime("%H:%M:%S"),
            "agent_name": "MCP Agent",
            "node_name": "mcp_agent",
            "event_type": "mcp_tool_execution",
            "status": "success",
            "execution_time_ms": elapsed_ms,
            "details": {
                "summary": " ".join(summary_lines),
                "tools_executed": executed_tools,
                "data": combined_data
            }
        }
        if "execution_log" not in state or state["execution_log"] is None:
            state["execution_log"] = []
        state["execution_log"].append(log_entry)

        return state
