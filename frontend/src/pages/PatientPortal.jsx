import React, { useState, useEffect, useCallback } from 'react';
import { 
  User, 
  Calendar, 
  Clock, 
  Stethoscope, 
  AlertCircle, 
  CheckCircle2, 
  X, 
  RefreshCw,
  Send,
  HeartPulse,
  Bell
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { apiService } from '../services/api';
import { wsClient } from '../services/websocket';

export function PatientPortal() {
  const { user } = useAuth();
  const patientId = user?.patient_id || 'P001';

  const [profile, setProfile] = useState(null);
  const [appointments, setAppointments] = useState([]);
  const [availableDocs, setAvailableDocs] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);

  // AI Booking request
  const [requestQuery, setRequestQuery] = useState('');
  const [requestRunning, setRequestRunning] = useState(false);
  const [requestResult, setRequestResult] = useState(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [pat, appts, docs, notifs] = await Promise.all([
        apiService.getPatientById(patientId).catch(() => null),
        apiService.getPatientAppointments(patientId).catch(() => []),
        apiService.getAvailableDoctors().catch(() => []),
        apiService.getNotifications().catch(() => [])
      ]);
      setProfile(pat);
      setAppointments(Array.isArray(appts) ? appts : []);
      setAvailableDocs(Array.isArray(docs) ? docs : []);
      setNotifications(Array.isArray(notifs) ? notifs : (notifs?.notifications || []));
    } catch (err) {
      console.error('Failed to load patient portal data', err);
    } finally {
      setLoading(false);
    }
  }, [patientId]);

  useEffect(() => {
    loadData();

    const unsubApptCreated = wsClient.on('APPOINTMENT_CREATED', () => loadData());
    const unsubApptUpdated = wsClient.on('APPOINTMENT_UPDATED', () => loadData());
    const unsubApptCancelled = wsClient.on('APPOINTMENT_CANCELLED', () => loadData());
    const unsubNotif = wsClient.on('NOTIFICATION_CREATED', () => loadData());

    return () => {
      unsubApptCreated();
      unsubApptUpdated();
      unsubApptCancelled();
      unsubNotif();
    };
  }, [loadData]);

  const handleCancelAppointment = async (apptId) => {
    if (!window.confirm('Are you sure you want to cancel this appointment?')) return;
    try {
      await apiService.updateAppointmentStatus(apptId, 'cancelled', 'Cancelled by patient');
      await loadData();
    } catch (err) {
      alert(err.message || 'Failed to cancel appointment');
    }
  };

  const handleSendRequest = async (e) => {
    e.preventDefault();
    if (!requestQuery.trim()) return;
    setRequestRunning(true);
    setRequestResult(null);
    try {
      const res = await apiService.sendWorkflowRequest(requestQuery.trim());
      setRequestResult(res);
      setRequestQuery('');
      await loadData();
    } catch (err) {
      setRequestResult({ error: err.message });
    } finally {
      setRequestRunning(false);
    }
  };

  const handleMarkNotification = async (notifId) => {
    try {
      await apiService.markNotificationRead(notifId);
      await loadData();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Patient Profile Card */}
      <div className="bg-dark-800 border border-dark-700/80 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-gradient-to-tr from-blue-500 to-cyan-600 rounded-xl text-white shadow-lg shadow-blue-500/20">
            <User className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-white tracking-tight">
                {profile?.name || user?.full_name || 'Rahul Sharma'}
              </h1>
              <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-blue-500/10 text-blue-400 border border-blue-500/20">
                {patientId}
              </span>
            </div>
            <p className="text-xs text-gray-400 mt-0.5">
              {profile?.age || 32} Years • {profile?.gender || 'Male'} • Blood Group: <span className="font-mono text-cyan-400 font-semibold">{profile?.blood_group || 'O+'}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {profile?.existing_conditions && profile.existing_conditions.length > 0 ? (
            <div className="flex flex-wrap gap-1.5">
              {profile.existing_conditions.map((c, i) => (
                <span key={i} className="px-2.5 py-1 rounded-full text-[10px] font-mono bg-red-950/60 text-red-300 border border-red-800/80">
                  {c}
                </span>
              ))}
            </div>
          ) : (
            <span className="text-xs text-gray-500 font-mono">No chronic conditions listed</span>
          )}
          <button
            onClick={loadData}
            className="p-2 bg-dark-700 hover:bg-dark-600 rounded-lg text-gray-300 border border-dark-600 transition-colors ml-2"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-blue-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* Request Appointment Assistant */}
      <div className="bg-dark-800 border border-dark-700/80 rounded-2xl p-5 shadow-xl">
        <h2 className="text-sm font-bold text-white mb-1 flex items-center gap-2">
          <HeartPulse className="w-4 h-4 text-cyan-400" />
          <span>Book an Appointment via AI Assistant</span>
        </h2>
        <p className="text-xs text-gray-400 mb-3">
          Type your requirement naturally (e.g. "I need an appointment with a cardiologist tomorrow morning")
        </p>

        <form onSubmit={handleSendRequest} className="flex gap-2">
          <input
            type="text"
            value={requestQuery}
            onChange={(e) => setRequestQuery(e.target.value)}
            placeholder="Type your request here..."
            className="flex-1 px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-xs text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
          />
          <button
            type="submit"
            disabled={requestRunning || !requestQuery.trim()}
            className="px-4 py-2 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all"
          >
            {requestRunning ? (
              <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
            ) : (
              <>
                <Send className="w-3.5 h-3.5" />
                <span>Request</span>
              </>
            )}
          </button>
        </form>

        {requestResult && (
          <div className="mt-3 p-3.5 bg-dark-900 border border-cyan-500/30 rounded-xl text-xs">
            <div className="flex items-center justify-between text-[11px] font-mono text-cyan-400 mb-1">
              <span>Recommendation Plan</span>
              <span>{requestResult.status}</span>
            </div>
            <p className="text-gray-200">{requestResult.recommendation || requestResult.error}</p>
            {requestResult.requires_human_approval && (
              <div className="mt-2 text-[11px] text-amber-400 font-mono flex items-center gap-1.5">
                <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                <span>Pending hospital receptionist confirmation. You will be notified once booked.</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* My Appointments */}
      <div className="bg-dark-800 border border-dark-700/80 rounded-2xl p-6 shadow-xl">
        <h2 className="text-base font-bold text-white tracking-tight mb-1 flex items-center gap-2">
          <Calendar className="w-4 h-4 text-cyan-400" />
          <span>My Scheduled Appointments ({appointments.length})</span>
        </h2>
        <p className="text-xs text-gray-400 mb-4">View your booking history and manage upcoming consultations</p>

        {appointments.length === 0 ? (
          <div className="py-10 text-center text-gray-500 text-xs">
            You have no appointments currently scheduled.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-dark-900/60 text-gray-400 border-b border-dark-700 font-mono">
                <tr>
                  <th className="py-2.5 px-3">Appt ID</th>
                  <th className="py-2.5 px-3">Doctor</th>
                  <th className="py-2.5 px-3">Date & Time</th>
                  <th className="py-2.5 px-3">Department</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">Reason</th>
                  <th className="py-2.5 px-3 text-right">Action</th>
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
                      <td className="py-3 px-3 font-mono text-cyan-400 font-semibold">{a.appointment_id}</td>
                      <td className="py-3 px-3 text-white font-medium">{a.doctor_id}</td>
                      <td className="py-3 px-3 text-gray-300">{a.appointment_date} at {a.appointment_time}</td>
                      <td className="py-3 px-3 text-gray-300">{a.department}</td>
                      <td className="py-3 px-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-mono border ${statusColors[a.status] || 'bg-gray-800 text-gray-400'}`}>
                          {a.status}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-gray-400 max-w-xs truncate">{a.reason || 'General checkup'}</td>
                      <td className="py-3 px-3 text-right">
                        {a.status !== 'cancelled' && a.status !== 'completed' && (
                          <button
                            onClick={() => handleCancelAppointment(a.appointment_id)}
                            className="px-2.5 py-1 bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400 rounded text-[11px] font-medium"
                          >
                            Cancel
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

      {/* Available Specialists Reference */}
      <div className="bg-dark-800 border border-dark-700/80 rounded-2xl p-6 shadow-xl">
        <h2 className="text-base font-bold text-white tracking-tight mb-1 flex items-center gap-2">
          <Stethoscope className="w-4 h-4 text-emerald-400" />
          <span>Available Medical Specialists ({availableDocs.length})</span>
        </h2>
        <p className="text-xs text-gray-400 mb-4">Physicians currently on active duty for bookings</p>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
          {availableDocs.map(d => (
            <div key={d.doctor_id} className="p-3 bg-dark-900 border border-dark-700 rounded-xl text-xs">
              <div className="font-semibold text-white">{d.name}</div>
              <div className="text-[11px] text-cyan-400 font-mono">{d.specialization}</div>
              <div className="text-[11px] text-gray-400 mt-1">Shift: {d.shift}</div>
              <div className="text-[10px] text-emerald-400 font-mono mt-2">● Currently Available</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}