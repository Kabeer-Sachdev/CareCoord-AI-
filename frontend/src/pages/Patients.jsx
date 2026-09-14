import React, { useState, useEffect } from 'react';
import { Users, Eye, X } from 'lucide-react';
import { DataTable } from '../components/DataTable';
import { apiService } from '../services/api';

export function PatientsPage() {
  const [patients, setPatients] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedPatient, setSelectedPatient] = useState(null);

  useEffect(() => {
    async function loadPatients() {
      setIsLoading(true);
      try {
        const data = await apiService.getPatients();
        setPatients(data);
      } catch (err) {
        console.error("Failed to load patients:", err);
      } finally {
        setIsLoading(false);
      }
    }
    loadPatients();
  }, []);

  const columns = [
    {
      header: 'ID',
      accessor: 'patient_id',
      render: (row) => <span className="font-mono text-cyan-400 font-semibold">{row.patient_id}</span>
    },
    { header: 'Name', accessor: 'name' },
    { header: 'Age', accessor: 'age', render: (row) => `${row.age} yrs` },
    { header: 'Gender', accessor: 'gender' },
    { header: 'Department', accessor: 'department' },
    { 
      header: 'Blood Group', 
      accessor: 'blood_group',
      render: (row) => <span className="px-2 py-0.5 rounded bg-dark-700 font-mono text-xs border border-dark-600">{row.blood_group}</span>
    },
    { header: 'Phone', accessor: 'phone', render: (row) => <span className="font-mono text-gray-400">{row.phone}</span> },
    {
      header: 'Actions',
      render: (row) => (
        <button
          onClick={() => setSelectedPatient(row)}
          className="px-2.5 py-1 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/20 rounded-lg font-medium text-xs flex items-center gap-1 transition-colors"
        >
          <Eye className="w-3.5 h-3.5" />
          <span>Details</span>
        </button>
      )
    }
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center bg-dark-800 border border-dark-700/80 p-6 rounded-2xl shadow-xl">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Users className="w-5 h-5 text-cyan-400" />
            <span>Patient Registry</span>
          </h1>
          <p className="text-xs text-gray-400 mt-1">Live patient directory synced directly with SQLite backend database.</p>
        </div>
      </div>

      <DataTable
        columns={columns}
        data={patients}
        isLoading={isLoading}
        searchPlaceholder="Search patients by name, ID, or department..."
        emptyMessage="No patient records found in SQLite database."
      />

      {/* Patient Detail Modal */}
      {selectedPatient && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-dark-800 border border-dark-700 rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4 relative">
            <button
              onClick={() => setSelectedPatient(null)}
              className="absolute top-4 right-4 p-1 rounded-lg bg-dark-700 text-gray-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-3 pb-3 border-b border-dark-700">
              <div className="p-3 bg-cyan-500/10 text-cyan-400 rounded-xl border border-cyan-500/20 font-mono font-bold">
                {selectedPatient.patient_id}
              </div>
              <div>
                <h3 className="font-bold text-lg text-white">{selectedPatient.name}</h3>
                <p className="text-xs text-gray-400 font-mono">Registered: {new Date(selectedPatient.created_at).toLocaleDateString()}</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 bg-dark-900 rounded-lg border border-dark-700">
                <span className="text-gray-500 block text-[10px]">AGE / GENDER</span>
                <span className="font-semibold text-white">{selectedPatient.age} yrs / {selectedPatient.gender}</span>
              </div>
              <div className="p-3 bg-dark-900 rounded-lg border border-dark-700">
                <span className="text-gray-500 block text-[10px]">BLOOD GROUP</span>
                <span className="font-semibold text-cyan-400 font-mono">{selectedPatient.blood_group}</span>
              </div>
              <div className="p-3 bg-dark-900 rounded-lg border border-dark-700">
                <span className="text-gray-500 block text-[10px]">PRIMARY DEPARTMENT</span>
                <span className="font-semibold text-white">{selectedPatient.department}</span>
              </div>
              <div className="p-3 bg-dark-900 rounded-lg border border-dark-700">
                <span className="text-gray-500 block text-[10px]">PHONE</span>
                <span className="font-semibold text-gray-300 font-mono">{selectedPatient.phone}</span>
              </div>
            </div>

            <div>
              <span className="text-xs text-gray-400 font-semibold block mb-2">EXISTING CONDITIONS</span>
              {selectedPatient.existing_conditions && selectedPatient.existing_conditions.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {selectedPatient.existing_conditions.map((cond, idx) => (
                    <span key={idx} className="px-2.5 py-1 rounded-md bg-amber-500/10 text-amber-300 border border-amber-500/20 text-xs">
                      {cond}
                    </span>
                  ))}
                </div>
              ) : (
                <span className="text-xs text-gray-500 font-mono">No prior medical conditions recorded.</span>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
