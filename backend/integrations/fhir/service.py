"""
FHIR Interoperability Service.
Handles FHIR capability statements, resource mapping, schema validation, and export audit trails.
"""

from datetime import datetime
import uuid
from typing import Dict, Any, List, Optional
import logging

from backend.mcp.schemas.mcp_schemas import (
    FHIRMetadataResponse,
    FHIRExportResponse
)
from backend.integrations.fhir.mapper import FHIRMapper

logger = logging.getLogger("CareCoord.FHIRService")

class FHIRService:
    def get_capability_statement(self) -> FHIRMetadataResponse:
        """Returns the HL7 FHIR Release 4 (R4) CapabilityStatement for CareCoord."""
        return FHIRMetadataResponse(
            resourceType="CapabilityStatement",
            id="carecoord-fhir-capability-v1",
            status="active",
            date=datetime.utcnow().strftime("%Y-%m-%d"),
            publisher="CareCoord Hospital Interoperability Hub",
            kind="capability",
            fhirVersion="4.0.1",
            format=["json"],
            supported_resources=["Patient", "Practitioner", "Appointment"],
            mapping_assumptions={
                "Patient": "MRN maps to identifier.system 'urn:carecoord:mrn'; age calculates approximate birthDate.",
                "Practitioner": "Staff ID maps to 'urn:carecoord:practitioner'; specialization maps to qualification.",
                "Appointment": "CareCoord status ('scheduled', 'completed', 'cancelled') maps to FHIR R4 ('booked', 'fulfilled', 'cancelled')."
            }
        )

    def export_patient(
        self,
        patient_id: str,
        validate_only: bool = False,
        user_id: Optional[str] = None
    ) -> FHIRExportResponse:
        """Exports a CareCoord Patient to a validated HL7 FHIR R4 Patient resource."""
        from backend.database.database import SessionLocal
        from backend.database.models import Patient, FHIRExportLog

        db = SessionLocal()
        export_id = f"FHIR-EXP-{uuid.uuid4().hex[:8].upper()}"
        try:
            p = db.query(Patient).filter(Patient.patient_id == patient_id.strip()).first()
            if not p:
                return FHIRExportResponse(
                    export_id=export_id,
                    resource_type="Patient",
                    entity_id=patient_id,
                    status="FAILED",
                    fhir_resource=None,
                    validation_errors=[f"Patient '{patient_id}' not found in CareCoord database."]
                )

            fhir_json, errors = FHIRMapper.patient_to_fhir(p)
            status = "VALIDATION_ERROR" if errors else "SUCCESS"

            if not validate_only:
                log_rec = FHIRExportLog(
                    export_id=export_id,
                    resource_type="Patient",
                    entity_id=patient_id,
                    user_id=user_id,
                    status=status,
                    resource_payload=fhir_json
                )
                db.add(log_rec)
                db.commit()

            return FHIRExportResponse(
                export_id=export_id,
                resource_type="Patient",
                entity_id=patient_id,
                status=status,
                fhir_resource=fhir_json,
                validation_errors=errors
            )
        finally:
            db.close()

    def export_appointment(
        self,
        appointment_id: str,
        validate_only: bool = False,
        user_id: Optional[str] = None
    ) -> FHIRExportResponse:
        """Exports a CareCoord Appointment to a validated HL7 FHIR R4 Appointment resource."""
        from backend.database.database import SessionLocal
        from backend.database.models import Appointment, FHIRExportLog

        db = SessionLocal()
        export_id = f"FHIR-EXP-{uuid.uuid4().hex[:8].upper()}"
        try:
            a = db.query(Appointment).filter(Appointment.appointment_id == appointment_id.strip()).first()
            if not a:
                return FHIRExportResponse(
                    export_id=export_id,
                    resource_type="Appointment",
                    entity_id=appointment_id,
                    status="FAILED",
                    fhir_resource=None,
                    validation_errors=[f"Appointment '{appointment_id}' not found in CareCoord database."]
                )

            fhir_json, errors = FHIRMapper.appointment_to_fhir(a)
            status = "VALIDATION_ERROR" if errors else "SUCCESS"

            if not validate_only:
                log_rec = FHIRExportLog(
                    export_id=export_id,
                    resource_type="Appointment",
                    entity_id=appointment_id,
                    user_id=user_id,
                    status=status,
                    resource_payload=fhir_json
                )
                db.add(log_rec)
                db.commit()

            return FHIRExportResponse(
                export_id=export_id,
                resource_type="Appointment",
                entity_id=appointment_id,
                status=status,
                fhir_resource=fhir_json,
                validation_errors=errors
            )
        finally:
            db.close()

    def get_export_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves history of FHIR exports from database."""
        from backend.database.database import SessionLocal
        from backend.database.models import FHIRExportLog

        db = SessionLocal()
        try:
            records = db.query(FHIRExportLog).order_by(FHIRExportLog.created_at.desc()).limit(limit).all()
            return [
                {
                    "export_id": r.export_id,
                    "resource_type": r.resource_type,
                    "entity_id": r.entity_id,
                    "user_id": r.user_id,
                    "status": r.status,
                    "created_at": r.created_at.isoformat()
                }
                for r in records
            ]
        finally:
            db.close()

fhir_service = FHIRService()
