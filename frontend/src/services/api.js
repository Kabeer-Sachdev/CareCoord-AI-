const API_BASE_URL = '/api';

function getToken() {
  return localStorage.getItem('cc_token');
}

async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const token = getToken();
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
    ...options,
  };
  try {
    const response = await fetch(url, config);
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP Error ${response.status}: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`API Request Error [${endpoint}]:`, error);
    throw error;
  }
}

export const apiService = {
  // Auth & Account
  login: (credentials) => request('/auth/login', { method: 'POST', body: JSON.stringify(credentials) }),
  register: (data) => request('/auth/register', { method: 'POST', body: JSON.stringify(data) }),
  getCurrentUser: () => request('/auth/me'),

  // Dashboard & Workflow
  getDashboardSummary: () => request('/dashboard/summary'),
  sendWorkflowRequest: (message) => request('/workflow/request', { method: 'POST', body: JSON.stringify({ message }) }),

  // Phase 3 Stateful LangGraph Workflows
  getWorkflows: () => request('/workflows'),
  getWorkflowById: (id) => request(`/workflows/${id}`),
  getWorkflowEvents: (id) => request(`/workflows/${id}/events`),
  approveWorkflow: (id, notes) => request(`/workflows/${id}/approve`, { method: 'POST', body: JSON.stringify({ action: 'approve', notes: notes || 'Approved via Hospital Command Terminal' }) }),
  rejectWorkflow: (id, notes) => request(`/workflows/${id}/reject`, { method: 'POST', body: JSON.stringify({ action: 'reject', notes: notes || 'Rejected via Hospital Command Terminal' }) }),

  // Patients
  getPatients: () => request('/patients'),
  getPatientById: (id) => request(`/patients/${id}`),
  createPatient: (data) => request('/patients', { method: 'POST', body: JSON.stringify(data) }),

  // Doctors
  getDoctors: () => request('/doctors'),
  getAvailableDoctors: () => request('/doctors/available'),
  getDoctorsBySpecialization: (spec) => request(`/doctors/specialization/${encodeURIComponent(spec)}`),
  getDoctorById: (id) => request(`/doctors/${id}`),
  updateDoctorStatus: (id, availability_status, notes) => request(`/doctors/${id}/status`, { method: 'PUT', body: JSON.stringify({ availability_status, notes }) }),

  // Appointments
  getAppointments: () => request('/appointments'),
  getDoctorAppointments: (doctorId) => request(`/appointments/doctor/${doctorId}`),
  getPatientAppointments: (patientId) => request(`/appointments/patient/${patientId}`),
  createAppointment: (data) => request('/appointments', { method: 'POST', body: JSON.stringify(data) }),
  updateAppointmentStatus: (id, status, notes) => request(`/appointments/${id}/status`, { method: 'PUT', body: JSON.stringify({ status, notes }) }),
  deleteAppointment: (id) => request(`/appointments/${id}`, { method: 'DELETE' }),

  // Beds
  getBeds: () => request('/beds'),
  getAvailableBeds: () => request('/beds/available'),
  updateBedStatus: (id, status, patient_id, notes) => request(`/beds/${id}/status`, { method: 'PUT', body: JSON.stringify({ status, patient_id, notes }) }),
  transferPatient: (data) => request('/beds/transfer', { method: 'POST', body: JSON.stringify(data) }),

  // Emergencies
  getEmergencies: () => request('/emergencies'),
  createEmergency: (data) => request('/emergencies', { method: 'POST', body: JSON.stringify(data) }),
  updateEmergency: (id, data) => request(`/emergencies/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  // Auth & Notifications (Phase 4)
  getNotifications: () => request('/notifications'),
  markNotificationRead: (id) => request(`/notifications/${id}/read`, { method: 'PUT' }),
  markAllNotificationsRead: () => request('/notifications/read-all', { method: 'PUT' }),
  getUsers: () => request('/auth/users'),
  getAuditLogs: (limit = 50) => request(`/auth/audit-logs?limit=${limit}`),

  // Phase 5 Policy Intelligence (RAG)
  getPolicies: (department) => request(department && department !== 'All' ? `/policies?department=${encodeURIComponent(department)}` : '/policies'),
  getPolicyById: (id) => request(`/policies/${id}`),
  getPolicyChunks: (id) => request(`/policies/${id}/chunks`),
  deletePolicy: (id) => request(`/policies/${id}`, { method: 'DELETE' }),
  reprocessPolicy: (id) => request(`/policies/${id}/reprocess`, { method: 'POST' }),
  askPolicy: (data) => request('/policies/ask', { method: 'POST', body: JSON.stringify(data) }),
  uploadPolicy: async (formData) => {
    const token = getToken();
    const response = await fetch(`${API_BASE_URL}/policies/upload`, {
      method: 'POST',
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {})
      },
      body: formData
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || `Upload failed: ${response.statusText}`);
    }
    return await response.json();
  },

  // Phase 6 Machine Learning Resource Demand Prediction
  getMlOverview: (date) => request(date ? `/ml/forecast/overview?forecast_date=${encodeURIComponent(date)}` : '/ml/forecast/overview'),
  getMlMetrics: () => request('/ml/metrics'),
  getMlModels: () => request('/ml/models'),
  predictPatientArrivals: (data) => request('/ml/predict/patient-arrivals', { method: 'POST', body: JSON.stringify(data) }),
  predictEmergencyDemand: (data) => request('/ml/predict/emergency-demand', { method: 'POST', body: JSON.stringify(data) }),
  predictBedOccupancy: (data) => request('/ml/predict/bed-occupancy', { method: 'POST', body: JSON.stringify(data) }),
  predictAppointmentDemand: (data) => request('/ml/predict/appointment-demand', { method: 'POST', body: JSON.stringify(data) }),
  trainMlModels: () => request('/ml/train', { method: 'POST' }),

  // Phase 7 Intelligent Hospital Resource Allocation and Optimization
  runAppointmentOptimization: (data) => request('/optimization/appointments/run', { method: 'POST', body: JSON.stringify(data) }),
  runDoctorScheduling: (data) => request('/optimization/doctors/run', { method: 'POST', body: JSON.stringify(data) }),
  runBedAllocation: (data) => request('/optimization/beds/run', { method: 'POST', body: JSON.stringify(data) }),
  getOptimizationRuns: (type, status, limit = 50) => {
    let url = `/optimization/results?limit=${limit}`;
    if (type) url += `&optimization_type=${encodeURIComponent(type)}`;
    if (status) url += `&approval_status=${encodeURIComponent(status)}`;
    return request(url);
  },
  getOptimizationRunById: (id) => request(`/optimization/results/${id}`),
  approveOptimizationRun: (id, notes) => request(`/optimization/results/${id}/approve`, { method: 'POST', body: JSON.stringify({ notes }) }),
  rejectOptimizationRun: (id, reason) => request(`/optimization/results/${id}/reject`, { method: 'POST', body: JSON.stringify({ reason }) }),
  reoptimizeRun: (id, adjustedParams) => request(`/optimization/results/${id}/reoptimize`, { method: 'POST', body: JSON.stringify({ adjusted_parameters: adjustedParams }) }),
  getOptimizationMetrics: () => request('/optimization/metrics'),

  // Phase 8 MCP External Integrations & FHIR Interoperability
  getMcpServers: () => request('/integrations/mcp/servers'),
  connectMcpServer: (serverId) => request('/integrations/mcp/servers/connect', { method: 'POST', body: JSON.stringify({ server_id: serverId }) }),
  disconnectMcpServer: (serverId) => request('/integrations/mcp/servers/disconnect', { method: 'POST', body: JSON.stringify({ server_id: serverId }) }),
  getMcpTools: (serverId) => request(serverId ? `/integrations/mcp/servers/${encodeURIComponent(serverId)}/tools` : '/integrations/mcp/tools'),
  executeMcpTool: (data) => request('/integrations/mcp/tools/execute', { method: 'POST', body: JSON.stringify(data) }),
  getMcpHealth: () => request('/integrations/mcp/health'),
  getFhirMetadata: () => request('/integrations/fhir/metadata'),
  exportFhirPatient: (patientId, validateOnly = false) => request('/integrations/fhir/patient/export', { method: 'POST', body: JSON.stringify({ entity_id: patientId, validate_only: validateOnly }) }),
  exportFhirAppointment: (appointmentId, validateOnly = false) => request('/integrations/fhir/appointment/export', { method: 'POST', body: JSON.stringify({ entity_id: appointmentId, validate_only: validateOnly }) }),
  getIntegrationAuditLogs: (limit = 50) => request(`/integrations/audit?limit=${limit}`),
};
