import React, { useState, useEffect, useCallback } from 'react';
import { 
  Stethoscope, 
  Calendar, 
  Clock, 
  CheckCircle2, 
  XCircle, 
  AlertCircle, 
  User, 
  RefreshCw,
  Activity,
  Check,
  X
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { apiService } from '../services/api';
import { wsClient } from '../services/websocket';

export function DoctorPortal() {
  const { user } = useAuth();
  const [appointments, setAppointments] = useState([]);
  const [doctorInfo, setDoctorInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);
  const [currentStatus, setCurrentStatus] = useState('Available');
  const [statusMessage, setStatusMessage] = useState('');

  const doctorId = user?.doctor_id || 'D001';

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [appts, doc] = await Promise.all([
        apiService.getDoctorAppointments(doctorId),
        apiService.getDoctorById(doctorId).catch(() => null)
      ]);
      setAppointments(Array.isArray(appts) ? appts : []);
      if (doc) {
        setDoctorInfo(doc);
        setCurrentStatus(doc.availability_status || (doc.availability ? 'Available' : 'Unavailable'));
      }
    } catch (err) {
      console.error('Failed to load doctor portal data', err);
    } finally {
      setLoading(false);
    }
  }, [doctorId]);

  useEffect(() => {
    loadData();

    // Subscribe to live WebSocket events
    const unsubApptCreated = wsClient.on('APPOINTMENT_CREATED', () => loadData());
    const unsubApptUpdated = wsClient.on('APPOINTMENT_UPDATED', () => loadData());
    const unsubDoctorStatus = wsClient.on('DOCTOR_STATUS_CHANGED', (data) => {
      if (data?.doctor_id === doctorId && data?.availability_status) {
        setCurrentStatus(data.availability_status);
      }
    });

    return () => {
      unsubApptCreated();
      unsubApptUpdated();
      unsubDoctorStatus();
    };
  }, [loadData, doctorId]);

  const handleStatusChange = async (newStatus) => {
    try {
      setCurrentStatus(newStatus);
      await apiService.updateDoctorStatus(doctorId, newStatus);
      setStatusMessage(`Status updated to ${newStatus}`);
      setTimeout(() => setStatusMessage(''), 3000);
    } catch (err) {
      console.error('Status update failed', err);
      setStatusMessage('Failed to update status');
      setTimeout(() => setStatusMessage(''), 3000);
    }
  };

  const handleAppointmentAction = async (apptId, newStatus) => {
    try {
      setActionLoading(apptId);
      await apiService.updateAppointmentStatus(apptId, newStatus, `Updated by Dr. ${user?.full_name || 'Mehta'}`);
      await loadData();
    } catch (err) {
      alert(err.message || 'Action failed');
    } finally {
      setActionLoading(null);
    }
  };

  // KPI Calculations
  const todayStr = new Date().toISOString().split('T')[0];
  const todayAppts = appointments.filter(a => a.appointment_date === todayStr || a.appointment_date === 'tomorrow');
  const pendingAppts = appointments.filter(a => a.status === 'pending');
  const completedAppts = appointments.filter(a => a.status === 'completed');
  const upcomingAppts = appointments.filter(a => a.status === 'scheduled' || a.status === 'confirmed');

  const statusOptions = [
    { label: 'Available', color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' },
    { label: 'Busy', color: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30' },
    { label: 'Unavailable', color: 'bg-red-500/10 text-red-400 border-red-500/30' },
    { label: 'On Leave', color: 'bg-gray-500/10 text-gray-400 border-gray-500/30' }
  ];

  return (
    <div className="space-y-6">
      {/* Header Profile & Status Selector */}
      <div className="bg-dark-800 border border-dark-700/80 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-gradient-to-tr from-emerald-500 to-teal-600 rounded-xl text-white shadow-lg shadow-emerald-500/20">
            <Stethoscope className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-white tracking-tight">
                {doctorInfo?.name || user?.full_name || 'Dr. Mehta'}
              </h1>
              <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                {doctorId}
              </span>
            </div>
            <p className="text-xs text-gray-400 font-mono mt-0.5">
              {doctorInfo?.specialization || 'Cardiology'} • Shift: {doctorInfo?.shift || '09:00-17:00'}
            </p>
          </div>
        </div>

        {/* Status Toggle */}
        <div className="flex flex-col sm:flex-row sm:items-center gap-3">
          <div className="text-xs text-gray-400 font-medium">My Availability:</div>
          <div className="flex flex-wrap gap-1.5">
            {statusOptions.map(opt => {
              const active = currentStatus.toLowerCase() === opt.label.toLowerCase();
              return (
                <button
                  key={opt.label}
                  onClick={() => handleStatusChange(opt.label)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                    active
                      ? `${opt.color} ring-1 ring-white/20 font-semibold shadow-sm`
                      : 'bg-dark-900 border-dark-700 text-gray-400 hover:text-white'
                  }`}
                >
                  {opt.label}
                </button>
              );
            })}
          </div>
          {statusMessage && (
            <span className="text-[11px] font-mono text-cyan-400 animate-pulse">{statusMessage}</span>
          )}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-dark-800 border border-dark-700/80 rounded-xl p-4">
          <div className="flex items-center justify-between text-gray-400 text-xs">
            <span>Today's Sessions</span>
            <Calendar className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-white mt-2">{todayAppts.length}</div>
          <div className="text-[10px] text-gray-500 mt-1 font-mono">Scheduled & pending</div>
        </div>

        <div className="bg-dark-800 border border-dark-700/80 rounded-xl p-4">
          <div className="flex items-center justify-between text-gray-400 text-xs">
            <span>Upcoming</span>
            <Clock className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-white mt-2">{upcomingAppts.length}</div>
          <div className="text-[10px] text-gray-500 mt-1 font-mono">Confirmed bookings</div>
        </div>

        <div className="bg-dark-800 border border-dark-700/80 rounded-xl p-4">
          <div className="flex items-center justify-between text-gray-400 text-xs">
            <span>Pending Approvals</span>
            <AlertCircle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-white mt-2">{pendingAppts.length}</div>
          <div className="text-[10px] text-gray-500 mt-1 font-mono">Requires decision</div>
        </div>

        <div className="bg-dark-800 border border-dark-700/80 rounded-xl p-4">
          <div className="flex items-center justify-between text-gray-400 text-xs">
            <span>Completed</span>
            <CheckCircle2 className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold text-white mt-2">{completedAppts.length}</div>
          <div className="text-[10px] text-gray-500 mt-1 font-mono">Total attended</div>
        </div>
      </div>

      {/* Pending Approval Table */}
      {pendingAppts.length > 0 && (
        <div className="bg-dark-800 border border-amber-500/30 rounded-2xl p-5 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2 text-amber-400 font-semibold text-sm">
              <AlertCircle className="w-4 h-4" />
              <span>Pending Appointment Requests ({pendingAppts.length})</span>
            </div>
            <span className="text-[11px] text-gray-400 font-mono">Requires Doctor Confirmation</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-dark-900/60 text-gray-400 border-b border-dark-700">
                <tr>
                  <th className="py-2.5 px-3 font-mono">Appt ID</th>
                  <th className="py-2.5 px-3">Patient</th>
                  <th className="py-2.5 px-3">Date & Time</th>
                  <th className="py-2.5 px-3">Reason</th>
                  <th className="py-2.5 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-700/50">
                {pendingAppts.map(a => (
                  <tr key={a.appointment_id} className="hover:bg-dark-700/30">
                    <td className="py-3 px-3 font-mono text-cyan-400">{a.appointment_id}</td>
                    <td className="py-3 px-3 text-white font-medium">{a.patient_id}</td>
                    <td className="py-3 px-3 text-gray-300">{a.appointment_date} at {a.appointment_time}</td>
                    <td className="py-3 px-3 text-gray-400 truncate max-w-xs">{a.reason || 'General Consultation'}</td>
                    <td className="py-3 px-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          disabled={actionLoading === a.appointment_id}
                          onClick={() => handleAppointmentAction(a.appointment_id, 'confirmed')}
                          className="px-2.5 py-1 bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/40 text-emerald-400 rounded-lg text-xs flex items-center gap-1"
                        >
                          <Check className="w-3.5 h-3.5" />
                          <span>Accept</span>
                        </button>
                        <button
                          disabled={actionLoading === a.appointment_id}
                          onClick={() => handleAppointmentAction(a.appointment_id, 'rejected')}
                          className="px-2.5 py-1 bg-red-500/20 hover:bg-red-500/30 border border-red-500/40 text-red-400 rounded-lg text-xs flex items-center gap-1"
                        >
                          <X className="w-3.5 h-3.5" />
                          <span>Reject</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Today's Schedule Table */}
      <div className="bg-dark-800 border border-dark-700/80 rounded-2xl p-6 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-bold text-white tracking-tight">Today's Patient Schedule</h2>
            <p className="text-xs text-gray-400">All registered appointments for your current shift</p>
          </div>
          <button
            onClick={loadData}
            className="p-2 bg-dark-700 hover:bg-dark-600 rounded-lg text-gray-300 border border-dark-600 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-cyan-400' : ''}`} />
          </button>
        </div>

        {appointments.length === 0 ? (
          <div className="py-12 text-center text-gray-500 text-xs">
            No appointments scheduled for this doctor.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-dark-900/60 text-gray-400 border-b border-dark-700 font-mono">
                <tr>
                  <th className="py-2.5 px-3">Time</th>
                  <th className="py-2.5 px-3">Appt ID</th>
                  <th className="py-2.5 px-3">Patient</th>
                  <th className="py-2.5 px-3">Department</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">Reason</th>
                  <th className="py-2.5 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-700/50">
                {appointments.map(a => {
                  const statusColors = {
                    confirmed: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
                    scheduled: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
                    completed: 'bg-purple-500/10 text-purple-400 border-purple-500/30',
                    cancelled: 'bg-red-500/10 text-red-400 border-red-500/30',
                    pending: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
                  };
                  return (
                    <tr key={a.appointment_id} className="hover:bg-dark-700/30">
                      <td className="py-3 px-3 font-mono text-cyan-400 font-semibold">{a.appointment_time}</td>
                      <td className="py-3 px-3 font-mono text-gray-400">{a.appointment_id}</td>
                      <td className="py-3 px-3 text-white font-medium">{a.patient_id}</td>
                      <td className="py-3 px-3 text-gray-300">{a.department}</td>
                      <td className="py-3 px-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-mono border ${statusColors[a.status] || 'bg-gray-800 text-gray-400'}`}>
                          {a.status}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-gray-400 max-w-xs truncate">{a.reason || 'Consultation'}</td>
                      <td className="py-3 px-3 text-right">
                        {a.status !== 'completed' && a.status !== 'cancelled' && (
                          <button
                            onClick={() => handleAppointmentAction(a.appointment_id, 'completed')}
                            className="px-2 py-1 bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/30 text-purple-300 rounded text-[11px]"
                          >
                            Mark Done
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}