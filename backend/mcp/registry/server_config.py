"""
MCP Server Configuration and Security Allowlists.
Defines registered MCP server instances, supported transports, tool security boundaries, and RBAC mappings.
"""

from typing import Dict, Any, List

DEFAULT_MCP_SERVERS: Dict[str, Dict[str, Any]] = {
    "hospital-his": {
        "server_id": "hospital-his",
        "name": "Hospital Information System (HIS)",
        "description": "Standardized electronic hospital administrative queries for patients, doctors, schedules, and beds.",
        "transport_type": "in-memory",
        "endpoint": "local://hospital_his_server",
        "is_enabled": True
    },
    "laboratory-lis": {
        "server_id": "laboratory-lis",
        "name": "Laboratory Information System (LIS)",
        "description": "Diagnostic pathology service catalog, reagent uptime, and specimen accession tracking.",
        "transport_type": "in-memory",
        "endpoint": "local://laboratory_lis_server",
        "is_enabled": True
    },
    "pharmacy-rx": {
        "server_id": "pharmacy-rx",
        "name": "Hospital Pharmacy Service",
        "description": "Formulary medication lookup, inventory stock verification, and dispensary operating schedules.",
        "transport_type": "in-memory",
        "endpoint": "local://pharmacy_rx_server",
        "is_enabled": True
    }
}

ALLOWED_MCP_TOOLS: Dict[str, List[str]] = {
    "hospital-his": [
        "get_patient_record",
        "get_patient_appointments",
        "get_available_doctors",
        "get_doctor_schedule",
        "get_available_beds",
        "get_department_information"
    ],
    "laboratory-lis": [
        "get_lab_service_catalog",
        "check_lab_service_availability",
        "get_sample_test_status",
        "get_lab_department_information"
    ],
    "pharmacy-rx": [
        "get_pharmacy_catalog",
        "check_product_availability",
        "get_pharmacy_operating_hours"
    ]
}

TOOL_ROLE_PERMISSIONS: Dict[str, str] = {
    # Hospital HIS tools
    "get_patient_record": "PATIENT",
    "get_patient_appointments": "PATIENT",
    "get_available_doctors": "PATIENT",
    "get_doctor_schedule": "NURSE",
    "get_available_beds": "NURSE",
    "get_department_information": "PATIENT",

    # Lab LIS tools
    "get_lab_service_catalog": "PATIENT",
    "check_lab_service_availability": "PATIENT",
    "get_sample_test_status": "PATIENT",
    "get_lab_department_information": "PATIENT",

    # Pharmacy tools
    "get_pharmacy_catalog": "PATIENT",
    "check_product_availability": "PATIENT",
    "get_pharmacy_operating_hours": "PATIENT"
}
