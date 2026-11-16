from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class MCPServerInfo(BaseModel):
    server_id: str
    name: str
    description: Optional[str] = None
    transport_type: str = "in-memory"  # in-memory, stdio, sse
    endpoint: Optional[str] = None
    status: str = "DISCONNECTED"  # CONNECTED, DISCONNECTED, ERROR
    is_enabled: bool = True
    tool_count: int = 0
    last_connected_at: Optional[datetime] = None

class MCPToolDefinition(BaseModel):
    name: str
    server_id: str
    server_name: str
    description: Optional[str] = None
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    required_role: str = "PATIENT"
    read_only: bool = True

class MCPToolExecutionRequest(BaseModel):
    server_id: str
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    workflow_id: Optional[str] = None

class MCPToolExecutionResponse(BaseModel):
    execution_id: str
    server_id: str
    tool_name: str
    status: str  # SUCCESS, FAILED, BLOCKED
    result: Optional[Dict[str, Any]] = None
    duration_ms: float = 0.0
    error: Optional[str] = None

class MCPServerConnectRequest(BaseModel):
    server_id: str

class MCPHealthResponse(BaseModel):
    status: str = "HEALTHY"
    total_servers: int = 0
    connected_servers: int = 0
    total_tools: int = 0
    avg_response_time_ms: float = 0.0
    success_rate: float = 100.0

class FHIRMetadataResponse(BaseModel):
    resourceType: str = "CapabilityStatement"
    id: str = "carecoord-fhir-capability"
    status: str = "active"
    date: str
    publisher: str = "CareCoord Health Interoperability Hub"
    kind: str = "capability"
    fhirVersion: str = "4.0.1"
    format: List[str] = ["json"]
    supported_resources: List[str] = ["Patient", "Practitioner", "Appointment"]
    mapping_assumptions: Dict[str, str] = Field(default_factory=dict)

class FHIRExportRequest(BaseModel):
    entity_id: str
    validate_only: bool = False

class FHIRExportResponse(BaseModel):
    export_id: str
    resource_type: str
    entity_id: str
    status: str  # SUCCESS, VALIDATION_ERROR, FAILED
    fhir_resource: Optional[Dict[str, Any]] = None
    validation_errors: List[str] = Field(default_factory=list)

class ExternalAuditLogItem(BaseModel):
    execution_id: str
    server_id: str
    tool_name: str
    user_id: Optional[str] = None
    workflow_id: Optional[str] = None
    status: str
    duration_ms: float
    error_summary: Optional[str] = None
    created_at: datetime
