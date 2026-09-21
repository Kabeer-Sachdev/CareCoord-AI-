const API_BASE_URL = '/api';

async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const config = {
    headers: {
      'Content-Type': 'application/json',
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
  // Dashboard & Workflow
  getDashboardSummary: () => request('/dashboard/summary'),
  sendWorkflowRequest: (message) => request('/workflow/request', {
    method: 'POST',
    body: JSON.stringify({ message }),
  }),

  // Phase 3 Stateful LangGraph Workflows
  getWorkflows: () => request('/workflows'),
  getWorkflowById: (id) => request(`/workflows/${id}`),
  getWorkflowEvents: (id) => request(`/workflows/${id}/events`),
  approveWorkflow: (id, notes) => request(`/workflows/${id}/approve`, {
    method: 'POST',
    body: JSON.stringify({ action: 'approve', notes: notes || 'Approved via Hospital Command Terminal' }),
  }),
  rejectWorkflow: (id, notes) => request(`/workflows/${id}/reject`, {
    method: 'POST',
    body: JSON.stringify({ action: 'reject', notes: notes || 'Rejected via Hospital Command Terminal' }),
  }),

  // Patients
  getPatients: () => request('/patients'),
  getPatientById: (id) => request(`/patients/${id}`),

  // Doctors
  getDoctors: () => request('/doctors'),
  getAvailableDoctors: () => request('/doctors/available'),
  getDoctorsBySpecialization: (spec) => request(`/doctors/specialization/${encodeURIComponent(spec)}`),

  // Appointments
  getAppointments: () => request('/appointments'),
  getDoctorAppointments: (doctorId) => request(`/appointments/doctor/${doctorId}`),
  getPatientAppointments: (patientId) => request(`/appointments/patient/${patientId}`),

  // Beds
  getBeds: () => request('/beds'),
  getAvailableBeds: () => request('/beds/available'),

  // Emergencies
  getEmergencies: () => request('/emergencies'),
};
