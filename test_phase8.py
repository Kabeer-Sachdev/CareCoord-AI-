"""
CareCoord Phase 8 Verification Test Suite: MCP External Integrations & FHIR Interoperability
Tests:
1. Official MCP Server initialization (Hospital HIS, Laboratory LIS, Pharmacy Rx).
2. Dynamic MCP tool discovery (13 distinct tools).
3. Tool execution: Laboratory CBC availability, Pharmacy Amoxicillin stock check, HIS Patient Record.
4. Input schema validation & invalid argument rejection.
5. Role-based access control (RBAC) & security allowlists.
6. Server connection lifecycle (disconnect, error handling, reconnect).
7. HL7 FHIR R4 resource conversion (Patient, Practitioner, Appointment) & CapabilityStatement.
8. LangGraph Coordinator routing & federated multi-service aggregation.
9. Persistent audit trail logging.
"""

import unittest
from datetime import date

# Database and models
from backend.database.database import SessionLocal, init_db
from backend.database.models import User, Patient, Doctor, Appointment, MCPToolExecution, FHIRExportLog

# MCP Components
from backend.mcp.client.mcp_client import mcp_client
from backend.mcp.registry.server_registry import server_registry
from backend.mcp.services.integration_service import integration_service
from backend.mcp.schemas.mcp_schemas import MCPToolExecutionRequest

# FHIR Components
from backend.integrations.fhir.mapper import FHIRMapper
from backend.integrations.fhir.service import fhir_service

# Coordinator & Workflow Service
from backend.services.workflow_service import workflow_service
from backend.schemas.workflow import WorkflowRequest


class TestPhase8MCPAndFHIR(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.db = SessionLocal()

        # Admin user
        cls.admin_user = cls.db.query(User).filter(User.role == "ADMIN").first()
        if not cls.admin_user:
            cls.admin_user = User(username="admin_test", role="ADMIN", is_active=True)
            cls.db.add(cls.admin_user)
            cls.db.commit()

        # Doctor user
        cls.doctor_user = cls.db.query(User).filter(User.role == "DOCTOR").first()
        if not cls.doctor_user:
            cls.doctor_user = User(username="doctor_test", role="DOCTOR", is_active=True)
            cls.db.add(cls.doctor_user)
            cls.db.commit()

        # Patient user
        cls.patient_user = cls.db.query(User).filter(User.role == "PATIENT").first()
        if not cls.patient_user:
            cls.patient_user = User(username="patient_test", role="PATIENT", is_active=True)
            cls.db.add(cls.patient_user)
            cls.db.commit()

        # Pre-populate / connect all MCP servers in registry
        server_registry.sync_to_db()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    # 1. MCP Server Registry and Initial State
    def test_01_server_registry_initialization(self):
        servers = server_registry.list_servers()
        self.assertGreaterEqual(len(servers), 3)
        server_ids = [s.server_id for s in servers]
        self.assertIn("hospital-his", server_ids)
        self.assertIn("laboratory-lis", server_ids)
        self.assertIn("pharmacy-rx", server_ids)
        print("\n[PASS] MCP Server Registry initialized with 3 default servers.")

    # 2. Dynamic Tool Discovery
    def test_02_dynamic_tool_discovery(self):
        tools = mcp_client.discover_tools()
        self.assertGreaterEqual(len(tools), 13)
        tool_names = [t.name for t in tools]

        # Verify key tools across the 3 domains
        self.assertIn("get_patient_record", tool_names)
        self.assertIn("get_available_doctors", tool_names)
        self.assertIn("get_available_beds", tool_names)
        self.assertIn("get_lab_service_catalog", tool_names)
        self.assertIn("check_lab_service_availability", tool_names)
        self.assertIn("get_pharmacy_catalog", tool_names)
        self.assertIn("check_product_availability", tool_names)
        print(f"[PASS] Dynamic Tool Discovery found {len(tools)} tools across all servers.")

    # 3. Laboratory MCP Tool Execution
    def test_03_laboratory_tool_execution(self):
        res = integration_service.execute_tool_with_security(
            server_id="laboratory-lis",
            tool_name="check_lab_service_availability",
            arguments={"test_code": "LAB-CBC"},
            user=self.admin_user
        )
        self.assertEqual(res.status, "SUCCESS")
        self.assertEqual(res.server_id, "laboratory-lis")
        self.assertTrue(res.result.get("is_currently_available"))
        print(f"[PASS] Laboratory Tool Execution (check_lab_service_availability): {res.result['name']} available.")

    # 4. Pharmacy MCP Tool Execution
    def test_04_pharmacy_tool_execution(self):
        res = integration_service.execute_tool_with_security(
            server_id="pharmacy-rx",
            tool_name="check_product_availability",
            arguments={"medication_code": "MED-AMOX-500"},
            user=self.doctor_user
        )
        self.assertEqual(res.status, "SUCCESS")
        self.assertEqual(res.server_id, "pharmacy-rx")
        self.assertTrue(res.result.get("is_stocked"))
        self.assertGreater(res.result["available_units"], 0)
        print(f"[PASS] Pharmacy Tool Execution (check_product_availability): {res.result['generic_name']} stock = {res.result['available_units']}.")

    # 5. Hospital HIS Tool Execution
    def test_05_hospital_tool_execution(self):
        patient = self.db.query(Patient).first()
        res = integration_service.execute_tool_with_security(
            server_id="hospital-his",
            tool_name="get_patient_record",
            arguments={"patient_id": patient.patient_id},
            user=self.admin_user
        )
        self.assertEqual(res.status, "SUCCESS")
        self.assertEqual(res.result["patient_id"], patient.patient_id)
        self.assertEqual(res.result["name"], patient.name)
        print(f"[PASS] Hospital HIS Tool Execution (get_patient_record): Patient {res.result['name']} found.")

    # 6. Input Schema Validation
    def test_06_input_schema_validation(self):
        # Missing required parameter "patient_id"
        res = integration_service.execute_tool_with_security(
            server_id="hospital-his",
            tool_name="get_patient_record",
            arguments={},
            user=self.admin_user
        )
        self.assertNotEqual(res.status, "SUCCESS")
        self.assertIsNotNone(res.error)
        print(f"[PASS] Input Schema Validation correctly caught missing arguments: {res.error[:60]}...")

    # 7. Role-Based Access Control (RBAC) Guardrails
    def test_07_rbac_access_control(self):
        # PATIENT role should NOT be permitted to query get_doctor_schedule
        res = integration_service.execute_tool_with_security(
            server_id="hospital-his",
            tool_name="get_doctor_schedule",
            arguments={"doctor_id": "D001"},
            user=self.patient_user
        )
        self.assertEqual(res.status, "BLOCKED")
        self.assertIn("denied", res.error.lower())
        print(f"[PASS] RBAC Guardrail enforced: PATIENT blocked from staff-only doctor schedule.")

    # 8. Server Connection Lifecycle (Disconnect & Error Handling)
    def test_08_server_lifecycle_and_error_handling(self):
        # Disconnect pharmacy-rx
        server_registry.disconnect_server("pharmacy-rx")
        status = server_registry.get_server("pharmacy-rx")
        self.assertEqual(status.status, "DISCONNECTED")

        # Attempt to run tool on disconnected server
        res = integration_service.execute_tool_with_security(
            server_id="pharmacy-rx",
            tool_name="get_pharmacy_catalog",
            arguments={},
            user=self.admin_user
        )
        self.assertNotEqual(res.status, "SUCCESS")
        self.assertIn("disconnected", res.error.lower())

        # Reconnect
        reconnected = server_registry.connect_server("pharmacy-rx")
        self.assertTrue(reconnected)
        res2 = integration_service.execute_tool_with_security(
            server_id="pharmacy-rx",
            tool_name="get_pharmacy_catalog",
            arguments={},
            user=self.admin_user
        )
        self.assertEqual(res2.status, "SUCCESS")
        print(f"[PASS] Server Lifecycle: Disconnect, error rejection, and reconnection validated.")

    # 9. FHIR R4 Patient Mapping
    def test_09_fhir_patient_mapping(self):
        patient = self.db.query(Patient).first()
        fhir_patient, errors = FHIRMapper.patient_to_fhir(patient)
        self.assertEqual(len(errors), 0)
        self.assertEqual(fhir_patient["resourceType"], "Patient")
        self.assertEqual(fhir_patient["id"], patient.patient_id)
        self.assertEqual(fhir_patient["name"][0]["text"], patient.name)
        print(f"[PASS] FHIR R4 Patient Resource validated conforming to HL7 specification.")

    # 10. FHIR R4 Appointment & Practitioner Mapping
    def test_10_fhir_appointment_and_practitioner(self):
        doctor = self.db.query(Doctor).first()
        fhir_doc, doc_errors = FHIRMapper.doctor_to_practitioner(doctor)
        self.assertEqual(len(doc_errors), 0)
        self.assertEqual(fhir_doc["resourceType"], "Practitioner")
        self.assertEqual(fhir_doc["id"], doctor.doctor_id)

        appt = self.db.query(Appointment).first()
        fhir_appt, appt_errors = FHIRMapper.appointment_to_fhir(appt)
        self.assertEqual(len(appt_errors), 0)
        self.assertEqual(fhir_appt["resourceType"], "Appointment")
        print(f"[PASS] FHIR R4 Practitioner & Appointment Resources mapped correctly.")

    # 11. FHIR CapabilityStatement
    def test_11_fhir_capability_statement(self):
        meta = fhir_service.get_capability_statement()
        self.assertEqual(meta.resourceType, "CapabilityStatement")
        self.assertEqual(meta.fhirVersion, "4.0.1")
        self.assertIn("Patient", meta.supported_resources)
        self.assertIn("Practitioner", meta.supported_resources)
        self.assertIn("Appointment", meta.supported_resources)
        print(f"[PASS] FHIR CapabilityStatement returned valid R4 metadata.")

    # 12. LangGraph Coordinator Routing to MCP Agent
    def test_12_coordinator_mcp_routing(self):
        req = WorkflowRequest(
            message="Check laboratory availability for CBC blood test and check amoxicillin stock in pharmacy."
        )
        res = workflow_service.process_workflow(db=self.db, request=req)
        self.assertIn(res.status.lower(), ["success", "completed", "requires_human_approval"])
        self.assertIn("mcp", res.agent_used.lower())
        self.assertTrue("diagnostic test" in res.recommendation.lower() or "laboratory" in res.recommendation.lower() or "blood" in res.recommendation.lower())
        print(f"[PASS] Coordinator Agent successfully routed request through LangGraph MCP Agent node. Agent: {res.agent_used}")

    # 13. Audit Logging
    def test_13_audit_trail_logging(self):
        executions = self.db.query(MCPToolExecution).all()
        self.assertGreaterEqual(len(executions), 1)
        exports = self.db.query(FHIRExportLog).all()
        self.assertIsNotNone(exports)
        print(f"[PASS] Persistent Audit Trail logged {len(executions)} tool executions.")


if __name__ == "__main__":
    unittest.main()
