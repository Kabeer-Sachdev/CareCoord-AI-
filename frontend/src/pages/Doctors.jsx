import React, { useState, useEffect } from 'react';
import { UserCheck, Clock, Briefcase, Filter } from 'lucide-react';
import { StatusBadge } from '../components/StatusBadge';
import { ProgressBar } from '../components/ProgressBar';
import { apiService } from '../services/api';

export function DoctorsPage() {
  const [doctors, setDoctors] = useState([]);
  const [filterSpec, setFilterSpec] = useState('ALL');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadDoctors() {
      setIsLoading(true);
      try {
        const data = await apiService.getDoctors();
        setDoctors(data);
      } catch (err) {
        console.error("Failed to load doctors:", err);
      } finally {
        setIsLoading(false);
      }
    }
    loadDoctors();
  }, []);

  const specializations = ['ALL', ...new Set(doctors.map(d => d.specialization))];

  const filteredDoctors = filterSpec === 'ALL' 
    ? doctors 
    : doctors.filter(d => d.specialization === filterSpec);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-dark-800 border border-dark-700/80 p-6 rounded-2xl shadow-xl">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <UserCheck className="w-5 h-5 text-emerald-400" />
            <span>Doctor Roster & Workload</span>
          </h1>
          <p className="text-xs text-gray-400 mt-1">Live doctor availability matrix, shifts, and active patient load.</p>
        </div>

        {/* Specialization Filter Dropdown */}
        <div className="flex items-center gap-2 bg-dark-900 border border-dark-600 rounded-xl px-3 py-1.5 text-xs text-gray-300">
          <Filter className="w-4 h-4 text-cyan-400" />
          <span className="text-gray-500 font-mono">SPEC:</span>
          <select
            value={filterSpec}
            onChange={(e) => setFilterSpec(e.target.value)}
            className="bg-transparent text-white focus:outline-none cursor-pointer font-medium"
          >
            {specializations.map((spec, idx) => (
              <option key={idx} value={spec} className="bg-dark-800 text-white">{spec}</option>
            ))}
          </select>
        </div>
      </div>

      {isLoading ? (
        <div className="py-12 text-center text-xs font-mono text-gray-400">Loading doctor roster...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredDoctors.map((doc) => {
            const workloadPct = Math.min(100, Math.round((doc.current_patients / 6) * 100));

            return (
              <div key={doc.id} className="bg-dark-800 border border-dark-700/80 rounded-xl p-5 shadow-lg space-y-4 hover:border-dark-600 transition-colors">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-bold text-base text-white">{doc.name}</h3>
                    <span className="text-xs font-mono text-cyan-400">{doc.doctor_id} | {doc.specialization}</span>
                  </div>
                  <StatusBadge status={doc.availability ? 'available' : 'unavailable'} />
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                  <div className="p-2.5 bg-dark-900/60 rounded-lg border border-dark-700/50 flex items-center gap-2 text-gray-300">
                    <Clock className="w-3.5 h-3.5 text-cyan-400" />
                    <span>{doc.shift}</span>
                  </div>
                  <div className="p-2.5 bg-dark-900/60 rounded-lg border border-dark-700/50 flex items-center gap-2 text-gray-300">
                    <Briefcase className="w-3.5 h-3.5 text-amber-400" />
                    <span>{doc.experience_years} Yrs Exp</span>
                  </div>
                </div>

                <ProgressBar
                  label="Current Patient Load"
                  percentage={workloadPct}
                  occupied={doc.current_patients}
                  total={6}
                />
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
