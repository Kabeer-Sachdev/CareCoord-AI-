"""
FastAPI Routes for Phase 8 MCP External Integrations and FHIR Interoperability.
Exposes endpoints for MCP server lifecycle, dynamic tool discovery, safe execution, health monitoring,
and HL7 FHIR R4 capability statement and resource exports.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.database.models import User
from backend.auth.dependencies import get_current_user, require_role
from backend.services.audit_service import log_audit
from backend.mcp.schemas.mcp_schemas import (
    MCPServerInfo,
    MCPToolDefinition,
    MCPToolExecutionRequest,
    MCPToolExecutionResponse,
    MCPServerConnectRequest,
    MCPHealthResponse,
    FHIRMetadataResponse,
    FHIRExportRequest,
    FHIRExportResponse,
    ExternalAuditLogItem
)
from backend.mcp.client.mcp_client import mcp_client
from backend.mcp.registry.server_registry import server_registry
from backend.mcp.services.integration_service import integration_service
from backend.integrations.fhir.service import fhir_service

router = APIRouter(prefix="/api/integrations", tags=["MCP External Interoperability & FHIR"])

# ------------------------------------------------------------------
# 1. MCP Server Management & Tool Discovery Endpoints
# ------------------------------------------------------------------

@router.get("/mcp/servers", response_model=List[MCPServerInfo], summary="List configured MCP servers")
def list_mcp_servers(current_user: User = Depends(get_current_user)):
    """Lists all configured MCP servers and their active connection states."""
    return server_registry.list_servers()


@router.post("/mcp/servers/connect", response_model=Dict[str, Any], summary="Connect to an MCP server (Admin Only)")
def connect_mcp_server(
    payload: MCPServerConnectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """
    Connects to a configured MCP server and triggers dynamic tool discovery.
    Restricted to hospital administrators.
    """
    success = server_registry.connect_server(payload.server_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP Server '{payload.server_id}' not found in configuration registry."
        )

    tools = server_registry.get_discovered_tools(payload.server_id)
    log_audit(
        db=db,
        user=current_user,
        action="CONNECT_MCP_SERVER",
        entity_type="MCP_SERVER",
        entity_id=payload.server_id,
        metadata={"tools_discovered": len(tools)}
    )

    return {
        "message": f"Successfully connected to MCP Server '{payload.server_id}'.",
        "server_id": payload.server_id,
        "tools_discovered_count": len(tools)
    }


@router.post("/mcp/servers/disconnect", response_model=Dict[str, Any], summary="Disconnect an MCP server (Admin Only)")
def disconnect_mcp_server(
    payload: MCPServerConnectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    """
    Disconnects an MCP server, removing exposed tools from active routing.
    Restricted to hospital administrators.
    """
    success = server_registry.disconnect_server(payload.server_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP Server '{payload.server_id}' not found."
        )

    log_audit(
        db=db,
        user=current_user,
        action="DISCONNECT_MCP_SERVER",
        entity_type="MCP_SERVER",
        entity_id=payload.server_id
    )

    return {
        "message": f"MCP Server '{payload.server_id}' disconnected.",
        "server_id": payload.server_id
    }


@router.get("/mcp/servers/{server_id}/tools", response_model=List[MCPToolDefinition], summary="List tools exposed by an MCP server")
def list_mcp_server_tools(
    server_id: str,
    current_user: User = Depends(get_current_user)
):
    """Lists tools discovered through the official MCP protocol on the specified server."""
    server = server_registry.get_server(server_id)
    if not server:
        raise HTTPException(status_code=404, detail=f"MCP Server '{server_id}' not found.")
    
    return server_registry.get_discovered_tools(server_id)


@router.get("/mcp/tools", response_model=List[MCPToolDefinition], summary="List all discovered MCP tools across all connected servers")
def list_all_mcp_tools(current_user: User = Depends(get_current_user)):
    """Returns all available tools across all active MCP servers."""
    return server_registry.get_discovered_tools()


@router.post("/mcp/tools/execute", response_model=MCPToolExecutionResponse, summary="Execute an MCP tool")
def execute_mcp_tool(
    payload: MCPToolExecutionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Executes an authorized MCP tool with argument validation, RBAC checks, and persistent audit logging.
    """
    return integration_service.execute_tool_with_security(
        server_id=payload.server_id,
        tool_name=payload.tool_name,
        arguments=payload.arguments,
        user=current_user,
        workflow_id=payload.workflow_id,
        db_session=db
    )


@router.get("/mcp/health", response_model=MCPHealthResponse, summary="Get MCP operational health & telemetry")
def get_mcp_health(current_user: User = Depends(get_current_user)):
    """Returns connectivity health, average latency, and success metrics across all MCP servers."""
    return integration_service.get_health()


# ------------------------------------------------------------------
# 2. HL7 FHIR Interoperability Endpoints
# ------------------------------------------------------------------

@router.get("/fhir/metadata", response_model=FHIRMetadataResponse, summary="Get FHIR CapabilityStatement (HL7 FHIR R4)")
def get_fhir_metadata(current_user: User = Depends(get_current_user)):
    """Returns the HL7 FHIR Release 4 CapabilityStatement specifying supported resources and mapping assumptions."""
    return fhir_service.get_capability_statement()


@router.post("/fhir/patient/export", response_model=FHIRExportResponse, summary="Export Patient to HL7 FHIR R4 Resource")
def export_patient_fhir(
    payload: FHIRExportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Translates a CareCoord internal Patient model into an HL7 FHIR R4 Patient JSON resource.
    Validates mandatory attributes and records an export audit trail.
    """
    return fhir_service.export_patient(
        patient_id=payload.entity_id,
        validate_only=payload.validate_only,
        user_id=str(current_user.id)
    )


@router.post("/fhir/appointment/export", response_model=FHIRExportResponse, summary="Export Appointment to HL7 FHIR R4 Resource")
def export_appointment_fhir(
    payload: FHIRExportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Translates a CareCoord internal Appointment model into an HL7 FHIR R4 Appointment JSON resource.
    Preserves references to Patient and Practitioner.
    """
    return fhir_service.export_appointment(
        appointment_id=payload.entity_id,
        validate_only=payload.validate_only,
        user_id=str(current_user.id)
    )


# ------------------------------------------------------------------
# 3. Integration Audit Logging
# ------------------------------------------------------------------

@router.get("/audit", response_model=List[ExternalAuditLogItem], summary="Get MCP external tool invocation audit log")
def get_integration_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user)
):
    """Returns recent tool execution history from external MCP integrations."""
    return integration_service.get_audit_logs(limit=limit)
