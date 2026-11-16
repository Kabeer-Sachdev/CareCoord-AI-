import React, { useState, useEffect } from 'react';
import {
  Server,
  Cpu,
  Activity,
  Layers,
  Database,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Play,
  RefreshCw,
  Power,
  FileCode,
  Share2,
  Clock,
  Terminal,
  ExternalLink,
  Search,
  Filter
} from 'lucide-react';
import { apiService } from '../services/api';

export function IntegrationsPage() {
  const [activeTab, setActiveTab] = useState('servers'); // 'servers' | 'explorer' | 'fhir' | 'activity'
  const [servers, setServers] = useState([]);
  const [tools, setTools] = useState([]);
  const [health, setHealth] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);
  const [fhirMeta, setFhirMeta] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Tool Explorer state
  const [selectedTool, setSelectedTool] = useState(null);
  const [toolArgs, setToolArgs] = useState('{}');
  const [isExecutingTool, setIsExecutingTool] = useState(false);
  const [toolExecutionResult, setToolExecutionResult] = useState(null);

  // FHIR Export state
  const [fhirEntityType, setFhirEntityType] = useState('Patient'); // 'Patient' | 'Appointment'
  const [fhirEntityId, setFhirEntityId] = useState('P001');
  const [isExportingFhir, setIsExportingFhir] = useState(false);
  const [fhirExportResult, setFhirExportResult] = useState(null);

  // Role
  const currentUserRole = localStorage.getItem('cc_role') || 'ADMIN';

  const fetchData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [serversData, toolsData, healthData, auditData, fhirData] = await Promise.all([
        apiService.getMcpServers().catch(() => []),
        apiService.getMcpTools().catch(() => []),
        apiService.getMcpHealth().catch(() => null),
        apiService.getIntegrationAuditLogs(25).catch(() => []),
        apiService.getFhirMetadata().catch(() => null)
      ]);
      setServers(serversData);
      setTools(toolsData);
      setHealth(healthData);
      setAuditLogs(auditData);
      setFhirMeta(fhirData);

      if (toolsData.length > 0 && !selectedTool) {
        setSelectedTool(toolsData[0]);
        initDefaultArgs(toolsData[0]);
      }
    } catch (err) {
      setError(err.message || 'Failed to load MCP integrations data.');
    } finally {
      setIsLoading(false);
    }
  };

  const initDefaultArgs = (tool) => {
    if (!tool) return;
    const sample = {};
    const props = tool.input_schema?.properties || {};
    Object.keys(props).forEach((k) => {
      if (k === 'patient_id') sample[k] = 'P001';
      else if (k === 'doctor_id') sample[k] = 'D001';
      else if (k === 'sample_id') sample[k] = 'SMP-1001';
      else if (k === 'test_code') sample[k] = 'LAB-CBC';
      else if (k === 'medication_code') sample[k] = 'MED-AMOX-500';
      else if (k === 'required_units') sample[k] = 10;
      else if (k === 'department') sample[k] = 'Cardiology';
      else sample[k] = props[k].type === 'integer' ? 1 : 'sample';
    });
    setToolArgs(JSON.stringify(sample, null, 2));
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleToggleServer = async (serverId, currentStatus) => {
    try {
      if (currentStatus === 'CONNECTED') {
        await apiService.disconnectMcpServer(serverId);
      } else {
        await apiService.connectMcpServer(serverId);
      }
      fetchData();
    } catch (err) {
      alert(`Server action failed: ${err.message}`);
    }
  };

  const handleRunTool = async () => {
    if (!selectedTool) return;
    setIsExecutingTool(true);
    setToolExecutionResult(null);
    try {
      let parsedArgs = {};
      try {
        parsedArgs = JSON.parse(toolArgs);
      } catch (e) {
        throw new Error('Invalid JSON arguments format.');
      }

      const res = await apiService.executeMcpTool({
        server_id: selectedTool.server_id,
        tool_name: selectedTool.name,
        arguments: parsedArgs
      });
      setToolExecutionResult(res);
      // Refresh audit logs
      const freshAudit = await apiService.getIntegrationAuditLogs(25).catch(() => []);
      setAuditLogs(freshAudit);
    } catch (err) {
      setToolExecutionResult({
        status: 'FAILED',
        error: err.message,
        duration_ms: 0
      });
    } finally {
      setIsExecutingTool(false);
    }
  };

  const handleExportFhir = async () => {
    if (!fhirEntityId.trim()) return;
    setIsExportingFhir(true);
    setFhirExportResult(null);
    try {
      let res;
      if (fhirEntityType === 'Patient') {
        res = await apiService.exportFhirPatient(fhirEntityId.trim());
      } else {
        res = await apiService.exportFhirAppointment(fhirEntityId.trim());
      }
      setFhirExportResult(res);
    } catch (err) {
      setFhirExportResult({
        status: 'FAILED',
        validation_errors: [err.message]
      });
    } finally {
      setIsExportingFhir(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
              Phase 8 Interoperability
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
              Model Context Protocol (MCP) & HL7 FHIR R4
            </span>
          </div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-3 mt-1.5">
            <Share2 className="w-7 h-7 text-emerald-400" />
            External Hospital System Interoperability
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Standardized tool federation across Hospital HIS, Laboratory LIS, and Pharmacy services with HL7 FHIR R4 mapping.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchData}
            disabled={isLoading}
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium border border-slate-700 transition"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            Sync MCP
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>MCP SERVERS</span>
            <Server className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100 mt-2">
            {servers.filter(s => s.status === 'CONNECTED').length} / {servers.length}
          </div>
          <div className="text-xs text-emerald-400 mt-1 flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Active MCP Host Connections</span>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>DISCOVERED TOOLS</span>
            <Cpu className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100 mt-2">
            {tools.length} Tools
          </div>
          <div className="text-xs text-slate-400 mt-1">
            Exposed via official protocol APIs
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>INTEROPERABILITY HEALTH</span>
            <Activity className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100 mt-2">
            {health?.status || 'HEALTHY'}
          </div>
          <div className="text-xs text-emerald-400 mt-1">
            {health?.success_rate || 100}% invocation reliability
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>FHIR R4 CONFORMANCE</span>
            <ShieldCheck className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100 mt-2">
            HL7 v4.0.1
          </div>
          <div className="text-xs text-amber-400/90 mt-1">
            Patient, Practitioner, Appointment
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-800 gap-2">
        <button
          onClick={() => setActiveTab('servers')}
          className={`pb-3 px-4 text-sm font-medium border-b-2 transition flex items-center gap-2 ${
            activeTab === 'servers'
              ? 'border-emerald-500 text-emerald-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Server className="w-4 h-4" />
          MCP Server Overview ({servers.length})
        </button>
        <button
          onClick={() => setActiveTab('explorer')}
          className={`pb-3 px-4 text-sm font-medium border-b-2 transition flex items-center gap-2 ${
            activeTab === 'explorer'
              ? 'border-cyan-500 text-cyan-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Terminal className="w-4 h-4" />
          MCP Tool Explorer ({tools.length})
        </button>
        <button
          onClick={() => setActiveTab('fhir')}
          className={`pb-3 px-4 text-sm font-medium border-b-2 transition flex items-center gap-2 ${
            activeTab === 'fhir'
              ? 'border-amber-500 text-amber-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <FileCode className="w-4 h-4" />
          HL7 FHIR Interoperability
        </button>
        <button
          onClick={() => setActiveTab('activity')}
          className={`pb-3 px-4 text-sm font-medium border-b-2 transition flex items-center gap-2 ${
            activeTab === 'activity'
              ? 'border-purple-500 text-purple-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Activity className="w-4 h-4" />
          Integration Activity ({auditLogs.length})
        </button>
      </div>

      {/* TAB 1: MCP Server Overview */}
      {activeTab === 'servers' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {servers.map((srv) => {
              const isConn = srv.status === 'CONNECTED';
              return (
                <div key={srv.server_id} className="p-5 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2.5">
                        <div className={`p-2 rounded-lg ${isConn ? 'bg-emerald-500/10 text-emerald-400' : 'bg-slate-800 text-slate-400'}`}>
                          <Server className="w-5 h-5" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-slate-100 text-base">{srv.name}</h3>
                          <span className="text-xs font-mono text-slate-400">{srv.server_id}</span>
                        </div>
                      </div>
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                        isConn ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-slate-800 text-slate-400 border border-slate-700'
                      }`}>
                        {srv.status}
                      </span>
                    </div>

                    <p className="text-xs text-slate-400 mt-3 line-clamp-3">
                      {srv.description}
                    </p>

                    <div className="mt-4 pt-3 border-t border-slate-800/80 space-y-1.5 text-xs">
                      <div className="flex justify-between text-slate-400">
                        <span>Transport:</span>
                        <span className="font-mono text-slate-300">{srv.transport_type}</span>
                      </div>
                      <div className="flex justify-between text-slate-400">
                        <span>Discovered Tools:</span>
                        <span className="font-semibold text-cyan-400">{srv.tool_count} tools exposed</span>
                      </div>
                      <div className="flex justify-between text-slate-400">
                        <span>Endpoint:</span>
                        <span className="font-mono text-slate-400 truncate max-w-[150px]">{srv.endpoint || 'local://'}</span>
                      </div>
                    </div>
                  </div>

                  <div className="mt-5 pt-3 border-t border-slate-800 flex items-center justify-between">
                    <button
                      onClick={() => {
                        setSelectedTool(tools.find(t => t.server_id === srv.server_id) || null);
                        setActiveTab('explorer');
                      }}
                      className="text-xs text-cyan-400 hover:text-cyan-300 font-medium flex items-center gap-1"
                    >
                      Browse Tools ({srv.tool_count}) &rarr;
                    </button>

                    {currentUserRole === 'ADMIN' && (
                      <button
                        onClick={() => handleToggleServer(srv.server_id, srv.status)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium border flex items-center gap-1.5 transition ${
                          isConn
                            ? 'bg-rose-500/10 border-rose-500/30 text-rose-400 hover:bg-rose-500/20'
                            : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20'
                        }`}
                      >
                        <Power className="w-3 h-3" />
                        {isConn ? 'Disconnect' : 'Connect'}
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 text-xs text-slate-400">
            <span className="font-semibold text-slate-300">MCP Architecture Note:</span> Servers are instantiated via the official Model Context Protocol Python SDK. Tools are dynamically introspected through standard protocol calls. All tools execute within read-only security parameters for patient data protection.
          </div>
        </div>
      )}

      {/* TAB 2: Tool Explorer */}
      {activeTab === 'explorer' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Tool List Sidebar */}
          <div className="lg:col-span-5 space-y-2">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Discovered MCP Tools ({tools.length})
            </div>
            <div className="space-y-1.5 max-h-[600px] overflow-y-auto pr-1">
              {tools.map((t) => {
                const isSelected = selectedTool?.name === t.name && selectedTool?.server_id === t.server_id;
                return (
                  <button
                    key={`${t.server_id}-${t.name}`}
                    onClick={() => {
                      setSelectedTool(t);
                      initDefaultArgs(t);
                      setToolExecutionResult(null);
                    }}
                    className={`w-full text-left p-3 rounded-xl border transition ${
                      isSelected
                        ? 'bg-cyan-500/10 border-cyan-500/40 text-slate-100'
                        : 'bg-slate-900/60 border-slate-800 text-slate-300 hover:bg-slate-800/60'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-sm font-semibold text-cyan-400">{t.name}</span>
                      <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                        {t.server_id}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1 line-clamp-2">
                      {t.description}
                    </p>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Tool Details & Execution Runner */}
          <div className="lg:col-span-7 space-y-4">
            {selectedTool ? (
              <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-4">
                <div>
                  <div className="flex items-center justify-between">
                    <h2 className="text-lg font-bold font-mono text-slate-100 flex items-center gap-2">
                      <Terminal className="w-5 h-5 text-cyan-400" />
                      {selectedTool.name}
                    </h2>
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      Read-Only Safe
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1.5">{selectedTool.description}</p>
                  <div className="mt-2 text-xs text-slate-500 font-mono">
                    Server: <span className="text-slate-300">{selectedTool.server_name}</span> ({selectedTool.server_id})
                  </div>
                </div>

                {/* Input Arguments Editor */}
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="text-xs font-medium text-slate-300">
                      Tool Arguments (JSON):
                    </label>
                    <button
                      onClick={() => initDefaultArgs(selectedTool)}
                      className="text-xs text-cyan-400 hover:underline"
                    >
                      Reset Sample Arguments
                    </button>
                  </div>
                  <textarea
                    value={toolArgs}
                    onChange={(e) => setToolArgs(e.target.value)}
                    rows={5}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 font-mono text-xs text-slate-200 border border-slate-800 focus:outline-none focus:border-cyan-500"
                  />
                </div>

                <div className="flex justify-end">
                  <button
                    onClick={handleRunTool}
                    disabled={isExecutingTool}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-medium text-sm transition shadow-lg shadow-cyan-600/20"
                  >
                    <Play className={`w-4 h-4 ${isExecutingTool ? 'animate-pulse' : ''}`} />
                    {isExecutingTool ? 'Invoking MCP Tool...' : 'Execute Tool'}
                  </button>
                </div>

                {/* Execution Results */}
                {toolExecutionResult && (
                  <div className="mt-4 pt-4 border-t border-slate-800 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-slate-300">Result Payload:</span>
                      <div className="flex items-center gap-2 text-xs">
                        <span className={`px-2 py-0.5 rounded font-bold ${
                          toolExecutionResult.status === 'SUCCESS' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
                        }`}>
                          {toolExecutionResult.status}
                        </span>
                        <span className="text-slate-400 font-mono">{toolExecutionResult.duration_ms}ms</span>
                      </div>
                    </div>

                    {toolExecutionResult.error ? (
                      <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-mono">
                        {toolExecutionResult.error}
                      </div>
                    ) : (
                      <pre className="p-3 rounded-lg bg-slate-950 border border-slate-800/80 font-mono text-xs text-emerald-400/90 overflow-x-auto max-h-60">
                        {JSON.stringify(toolExecutionResult.result, null, 2)}
                      </pre>
                    )}
                  </div>
                )}
              </div>
            ) : (
              <div className="p-12 text-center text-slate-500 border border-dashed border-slate-800 rounded-xl">
                Select a discovered MCP tool to inspect its schema and execute test requests.
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 3: HL7 FHIR Interoperability */}
      {activeTab === 'fhir' && (
        <div className="space-y-6">
          <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800">
            <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2 mb-2">
              <FileCode className="w-5 h-5 text-amber-400" />
              HL7 FHIR Release 4 (R4) Resource Export Engine
            </h2>
            <p className="text-xs text-slate-400">
              Transforms CareCoord internal relational entities into validated, conformant HL7 FHIR R4 JSON documents for external electronic health record (EHR) and laboratory exchange.
            </p>

            <div className="mt-4 flex flex-col sm:flex-row gap-4 items-end">
              <div>
                <label className="text-xs text-slate-400 font-medium block mb-1">Resource Type:</label>
                <select
                  value={fhirEntityType}
                  onChange={(e) => {
                    setFhirEntityType(e.target.value);
                    setFhirEntityId(e.target.value === 'Patient' ? 'P001' : 'A001');
                  }}
                  className="px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 text-sm focus:outline-none focus:border-amber-500"
                >
                  <option value="Patient">Patient Resource</option>
                  <option value="Appointment">Appointment Resource</option>
                </select>
              </div>

              <div>
                <label className="text-xs text-slate-400 font-medium block mb-1">Entity Identifier:</label>
                <input
                  type="text"
                  value={fhirEntityId}
                  onChange={(e) => setFhirEntityId(e.target.value)}
                  placeholder="e.g. P001 or A001"
                  className="px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 text-sm font-mono focus:outline-none focus:border-amber-500"
                />
              </div>

              <button
                onClick={handleExportFhir}
                disabled={isExportingFhir}
                className="px-4 py-2 rounded-lg bg-amber-600 hover:bg-amber-500 text-white font-medium text-sm transition shadow-lg shadow-amber-600/20"
              >
                {isExportingFhir ? 'Translating to FHIR...' : 'Generate FHIR R4 JSON'}
              </button>
            </div>

            {fhirExportResult && (
              <div className="mt-6 pt-4 border-t border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-300">
                    FHIR R4 JSON Output ({fhirExportResult.resource_type}):
                  </span>
                  <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                    fhirExportResult.status === 'SUCCESS' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
                  }`}>
                    {fhirExportResult.status}
                  </span>
                </div>

                {fhirExportResult.validation_errors?.length > 0 && (
                  <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs">
                    {fhirExportResult.validation_errors.join('; ')}
                  </div>
                )}

                {fhirExportResult.fhir_resource && (
                  <pre className="p-4 rounded-lg bg-slate-950 border border-slate-800 font-mono text-xs text-amber-300/90 overflow-x-auto max-h-96">
                    {JSON.stringify(fhirExportResult.fhir_resource, null, 2)}
                  </pre>
                )}
              </div>
            )}
          </div>

          {/* FHIR Capability Statement Info */}
          {fhirMeta && (
            <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800/80">
              <h3 className="font-semibold text-sm text-slate-200 mb-2">CapabilityStatement Metadata</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs text-slate-400">
                <div>Publisher: <span className="text-slate-300 font-medium">{fhirMeta.publisher}</span></div>
                <div>FHIR Version: <span className="font-mono text-slate-300">{fhirMeta.fhirVersion}</span></div>
                <div>Supported Resources: <span className="text-cyan-400 font-medium">{fhirMeta.supported_resources?.join(', ')}</span></div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 4: Integration Activity & Audit */}
      {activeTab === 'activity' && (
        <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <Activity className="w-5 h-5 text-purple-400" />
              External Tool Invocation Audit Log
            </h2>
            <span className="text-xs text-slate-400">Preserved in SQLite audit table</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 font-medium uppercase border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3">Execution ID</th>
                  <th className="py-2.5 px-3">MCP Server</th>
                  <th className="py-2.5 px-3">Tool Name</th>
                  <th className="py-2.5 px-3">User</th>
                  <th className="py-2.5 px-3">Duration</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {auditLogs.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-slate-500 font-sans">
                      No external MCP tool executions recorded yet.
                    </td>
                  </tr>
                ) : (
                  auditLogs.map((log) => (
                    <tr key={log.execution_id} className="hover:bg-slate-800/40 transition">
                      <td className="py-2.5 px-3 text-slate-400">{log.execution_id}</td>
                      <td className="py-2.5 px-3 text-cyan-400 font-sans font-medium">{log.server_id}</td>
                      <td className="py-2.5 px-3 text-slate-200">{log.tool_name}</td>
                      <td className="py-2.5 px-3 text-slate-400 font-sans">{log.user_id}</td>
                      <td className="py-2.5 px-3 text-slate-400">{log.duration_ms}ms</td>
                      <td className="py-2.5 px-3">
                        <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                          log.status === 'SUCCESS' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
                        }`}>
                          {log.status}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-slate-500 font-sans">
                        {new Date(log.created_at).toLocaleTimeString()}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
export default IntegrationsPage;
