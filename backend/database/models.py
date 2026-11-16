from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from backend.database.database import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(20), nullable=False)
    phone = Column(String(20), nullable=False)
    department = Column(String(100), nullable=False)
    blood_group = Column(String(10), nullable=False)
    existing_conditions = Column(JSON, nullable=True, default=list)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")
    beds = relationship("Bed", back_populates="patient")
    emergencies = relationship("Emergency", back_populates="patient", cascade="all, delete-orphan")


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    doctor_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    specialization = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    experience_years = Column(Integer, nullable=False, default=0)
    availability = Column(Boolean, default=True, nullable=False)
    availability_status = Column(String(50), default="Available", nullable=True)
    shift = Column(String(50), nullable=False)
    current_patients = Column(Integer, default=0, nullable=False)

    # Relationships
    appointments = relationship("Appointment", back_populates="doctor")
    assigned_emergencies = relationship("Emergency", back_populates="assigned_doctor")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    appointment_id = Column(String(50), unique=True, index=True, nullable=False)
    patient_id = Column(String(50), ForeignKey("patients.patient_id"), nullable=False)
    doctor_id = Column(String(50), ForeignKey("doctors.doctor_id"), nullable=False)
    appointment_date = Column(String(20), nullable=False)
    appointment_time = Column(String(20), nullable=False)
    department = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default="scheduled")  # scheduled, completed, cancelled, pending
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")


class Bed(Base):
    __tablename__ = "beds"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    bed_id = Column(String(50), unique=True, index=True, nullable=False)
    ward = Column(String(50), nullable=False)
    bed_type = Column(String(50), nullable=False)  # General, ICU, Emergency, Private
    status = Column(String(20), nullable=False, default="available")  # available, occupied, maintenance
    floor = Column(Integer, nullable=False)
    patient_id = Column(String(50), ForeignKey("patients.patient_id"), nullable=True)

    # Relationships
    patient = relationship("Patient", back_populates="beds")


class Emergency(Base):
    __tablename__ = "emergencies"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    emergency_id = Column(String(50), unique=True, index=True, nullable=False)
    patient_id = Column(String(50), ForeignKey("patients.patient_id"), nullable=False)
    priority = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    required_department = Column(String(100), nullable=False)
    required_bed_type = Column(String(50), nullable=False)
    assigned_doctor_id = Column(String(50), ForeignKey("doctors.doctor_id"), nullable=True)
    status = Column(String(20), nullable=False, default="waiting")  # waiting, being_processed, allocated, completed
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    patient = relationship("Patient", back_populates="emergencies")
    assigned_doctor = relationship("Doctor", back_populates="assigned_emergencies")


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    workflow_id = Column(String(50), unique=True, index=True, nullable=False)
    original_request = Column(Text, nullable=False)
    workflow_type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default="RUNNING")  # RUNNING, NEEDS_CLARIFICATION, REQUIRES_HUMAN_APPROVAL, APPROVED, REJECTED, COMPLETED, FAILED
    requires_human_approval = Column(Boolean, default=False, nullable=False)
    agent_used = Column(String(100), nullable=True)
    requested_by = Column(String(50), nullable=True)
    requested_role = Column(String(50), nullable=True)
    recommendation = Column(Text, nullable=True)
    final_result = Column(JSON, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    events = relationship("WorkflowEvent", back_populates="workflow_run", cascade="all, delete-orphan")


class WorkflowEvent(Base):
    __tablename__ = "workflow_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    workflow_id = Column(String(50), ForeignKey("workflow_runs.workflow_id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    agent_name = Column(String(50), nullable=False)
    node_name = Column(String(50), nullable=False)
    event_type = Column(String(50), nullable=False)  # node_start, tool_call, tool_result, validation, approval_required, approved, rejected, completed, failed
    status = Column(String(50), nullable=False)
    tool_name = Column(String(50), nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    details = Column(JSON, nullable=True)

    # Relationships
    workflow_run = relationship("WorkflowRun", back_populates="events")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # ADMIN, RECEPTIONIST, DOCTOR, NURSE, PATIENT
    full_name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    patient_id = Column(String(50), ForeignKey("patients.patient_id"), nullable=True)
    doctor_id = Column(String(50), ForeignKey("doctors.doctor_id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String(50), nullable=False)
    title = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    priority = Column(String(20), default="NORMAL", nullable=False)  # LOW, NORMAL, HIGH, CRITICAL
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="notifications")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    username = Column(String(50), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    meta_data = Column(JSON, nullable=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")


class PolicyDocument(Base):
    __tablename__ = "policy_documents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(200), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(20), nullable=False)  # PDF, DOCX, TXT
    department = Column(String(100), default="General", nullable=False)
    status = Column(String(50), default="PENDING", nullable=False)  # PENDING, PROCESSING, INDEXED, FAILED
    chunk_count = Column(Integer, default=0, nullable=False)
    file_size_bytes = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    chunks = relationship("PolicyChunk", back_populates="document", cascade="all, delete-orphan")


class PolicyChunk(Base):
    __tablename__ = "policy_chunks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    chunk_id = Column(String(50), unique=True, index=True, nullable=False)
    document_id = Column(String(50), ForeignKey("policy_documents.document_id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, default=0, nullable=False)
    page_number = Column(Integer, nullable=True)
    section_header = Column(String(255), nullable=True)
    chroma_id = Column(String(100), index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    document = relationship("PolicyDocument", back_populates="chunks")


class OptimizationRun(Base):
    __tablename__ = "optimization_runs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    optimization_id = Column(String(50), unique=True, index=True, nullable=False)
    optimization_type = Column(String(50), nullable=False)  # APPOINTMENT_SCHEDULING, DOCTOR_SCHEDULING, BED_ALLOCATION
    department = Column(String(100), nullable=True)
    target_date = Column(String(20), nullable=False)
    solver_status = Column(String(50), nullable=False)  # OPTIMAL, FEASIBLE, INFEASIBLE, UNKNOWN, FAILED
    objective_value = Column(Float, default=0.0, nullable=False)
    execution_duration_ms = Column(Float, default=0.0, nullable=False)
    constraint_validation = Column(String(50), default="PASSED", nullable=False)  # PASSED, WARNING, FAILED
    total_requests = Column(Integer, default=0, nullable=False)
    allocated_count = Column(Integer, default=0, nullable=False)
    unallocated_count = Column(Integer, default=0, nullable=False)
    approval_status = Column(String(50), default="PENDING_APPROVAL", nullable=False)  # PENDING_APPROVAL, APPROVED, REJECTED, COMMITTED
    requires_human_approval = Column(Boolean, default=True, nullable=False)
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    ml_forecast_snapshot = Column(JSON, nullable=True, default=dict)
    metrics_snapshot = Column(JSON, nullable=True, default=dict)
    parameters = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    allocations = relationship("OptimizationAllocation", back_populates="run", cascade="all, delete-orphan")


class OptimizationAllocation(Base):
    __tablename__ = "optimization_allocations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    optimization_id = Column(String(50), ForeignKey("optimization_runs.optimization_id"), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)  # APPOINTMENT, DOCTOR_SHIFT, BED_ASSIGNMENT
    request_id = Column(String(50), nullable=False)
    patient_id = Column(String(50), nullable=True)
    patient_name = Column(String(100), nullable=True)
    doctor_id = Column(String(50), nullable=True)
    doctor_name = Column(String(100), nullable=True)
    bed_id = Column(String(50), nullable=True)
    ward = Column(String(50), nullable=True)
    department = Column(String(100), nullable=True)
    allocated_time_slot = Column(String(50), nullable=True)
    shift_name = Column(String(50), nullable=True)
    allocation_status = Column(String(50), nullable=False)  # ALLOCATED, UNALLOCATED
    reason = Column(Text, nullable=True)
    is_committed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    run = relationship("OptimizationRun", back_populates="allocations")


# ------------------------------------------------------------------
# Phase 8: MCP External Integrations & FHIR Interoperability Models
# ------------------------------------------------------------------

class MCPServerRecord(Base):
    __tablename__ = "mcp_servers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    server_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    transport_type = Column(String(50), default="stdio", nullable=False)  # stdio, in-memory, sse
    endpoint = Column(String(255), nullable=True)
    status = Column(String(50), default="DISCONNECTED", nullable=False)  # CONNECTED, DISCONNECTED, ERROR
    is_enabled = Column(Boolean, default=True, nullable=False)
    tool_count = Column(Integer, default=0, nullable=False)
    last_connected_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class MCPToolExecution(Base):
    __tablename__ = "mcp_tool_executions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    execution_id = Column(String(50), unique=True, index=True, nullable=False)
    server_id = Column(String(50), nullable=False, index=True)
    tool_name = Column(String(100), nullable=False, index=True)
    user_id = Column(String(50), nullable=True)
    workflow_id = Column(String(50), nullable=True)
    arguments = Column(JSON, nullable=True, default=dict)
    result = Column(JSON, nullable=True, default=dict)
    status = Column(String(50), default="SUCCESS", nullable=False)  # SUCCESS, FAILED, BLOCKED
    duration_ms = Column(Float, default=0.0, nullable=False)
    error_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class FHIRExportLog(Base):
    __tablename__ = "fhir_export_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    export_id = Column(String(50), unique=True, index=True, nullable=False)
    resource_type = Column(String(50), nullable=False, index=True)  # Patient, Practitioner, Appointment
    entity_id = Column(String(50), nullable=False, index=True)
    user_id = Column(String(50), nullable=True)
    status = Column(String(50), default="SUCCESS", nullable=False)  # SUCCESS, VALIDATION_ERROR, FAILED
    resource_payload = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)





