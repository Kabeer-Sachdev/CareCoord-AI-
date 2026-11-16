import React, { useState, useEffect, useCallback } from 'react';
import { 
  Users, 
  Calendar, 
  UserCheck, 
  Clock, 
  Plus, 
  Search, 
  Terminal, 
  Check, 
  X, 
  RefreshCw,
  Send,
  AlertTriangle,
  Sparkles
} from 'lucide-react';
import { apiService } from '../services/api';
import { wsClient } from '../services/websocket';

export function ReceptionPortal() {
  const [patients, setPatients] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [workflows, setWorkflows] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);

  // Quick Registration Modal State
  const [showRegModal, setShowRegModal] = useState(false);
  const [newPatient, setNewPatient] = useState({
    name: '',
    age: '',
    gender: 'Male',
    phone: '',
    department: 'Cardiology',
    blood_group: 'O+',
    existing_conditions: ''
  });
  const [regLoading, setRegLoading] = useState(false);
  const [regMessage, setRegMessage] = useState('');

  // Natural Language Workflow State
  const [workflowQuery, setWorkflowQuery] = useState('');
  const [workflowRunning, setWorkflowRunning] = useState(false);
  const [workflowResult, setWorkflowResult] = useState(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [pts, appts, docs, wfs] = await Promise.all([
        apiService.getPatients().catch(() => []),
        apiService.getAppointments().catch(() => []),
        apiService.getDoctors().catch(() => []),
        apiService.getWorkflows().catch(() => [])
      ]);
      setPatients(Array.isArray(pts) ? pts : []);
      setAppointments(Array.isArray(appts) ? appts : []);
      setDoctors(Array.isArray(docs) ? docs : []);
      setWorkflows(Array.isArray(wfs) ? wfs : []);
    } catch (err) {
      console.error('Failed to load reception data', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();

    const unsubApptCreated = wsClient.on('APPOINTMENT_CREATED', () => loadData());
    const unsubApptUpdated = wsClient.on('APPOINTMENT_UPDATED', () => loadData());
    const unsubDoctorStatus = wsClient.on('DOCTOR_STATUS_CHANGED', () => loadData());
    const unsubWfStatus = wsClient.on('WORKFLOW_STATUS_CHANGED', () => loadData());

    return () => {
      unsubApptCreated();
      unsubApptUpdated();
      unsubDoctorStatus();
      unsubWfStatus();
    };
  }, [loadData]);

  const handleRegisterPatient = async (e) => {
    e.preventDefault();
    setRegLoading(true);
    setRegMessage('');
    try {
      const payload = {
        name: newPatient.name,
        age: parseInt(newPatient.age, 10),
        gender: newPatient.gender,
        phone: newPatient.phone,
        department: newPatient.department,
        blood_group: newPatient.blood_group,
        existing_conditions: newPatient.existing_conditions
          ? newPatient.existing_conditions.split(',').map(s => s.trim()).filter(Boolean)
          : []
      };
      await apiService.createPatient(payload);
      setRegMessage('✓ Patient successfully registered!');
      setShowRegModal(false);
      setNewPatient({
        name: '',
        age: '',
        gender: 'Male',
        phone: '',
        department: 'Cardiology',
        blood_group: 'O+',
        existing_conditions: ''
      });
      await loadData();
    } catch (err) {
      setRegMessage(`Registration failed: ${err.message}`);
    } finally {
      setRegLoading(false);
    }
  };

  const handleAppointmentStatus = async (apptId, status) => {
    try {
      await apiService.updateAppointmentStatus(apptId, status, 'Front desk receptionist action');
      await loadData();
    } catch (err) {
      alert(err.message || 'Status update failed');
    }
  };

  const handleExecuteWorkflow = async (e) => {
    e.preventDefault();
    if (!workflowQuery.trim()) return;
    setWorkflowRunning(true);
    setWorkflowResult(null);
    try {
      const res = await apiService.sendWorkflowRequest(workflowQuery.trim());
      setWorkflowResult(res);
      setWorkflowQuery('');
      await loadData();
    } catch (err) {
      setWorkflowResult({ error: err.message });
    } finally {
      setWorkflowRunning(false);
    }
  };

  const handleApproveWorkflow = async (wfId) => {
    try {
      await apiService.approveWorkflow(wfId, 'Approved by Front Desk Receptionist');
      await loadData();
    } catch (err) {
      alert(err.message || 'Approval failed');
    }
  };

  const handleRejectWorkflow = async (wfId) => {
    try {
      await apiService.rejectWorkflow(wfId, 'Rejected by Front Desk Receptionist');
      await loadData();
    } catch (err) {
      alert(err.message || 'Rejection failed');
    }
  };

  // Filtered Patients
  const filteredPatients = patients.filter(p => 
    p.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.patient_id?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.department?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const pendingWorkflows = workflows.filter(w => w.requires_human_approval && w.status === 'REQUIRES_HUMAN_APPROVAL');
  const availableDocs = doctors.filter(d => d.availability);

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-dark-800 border border-dark-700/80 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <span>Reception & Patient Services Desk</span>
            <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-purple-500/10 text-purple-400 border border-purple-500/20">
              DESK-01
            </span>
          </h1>
          <p className="text-xs text-gray-400 mt-1">Patient intake, scheduling desk, and natural-language workflow orchestration</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowRegModal(true)}
            className="px-3.5 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-semibold rounded-lg flex items-center gap-1.5 shadow-md shadow-purple-600/20 transition-all"
          >
            <Plus className="w-4 h-4" />
            <span>Register Patient</span>
          </button>
          <button
            onClick={loadData}
            className="p-2 bg-dark-700 hover:bg-dark-600 rounded-lg text-gray-300 border border-dark-600 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-purple-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-dark-800 border border-dark-700/80 rounded-xl p-4">
          <div className="flex items-center justify-between text-gray-400 text-xs">
            <span>Registered Patients</span>
            <Users className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold text-white mt-2">{patients.length}</div>
          <div className="text-[10px] text-gray-500 mt-1 font-mono">Active hospital records</div>
        </div>

        <div className="bg-dark-800 border border-dark-700/80 rounded-xl p-4">
          <div className="flex items-center justify-between text-gray-400 text-xs">
            <span>Total Appointments</span>
            <Calendar className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-white mt-2">{appointments.length}</div>
          <div className="text-[10px] text-gray-500 mt-1 font-mono">All scheduled bookings</div>
        </div>

        <div className="bg-dark-800 border border-dark-700/80 rounded-xl p-4">
          <div className="flex items-center justify-between text-gray-400 text-xs">
            <span>Available Doctors</span>
            <UserCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-white mt-2">{availableDocs.length} / {doctors.length}</div>
          <div className="text-[10px] text-gray-500 mt-1 font-mono">Ready for bookings</div>
        </div>

        <div className="bg-dark-800 border border-dark-700/80 rounded-xl p-4">
          <div className="flex items-center justify-between text-gray-400 text-xs">
            <span>Pending Approvals</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-white mt-2">{pendingWorkflows.length}</div>
          <div className="text-[10px] text-gray-500 mt-1 font-mono">AI recommendations</div>
        </div>
      </div>

      {/* Pending Human Approval Workflows */}
      {pendingWorkflows.length > 0 && (
        <div className="bg-dark-800 border border-amber-500/30 rounded-2xl p-5 shadow-xl">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2 text-amber-400 font-semibold text-sm">
              <AlertTriangle className="w-4 h-4" />
              <span>Pending Human Staff Approvals ({pendingWorkflows.length})</span>
            </div>
            <span className="text-[11px] text-gray-400 font-mono">Requires Human-in-the-Loop Sign-off</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {pendingWorkflows.map(wf => (
              <div key={wf.workflow_id} className="bg-dark-900 border border-dark-700 rounded-xl p-4 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between font-mono text-xs text-gray-400 mb-1">
                    <span className="text-cyan-400 font-semibold">{wf.workflow_id}</span>
                    <span>{wf.workflow_type}</span>
                  </div>
                  <p className="text-xs text-white mb-2 font-medium">"{wf.original_request}"</p>
                  <div className="p-2.5 bg-dark-800 rounded-lg text-xs text-gray-300 border border-dark-700 mb-3">
                    {wf.recommendation}
                  </div>
                </div>
                <div className="flex items-center justify-end gap-2 pt-2 border-t border-dark-700/60">
                  <button
                    onClick={() => handleRejectWorkflow(wf.workflow_id)}
                    className="px-3 py-1.5 bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400 rounded-lg text-xs flex items-center gap-1 font-medium"
                  >
                    <X className="w-3.5 h-3.5" />
                    <span>Reject</span>
                  </button>
                  <button
                    onClick={() => handleApproveWorkflow(wf.workflow_id)}
                    className="px-3 py-1.5 bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/40 text-emerald-400 rounded-lg text-xs flex items-center gap-1 font-medium"
                  >
                    <Check className="w-3.5 h-3.5" />
                    <span>Approve & Book</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Natural Language Workflow Input */}
      <div className="bg-dark-800 border border-dark-700/80 rounded-2xl p-5 shadow-xl">
        <h2 className="text-sm font-bold text-white mb-1 flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-purple-400" />
          <span>Reception AI Workflow Assistant</span>
        </h2>
        <p className="text-xs text-gray-400 mb-3">Execute operational workflows using natural language (e.g. "Book appointment for Rahul Sharma with Dr. Mehta tomorrow morning")</p>

        <form onSubmit={handleExecuteWorkflow} className="flex gap-2">
          <input
            type="text"
            value={workflowQuery}
            onChange={(e) => setWorkflowQuery(e.target.value)}
            placeholder="Type your workflow request..."
            className="flex-1 px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-xs text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
          />
          <button
            type="submit"
            disabled={workflowRunning || !workflowQuery.trim()}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all"
          >
            {workflowRunning ? (
              <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
            ) : (
              <>
                <Send className="w-3.5 h-3.5" />
                <span>Dispatch</span>
              </>
            )}
          </button>
        </form>

        {workflowResult && (
          <div className="mt-3 p-3 bg-dark-900 border border-purple-500/30 rounded-xl text-xs">
            <div className="flex items-center justify-between text-[11px] font-mono text-purple-400 mb-1">
              <span>Workflow: {workflowResult.workflow_id || 'Instant Dispatch'}</span>
              <span>Agent: {workflowResult.agent_used || 'Coordinator Agent'}</span>
            </div>
            <p className="text-gray-200 mt-1">{workflowResult.recommendation || workflowResult.error}</p>
          </div>
        )}
      </div>

      {/* Patient Directory & Search */}
      <div className="bg-dark-800 border border-dark-700/80 rounded-2xl p-6 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <div>
            <h2 className="text-base font-bold text-white tracking-tight">Patient Directory</h2>
            <p className="text-xs text-gray-400">Search and lookup patient history</p>
          </div>
          <div className="relative w-full sm:w-64">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by name, ID or dept..."
              className="w-full pl-9 pr-3 py-1.5 bg-dark-900 border border-dark-600 rounded-lg text-xs text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
            />
          </div>
        </div>

        <div className="overflow-x-auto max-h-80 overflow-y-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-dark-900/60 text-gray-400 border-b border-dark-700 font-mono sticky top-0">
              <tr>
                <th className="py-2.5 px-3">Patient ID</th>
                <th className="py-2.5 px-3">Name</th>
                <th className="py-2.5 px-3">Age / Gender</th>
                <th className="py-2.5 px-3">Department</th>
                <th className="py-2.5 px-3">Blood Group</th>
                <th className="py-2.5 px-3">Phone</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-dark-700/50">
              {filteredPatients.map(p => (
                <tr key={p.patient_id} className="hover:bg-dark-700/30">
                  <td className="py-2.5 px-3 font-mono text-purple-400 font-semibold">{p.patient_id}</td>
                  <td className="py-2.5 px-3 text-white font-medium">{p.name}</td>
                  <td className="py-2.5 px-3 text-gray-300">{p.age}y • {p.gender}</td>
                  <td className="py-2.5 px-3 text-gray-300">{p.department}</td>
                  <td className="py-2.5 px-3 text-gray-400 font-mono">{p.blood_group}</td>
                  <td className="py-2.5 px-3 text-gray-400 font-mono">{p.phone}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Registration Modal */}
      {showRegModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-dark-800 border border-dark-700 rounded-2xl p-6 max-w-md w-full shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-white">Register New Patient</h3>
              <button onClick={() => setShowRegModal(false)} className="text-gray-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleRegisterPatient} className="space-y-3 text-xs">
              <div>
                <label className="block text-gray-300 mb-1 font-medium">Full Name</label>
                <input
                  type="text"
                  required
                  value={newPatient.name}
                  onChange={(e) => setNewPatient({ ...newPatient, name: e.target.value })}
                  placeholder="e.g. Ananya Sen"
                  className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-gray-300 mb-1 font-medium">Age</label>
                  <input
                    type="number"
                    required
                    min="1"
                    max="120"
                    value={newPatient.age}
                    onChange={(e) => setNewPatient({ ...newPatient, age: e.target.value })}
                    className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-white"
                  />
                </div>
                <div>
                  <label className="block text-gray-300 mb-1 font-medium">Gender</label>
                  <select
                    value={newPatient.gender}
                    onChange={(e) => setNewPatient({ ...newPatient, gender: e.target.value })}
                    className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-white"
                  >
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-gray-300 mb-1 font-medium">Department</label>
                  <select
                    value={newPatient.department}
                    onChange={(e) => setNewPatient({ ...newPatient, department: e.target.value })}
                    className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-white"
                  >
                    <option value="Cardiology">Cardiology</option>
                    <option value="Neurology">Neurology</option>
                    <option value="Orthopedics">Orthopedics</option>
                    <option value="General Medicine">General Medicine</option>
                    <option value="Pediatrics">Pediatrics</option>
                  </select>
                </div>
                <div>
                  <label className="block text-gray-300 mb-1 font-medium">Blood Group</label>
                  <select
                    value={newPatient.blood_group}
                    onChange={(e) => setNewPatient({ ...newPatient, blood_group: e.target.value })}
                    className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-white"
                  >
                    {['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'].map(b => (
                      <option key={b} value={b}>{b}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-gray-300 mb-1 font-medium">Phone</label>
                <input
                  type="text"
                  required
                  value={newPatient.phone}
                  onChange={(e) => setNewPatient({ ...newPatient, phone: e.target.value })}
                  placeholder="+91 98765 43210"
                  className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-white"
                />
              </div>

              <div>
                <label className="block text-gray-300 mb-1 font-medium">Existing Conditions (comma-separated)</label>
                <input
                  type="text"
                  value={newPatient.existing_conditions}
                  onChange={(e) => setNewPatient({ ...newPatient, existing_conditions: e.target.value })}
                  placeholder="e.g. Hypertension, Type 2 Diabetes"
                  className="w-full px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-white"
                />
              </div>

              <div className="pt-3 flex gap-2 justify-end">
                <button
                  type="button"
                  onClick={() => setShowRegModal(false)}
                  className="px-3 py-2 bg-dark-700 hover:bg-dark-600 text-gray-300 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={regLoading}
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white font-semibold rounded-lg"
                >
                  {regLoading ? 'Saving...' : 'Register'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}