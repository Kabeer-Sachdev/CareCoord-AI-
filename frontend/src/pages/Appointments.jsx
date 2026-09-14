import React, { useState, useEffect } from 'react';
import { Calendar, Filter } from 'lucide-react';
import { DataTable } from '../components/DataTable';
import { StatusBadge } from '../components/StatusBadge';
import { apiService } from '../services/api';

export function AppointmentsPage() {
  const [appointments, setAppointments] = useState([]);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadAppointments() {
      setIsLoading(true);
      try {
        const data = await apiService.getAppointments();
        setAppointments(data);
      } catch (err) {
        console.error("Failed to load appointments:", err);
      } finally {
        setIsLoading(false);
      }
    }
    loadAppointments();
  }, []);

  const filteredAppts = statusFilter === 'ALL'
    ? appointments
    : appointments.filter(a => a.status.toLowerCase() === statusFilter.toLowerCase());

  const columns = [
    {
      header: 'ID',
      accessor: 'appointment_id',
      render: (row) => <span className="font-mono text-cyan-400 font-semibold">{row.appointment_id}</span>
    },
    {
      header: 'Patient ID',
      accessor: 'patient_id',
      render: (row) => <span className="font-mono text-gray-300">{row.patient_id}</span>
    },
    {
      header: 'Doctor ID',
      accessor: 'doctor_id',
      render: (row) => <span className="font-mono text-gray-300">{row.doctor_id}</span>
    },
    { header: 'Department', accessor: 'department' },
    { header: 'Date', accessor: 'appointment_date', render: (row) => <span className="font-mono text-gray-400">{row.appointment_date}</span> },
    { header: 'Time', accessor: 'appointment_time', render: (row) => <span className="font-mono text-gray-400">{row.appointment_time}</span> },
    { header: 'Reason', accessor: 'reason', render: (row) => <span className="text-xs text-gray-400 max-w-xs truncate block">{row.reason || 'N/A'}</span> },
    {
      header: 'Status',
      accessor: 'status',
      render: (row) => <StatusBadge status={row.status} />
    }
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-dark-800 border border-dark-700/80 p-6 rounded-2xl shadow-xl">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Calendar className="w-5 h-5 text-amber-400" />
            <span>Hospital Appointments</span>
          </h1>
          <p className="text-xs text-gray-400 mt-1">Live patient consultation schedules & booking status log.</p>
        </div>

        {/* Status Filter buttons */}
        <div className="flex items-center gap-1.5 bg-dark-900 border border-dark-600 rounded-xl p-1 text-xs">
          {['ALL', 'scheduled', 'completed', 'pending', 'cancelled'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1.5 rounded-lg font-medium capitalize transition-all ${
                statusFilter === st 
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30' 
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      <DataTable
        columns={columns}
        data={filteredAppts}
        isLoading={isLoading}
        searchPlaceholder="Search appointments by ID, patient, or department..."
        emptyMessage="No matching appointments found."
      />
    </div>
  );
}
