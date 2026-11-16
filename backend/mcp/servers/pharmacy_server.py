"""
Pharmacy Service Sandbox MCP Server.
Exposes standardized administrative tools for formulary catalog queries, product inventory stock checks,
and dispensary operating hours. Strictly administrative; no autonomous prescription or dispensing capability.
"""

from typing import Optional, Dict, Any, List
from mcp.server.mcpserver import MCPServer

pharmacy_mcp_server = MCPServer(
    name="Hospital Pharmacy Service",
    version="1.0.0",
    instructions="Provides administrative formulary catalog lookups, product stock availability checks, and dispensary operating schedules."
)

PHARMACY_CATALOG = [
    {
        "medication_code": "MED-AMOX-500",
        "generic_name": "Amoxicillin",
        "brand_name": "Amoxil",
        "form": "Oral Capsule",
        "strength": "500mg",
        "category": "Anti-Infective / Antibiotic",
        "available_units": 420,
        "requires_prescription": True,
        "storage_condition": "Room Temperature (15-25°C)",
        "unit_price_inr": 12.50
    },
    {
        "medication_code": "MED-ATOR-20",
        "generic_name": "Atorvastatin Calcium",
        "brand_name": "Lipitor",
        "form": "Oral Tablet",
        "strength": "20mg",
        "category": "Cardiovascular / Statin",
        "available_units": 350,
        "requires_prescription": True,
        "storage_condition": "Room Temperature (20-25°C)",
        "unit_price_inr": 18.00
    },
    {
        "medication_code": "MED-METF-500",
        "generic_name": "Metformin Hydrochloride",
        "brand_name": "Glucophage",
        "form": "Oral Tablet",
        "strength": "500mg",
        "category": "Endocrine / Antidiabetic",
        "available_units": 800,
        "requires_prescription": True,
        "storage_condition": "Room Temperature (15-30°C)",
        "unit_price_inr": 4.50
    },
    {
        "medication_code": "MED-PARA-650",
        "generic_name": "Paracetamol",
        "brand_name": "Dolo",
        "form": "Oral Tablet",
        "strength": "650mg",
        "category": "Analgesic / Antipyretic",
        "available_units": 1500,
        "requires_prescription": False,
        "storage_condition": "Room Temperature",
        "unit_price_inr": 2.20
    },
    {
        "medication_code": "MED-PANT-40",
        "generic_name": "Pantoprazole Sodium",
        "brand_name": "Pantocid",
        "form": "Delayed-Release Tablet",
        "strength": "40mg",
        "category": "Gastrointestinal / PPI",
        "available_units": 620,
        "requires_prescription": True,
        "storage_condition": "Room Temperature",
        "unit_price_inr": 9.80
    },
    {
        "medication_code": "MED-SALB-100",
        "generic_name": "Salbutamol Sulfate",
        "brand_name": "Ventolin Inhaler",
        "form": "Metered Dose Inhaler",
        "strength": "100mcg/actuation",
        "category": "Respiratory / Bronchodilator",
        "available_units": 95,
        "requires_prescription": True,
        "storage_condition": "Store below 30°C, Protect from Frost",
        "unit_price_inr": 165.00
    },
    {
        "medication_code": "MED-INS-GLAR",
        "generic_name": "Insulin Glargine",
        "brand_name": "Lantus SoloStar",
        "form": "Subcutaneous Injection Pen",
        "strength": "100 units/mL (3mL)",
        "category": "Endocrine / Long-Acting Insulin",
        "available_units": 45,
        "requires_prescription": True,
        "storage_condition": "Refrigerate (2-8°C), Do Not Freeze",
        "unit_price_inr": 680.00
    }
]


@pharmacy_mcp_server.tool(
    name="get_pharmacy_catalog",
    description="Retrieve hospital formulary product list, optionally filtered by therapeutic category (e.g., Cardiovascular, Antibiotic, Respiratory)."
)
def get_pharmacy_catalog(category: Optional[str] = None) -> Dict[str, Any]:
    items = PHARMACY_CATALOG
    if category and category.strip() and category.lower() != "all":
        cat_lower = category.strip().lower()
        items = [i for i in items if cat_lower in i["category"].lower() or cat_lower in i["generic_name"].lower()]
    
    return {
        "filter_category": category or "All Formulary",
        "catalog_size": len(items),
        "products": items,
        "dispensary": "CareCoord Central Hospital Pharmacy"
    }


@pharmacy_mcp_server.tool(
    name="check_product_availability",
    description="Verify current physical stock on hand for a specific formulary medication code (e.g., MED-AMOX-500) and check if required quantity can be fulfilled."
)
def check_product_availability(medication_code: str, required_units: int = 1) -> Dict[str, Any]:
    code_upper = medication_code.strip().upper()
    product = next((p for p in PHARMACY_CATALOG if p["medication_code"] == code_upper), None)
    
    if not product:
        return {
            "medication_code": medication_code,
            "is_stocked": False,
            "fulfillable": False,
            "available_units": 0,
            "message": f"Medication code '{medication_code}' is not catalogued in the active hospital formulary."
        }
    
    is_fulfillable = product["available_units"] >= required_units
    return {
        "medication_code": product["medication_code"],
        "generic_name": product["generic_name"],
        "strength": product["strength"],
        "form": product["form"],
        "is_stocked": True,
        "available_units": product["available_units"],
        "requested_units": required_units,
        "fulfillable": is_fulfillable,
        "requires_prescription": product["requires_prescription"],
        "storage_condition": product["storage_condition"],
        "status": "IN_STOCK" if product["available_units"] > 20 else "LOW_STOCK"
    }


@pharmacy_mcp_server.tool(
    name="get_pharmacy_operating_hours",
    description="Retrieve dispensary operating schedules, satellite pharmacy locations, and on-call emergency pharmacist coverage."
)
def get_pharmacy_operating_hours() -> Dict[str, Any]:
    return {
        "central_dispensary": {
            "location": "Ground Floor, Main Outpatient Atrium",
            "hours": "08:00 to 22:00 Daily",
            "services": ["Outpatient Prescription Dispensing", "Over-the-Counter Consultation", "Home Delivery Coordination"],
            "phone_extension": "4020"
        },
        "inpatient_satellite": {
            "location": "3rd Floor, Between ICU & Surgical Suites",
            "hours": "24/7 Continuous Service",
            "services": ["STAT Inpatient Medication Distribution", "IV Admixtures", "Narcotic Controlled Storage"],
            "phone_extension": "4025"
        },
        "chief_pharmacist": "Dr. S. K. Raman, M.Pharm",
        "emergency_code_delivery": "Immediate via pneumatic tube system or dedicated runner"
    }
