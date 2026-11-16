"""
Laboratory Information System (LIS) Sandbox MCP Server.
Demonstrates standardized tool integration for laboratory service catalogs, diagnostic test availability,
and specimen processing lifecycle tracking. Strictly operational; no clinical interpretation or diagnosis.
"""

from typing import Optional, Dict, Any, List
from mcp.server.mcpserver import MCPServer

laboratory_mcp_server = MCPServer(
    name="Laboratory Information System (LIS)",
    version="1.0.0",
    instructions="Provides administrative laboratory catalog queries, reagent availability checks, and specimen tracking status."
)

LAB_CATALOG = [
    {
        "test_code": "LAB-CBC",
        "name": "Complete Blood Count with Differential",
        "category": "Hematology",
        "sample_type": "Whole Blood (EDTA Lavendar)",
        "turnaround_hours": 2,
        "fasting_required": False,
        "available": True,
        "stat_eligible": True
    },
    {
        "test_code": "LAB-BMP",
        "name": "Basic Metabolic Panel (Electrolytes, Glucose, BUN, Creatinine)",
        "category": "Biochemistry",
        "sample_type": "Serum (SST Gold)",
        "turnaround_hours": 3,
        "fasting_required": True,
        "available": True,
        "stat_eligible": True
    },
    {
        "test_code": "LAB-LIP",
        "name": "Lipid Panel (Total Cholesterol, HDL, LDL, Triglycerides)",
        "category": "Biochemistry",
        "sample_type": "Serum (SST Gold)",
        "turnaround_hours": 4,
        "fasting_required": True,
        "available": True,
        "stat_eligible": False
    },
    {
        "test_code": "LAB-TROP",
        "name": "High-Sensitivity Cardiac Troponin I",
        "category": "Cardiology Markers",
        "sample_type": "Plasma (Heparin Green)",
        "turnaround_hours": 1,
        "fasting_required": False,
        "available": True,
        "stat_eligible": True
    },
    {
        "test_code": "LAB-CRP",
        "name": "C-Reactive Protein (Quantitative Inflammatory Marker)",
        "category": "Immunology",
        "sample_type": "Serum (SST Gold)",
        "turnaround_hours": 3,
        "fasting_required": False,
        "available": True,
        "stat_eligible": False
    },
    {
        "test_code": "LAB-RVP",
        "name": "Respiratory Viral Panel Multiplex RT-PCR",
        "category": "Molecular Microbiology",
        "sample_type": "Nasopharyngeal Swab",
        "turnaround_hours": 6,
        "fasting_required": False,
        "available": True,
        "stat_eligible": True
    },
    {
        "test_code": "LAB-URIN",
        "name": "Complete Urinalysis with Microscopic Examination",
        "category": "Clinical Pathology",
        "sample_type": "Clean Catch Urine",
        "turnaround_hours": 2,
        "fasting_required": False,
        "available": True,
        "stat_eligible": True
    }
]

MOCK_SPECIMEN_DB = {
    "SMP-1001": {
        "sample_id": "SMP-1001",
        "patient_id": "P001",
        "test_code": "LAB-BMP",
        "test_name": "Basic Metabolic Panel",
        "collection_time": "2026-11-16 08:30:00",
        "processing_stage": "ANALYZED",
        "verification_status": "PENDING_PATHOLOGIST_SIGN_OFF",
        "estimated_completion": "2026-11-16 11:30:00"
    },
    "SMP-1002": {
        "sample_id": "SMP-1002",
        "patient_id": "P007",
        "test_code": "LAB-TROP",
        "test_name": "High-Sensitivity Cardiac Troponin I",
        "collection_time": "2026-11-16 10:15:00",
        "processing_stage": "IN_PROCESS",
        "verification_status": "RUNNING_ON_ANALYZER_STAT",
        "estimated_completion": "2026-11-16 11:15:00"
    },
    "SMP-1003": {
        "sample_id": "SMP-1003",
        "patient_id": "P003",
        "test_code": "LAB-CBC",
        "test_name": "Complete Blood Count",
        "collection_time": "2026-11-15 14:00:00",
        "processing_stage": "VERIFIED",
        "verification_status": "RESULTS_DELIVERED_TO_EHR",
        "estimated_completion": "2026-11-15 16:00:00"
    }
}


@laboratory_mcp_server.tool(
    name="get_lab_service_catalog",
    description="Retrieve the catalog of diagnostic laboratory services, optionally filtered by discipline/category (e.g., Hematology, Biochemistry, Immunology)."
)
def get_lab_service_catalog(category: Optional[str] = None) -> Dict[str, Any]:
    tests = LAB_CATALOG
    if category and category.strip() and category.lower() != "all":
        cat_lower = category.strip().lower()
        tests = [t for t in tests if cat_lower in t["category"].lower()]
    
    return {
        "filter_category": category or "All Categories",
        "total_catalog_items": len(tests),
        "catalog": tests,
        "laboratory_network": "CareCoord Central Diagnostic Services"
    }


@laboratory_mcp_server.tool(
    name="check_lab_service_availability",
    description="Check whether a specific diagnostic laboratory test is actively offered, reagent levels are stocked, and analyzer uptime is nominal."
)
def check_lab_service_availability(test_code: str) -> Dict[str, Any]:
    code_upper = test_code.strip().upper()
    matched = next((t for t in LAB_CATALOG if t["test_code"] == code_upper), None)
    
    if not matched:
        return {
            "test_code": test_code,
            "is_offered": False,
            "message": f"Diagnostic test code '{test_code}' is not recognized in the laboratory formulary."
        }
    
    return {
        "test_code": matched["test_code"],
        "name": matched["name"],
        "category": matched["category"],
        "is_offered": True,
        "is_currently_available": matched["available"],
        "reagent_stock_status": "NORMAL_ADEQUATE",
        "analyzer_status": "ONLINE_CALIBRATED",
        "stat_capability": matched["stat_eligible"],
        "standard_turnaround_hours": matched["turnaround_hours"],
        "fasting_required": matched["fasting_required"]
    }


@laboratory_mcp_server.tool(
    name="get_sample_test_status",
    description="Track the administrative specimen processing lifecycle status for a laboratory sample accession ID (e.g., SMP-1001)."
)
def get_sample_test_status(sample_id: str) -> Dict[str, Any]:
    s_upper = sample_id.strip().upper()
    sample = MOCK_SPECIMEN_DB.get(s_upper)
    
    if not sample:
        # Graceful synthetic lookup for demonstration sample IDs
        return {
            "sample_id": sample_id,
            "found": False,
            "processing_stage": "NOT_RECEIVED",
            "message": f"No active laboratory accession record found for sample ID '{sample_id}'."
        }
    
    return {
        "found": True,
        "sample_id": sample["sample_id"],
        "patient_id": sample["patient_id"],
        "test_code": sample["test_code"],
        "test_name": sample["test_name"],
        "collection_time": sample["collection_time"],
        "processing_stage": sample["processing_stage"],
        "verification_status": sample["verification_status"],
        "estimated_completion": sample["estimated_completion"],
        "clinical_note": "Status indicates laboratory workflow milestone only; see EHR for clinical findings."
    }


@laboratory_mcp_server.tool(
    name="get_lab_department_information",
    description="Retrieve laboratory operating hours, accreditation details, sample drop-off stations, and emergency STAT contacts."
)
def get_lab_department_information() -> Dict[str, Any]:
    return {
        "facility_name": "CareCoord Central Clinical Diagnostic Pathology Laboratory",
        "accreditation": "CAP / NABL Simulated Quality Benchmark Tier-1",
        "operating_hours": "24/7 Continuous Automated STAT and Routine Processing",
        "drop_off_stations": [
            "Central Phlebotomy Suite (Ground Floor, Room 104)",
            "ED Rapid STAT Dropbox (Emergency Department Triage)",
            "ICU Pneumatic Tube Station #3"
        ],
        "stat_hotline": "+91-11-2659-4080",
        "laboratory_director": "Dr. A. Sen, MD (Pathology)"
    }
