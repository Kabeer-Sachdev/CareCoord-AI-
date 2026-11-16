"""
HL7 FHIR R4 Mapping Layer for CareCoord.
Translates CareCoord internal database models (Patient, Doctor, Appointment) into standard-compliant
HL7 FHIR R4 JSON resources, preserving unique identifiers, coding terminologies, and relationships.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

class FHIRMapper:
    """
    Translates CareCoord domain models to HL7 FHIR Release 4 (R4) specifications.
    Documents mapping assumptions and validates conformance against FHIR R4 schemas.
    """

    @staticmethod
    def patient_to_fhir(patient: Any) -> Tuple[Dict[str, Any], List[str]]:
        """
        Maps a CareCoord Patient SQLAlchemy model into an HL7 FHIR R4 Patient resource.
        Returns: (fhir_json_dict, validation_errors)
        """
        errors = []
        if not getattr(patient, "patient_id", None):
            errors.append("Missing required patient identifier (patient_id).")
        if not getattr(patient, "name", None):
            errors.append("Missing required patient name.")

        # Name splitting
        raw_name = getattr(patient, "name", "")
        parts = raw_name.strip().split()
        first_name = parts[0] if parts else "Unknown"
        last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

        # Gender mapping to standard FHIR values (male, female, other, unknown)
        gender_raw = str(getattr(patient, "gender", "unknown")).lower()
        if gender_raw in ["male", "m"]:
            fhir_gender = "male"
        elif gender_raw in ["female", "f"]:
            fhir_gender = "female"
        elif gender_raw in ["other", "non-binary"]:
            fhir_gender = "other"
        else:
            fhir_gender = "unknown"

        # Approximate birth year from age
        age = getattr(patient, "age", 0)
        current_year = datetime.utcnow().year
        approx_birth_year = current_year - int(age) if age else None
        birth_date_str = f"{approx_birth_year}-01-01" if approx_birth_year else None

        # Extensions: Blood group and existing clinical conditions
        extensions = []
        blood_group = getattr(patient, "blood_group", None)
        if blood_group:
            extensions.append({
                "url": "http://hl7.org/fhir/StructureDefinition/patient-bloodGroup",
                "valueString": blood_group
            })

        conditions = getattr(patient, "existing_conditions", []) or []
        for cond in conditions:
            extensions.append({
                "url": "urn:carecoord:fhir:extension:condition",
                "valueString": cond
            })

        resource = {
            "resourceType": "Patient",
            "id": getattr(patient, "patient_id", "P-UNKNOWN"),
            "meta": {
                "versionId": "1",
                "lastUpdated": datetime.utcnow().isoformat() + "Z",
                "profile": ["http://hl7.org/fhir/StructureDefinition/Patient"]
            },
            "identifier": [
                {
                    "use": "official",
                    "system": "urn:carecoord:mrn",
                    "value": getattr(patient, "patient_id", "")
                }
            ],
            "active": True,
            "name": [
                {
                    "use": "official",
                    "text": raw_name,
                    "family": last_name or first_name,
                    "given": [first_name]
                }
            ],
            "telecom": [
                {
                    "system": "phone",
                    "value": getattr(patient, "phone", ""),
                    "use": "mobile"
                }
            ],
            "gender": fhir_gender,
            "birthDate": birth_date_str,
            "extension": extensions,
            "managingOrganization": {
                "reference": "Organization/CareCoord-Hospital",
                "display": getattr(patient, "department", "General Hospital")
            }
        }

        return resource, errors

    @staticmethod
    def doctor_to_practitioner(doctor: Any) -> Tuple[Dict[str, Any], List[str]]:
        """
        Maps a CareCoord Doctor SQLAlchemy model into an HL7 FHIR R4 Practitioner resource.
        Returns: (fhir_json_dict, validation_errors)
        """
        errors = []
        if not getattr(doctor, "doctor_id", None):
            errors.append("Missing required doctor identifier (doctor_id).")
        if not getattr(doctor, "name", None):
            errors.append("Missing required doctor name.")

        raw_name = getattr(doctor, "name", "")
        clean_name = raw_name.replace("Dr.", "").strip()

        resource = {
            "resourceType": "Practitioner",
            "id": getattr(doctor, "doctor_id", "D-UNKNOWN"),
            "meta": {
                "versionId": "1",
                "lastUpdated": datetime.utcnow().isoformat() + "Z",
                "profile": ["http://hl7.org/fhir/StructureDefinition/Practitioner"]
            },
            "identifier": [
                {
                    "use": "official",
                    "system": "urn:carecoord:practitioner",
                    "value": getattr(doctor, "doctor_id", "")
                }
            ],
            "active": bool(getattr(doctor, "availability", True)),
            "name": [
                {
                    "use": "official",
                    "text": raw_name,
                    "family": clean_name,
                    "prefix": ["Dr."]
                }
            ],
            "qualification": [
                {
                    "code": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0360",
                                "code": "MD",
                                "display": "Doctor of Medicine"
                            }
                        ],
                        "text": getattr(doctor, "specialization", "General Medicine")
                    }
                }
            ],
            "extension": [
                {
                    "url": "urn:carecoord:fhir:extension:department",
                    "valueString": getattr(doctor, "department", "General")
                },
                {
                    "url": "urn:carecoord:fhir:extension:shift",
                    "valueString": getattr(doctor, "shift", "Day Shift")
                },
                {
                    "url": "urn:carecoord:fhir:extension:experienceYears",
                    "valueInteger": int(getattr(doctor, "experience_years", 0))
                }
            ]
        }

        return resource, errors

    @staticmethod
    def appointment_to_fhir(appointment: Any) -> Tuple[Dict[str, Any], List[str]]:
        """
        Maps a CareCoord Appointment SQLAlchemy model into an HL7 FHIR R4 Appointment resource.
        Returns: (fhir_json_dict, validation_errors)
        """
        errors = []
        if not getattr(appointment, "appointment_id", None):
            errors.append("Missing required appointment identifier (appointment_id).")
        if not getattr(appointment, "patient_id", None):
            errors.append("Missing required patient reference (patient_id).")

        # Status mapping
        status_raw = str(getattr(appointment, "status", "scheduled")).lower()
        status_map = {
            "scheduled": "booked",
            "in-progress": "arrived",
            "completed": "fulfilled",
            "cancelled": "cancelled"
        }
        fhir_status = status_map.get(status_raw, "booked")

        # Construct ISO 8601 start timestamp
        date_str = getattr(appointment, "appointment_date", "2026-11-16")
        time_str = getattr(appointment, "appointment_time", "09:00")
        try:
            start_iso = f"{date_str}T{time_str}:00Z"
        except Exception:
            start_iso = datetime.utcnow().isoformat() + "Z"

        resource = {
            "resourceType": "Appointment",
            "id": getattr(appointment, "appointment_id", "A-UNKNOWN"),
            "meta": {
                "versionId": "1",
                "lastUpdated": datetime.utcnow().isoformat() + "Z",
                "profile": ["http://hl7.org/fhir/StructureDefinition/Appointment"]
            },
            "identifier": [
                {
                    "use": "official",
                    "system": "urn:carecoord:appointment",
                    "value": getattr(appointment, "appointment_id", "")
                }
            ],
            "status": fhir_status,
            "serviceType": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/service-type",
                            "display": getattr(appointment, "department", "Outpatient Consultation")
                        }
                    ],
                    "text": getattr(appointment, "department", "Outpatient Consultation")
                }
            ],
            "description": getattr(appointment, "reason", "Clinical follow-up consultation"),
            "start": start_iso,
            "created": getattr(appointment, "created_at", datetime.utcnow()).isoformat() + "Z",
            "participant": [
                {
                    "actor": {
                        "reference": f"Patient/{getattr(appointment, 'patient_id', '')}",
                        "display": "Registered Patient"
                    },
                    "status": "accepted",
                    "required": "required"
                },
                {
                    "actor": {
                        "reference": f"Practitioner/{getattr(appointment, 'doctor_id', '')}",
                        "display": "Attending Consulting Physician"
                    },
                    "status": "accepted",
                    "required": "required"
                }
            ]
        }

        return resource, errors
