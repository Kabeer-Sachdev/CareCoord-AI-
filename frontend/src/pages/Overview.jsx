import React, { useState, useEffect } from 'react';
import { Users, UserCheck, Calendar, BedDouble, Siren, Activity, ArrowUpRight } from 'lucide-react';
import { KpiCard } from '../components/KpiCard';
import { ProgressBar } from '../components/ProgressBar';
import { StatusBadge } from '../components/StatusBadge';
import { ActivityTimeline } from '../components/ActivityTimeline';
import { apiService } from '../services/api';

export function OverviewPage({ onNavigateToWorkflow, lastWorkflowEvent }) {
  const [summary, setSummary] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchSummary = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiService.getDashboardSummary();
      setSummary(data);
    } catch (err) {
      setError(err.message || 'Failed to load hospital operations summary.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-3 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
          <span className="text-xs font-mono text-gray-400">Loading Hospital Ops Data...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-rose-500/10 border border-rose-500/30 rounded-xl text-center max-w-lg mx-auto my-12">
        <h3 className="text-rose-400 font-bold text-base mb-2">Backend Connection Error</h3>
        <p className="text-xs text-gray-300 mb-4">{error}</p>
        <button
          onClick={fetchSummary}
          className="px-4 py-2 bg-rose-500 hover:bg-rose-600 text-white font-medium text-xs rounded-lg transition-colors"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  const kpis = summary?.kpis || {};
  const utilization = summary?.resource_utilization || {};
  const docAvailability = summary?.doctor_availability || [];
  const recentAppts = summary?.recent_appointments || [];
  const activeEmgs = summary?.recent_emergencies || [];

  return (
    <div className="space-y-6">
      {/* Header Greeting */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-dark-800 border border-dark-700/80 p-6 rounded-2xl shadow-xl">
        <div>
          <div className="text-xs font-mono text-cyan-400 uppercase tracking-widest mb-1 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
            HOSPITAL OPERATIONS CENTER
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Real-Time Operations Command</h1>
          <p className="text-xs text-gray-400 mt-1">Live SQLite database metrics & agentic workflow orchestration layer.</p>
        </div>

        <button
          onClick={onNavigateToWorkflow}
          className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-semibold text-xs rounded-xl shadow-lg shadow-cyan-500/20 transition-all duration-200"
        >
          <Activity className="w-4 h-4" />
          <span>Launch AI Terminal</span>
          <ArrowUpRight className="w-4 h-4" />
        </button>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <KpiCard
          title="Total Patients"
          value={kpis.total_patients ?? 0}
          subtitle="Registered in system"
          icon={Users}
          color="cyan"
          statusText="DATABASE VERIFIED"
        />
        <KpiCard
          title="Available Doctors"
          value={`${kpis.available_doctors ?? 0} / ${kpis.total_doctors ?? 0}`}
          subtitle="Currently on duty"
          icon={UserCheck}
          color="emerald"
          statusText="ACTIVE ON SHIFT"
        />
        <KpiCard
          title="Today's Appts"
          value={kpis.today_appointments ?? 0}
          subtitle={`Out of ${kpis.total_appointments ?? 0} total`}
          icon={Calendar}
          color="amber"
          statusText="SCHEDULED TODAY"
        />
        <KpiCard
          title="Available Beds"
          value={`${kpis.available_beds ?? 0} / ${kpis.total_beds ?? 0}`}
          subtitle="All wards & ICUs"
          icon={BedDouble}
          color="cyan"
          statusText="READY FOR ALLOCATION"
        />
        <KpiCard
          title="Active Emergencies"
          value={kpis.active_emergencies ?? 0}
          subtitle="Triage & in-progress"
          icon={Siren}
          color="rose"
          statusText="REQUIRES TRIAGE"
        />
      </div>

      {/* Middle Grid: Resource Utilization & Doctor Availability */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Bed Utilization */}
        <div className="bg-dark-800 border border-dark-700/80 rounded-xl p-5 shadow-lg space-y-4">
          <div className="flex justify-between items-center pb-3 border-b border-dark-700">
            <h3 className="font-bold text-sm text-white">Bed Resource Utilization</h3>
            <span className="text-xs font-mono text-gray-400">SQLite Calculated</span>
          </div>

          <div className="space-y-4">
            <ProgressBar
              label="ICU Wards"
              percentage={utilization.ICU?.percentage ?? 0}
              total={utilization.ICU?.total}
              occupied={utilization.ICU?.occupied}
            />
            <ProgressBar
              label="Emergency Bays"
              percentage={utilization.Emergency?.percentage ?? 0}
              total={utilization.Emergency?.total}
              occupied={utilization.Emergency?.occupied}
            />
            <ProgressBar
              label="General Wards"
              percentage={utilization.General?.percentage ?? 0}
              total={utilization.General?.total}
              occupied={utilization.General?.occupied}
            />
            <ProgressBar
              label="Private Suites"
              percentage={utilization.Private?.percentage ?? 0}
              total={utilization.Private?.total}
              occupied={utilization.Private?.occupied}
            />
          </div>
        </div>

        {/* Doctor Availability by Department */}
        <div className="bg-dark-800 border border-dark-700/80 rounded-xl p-5 shadow-lg space-y-4">
          <div className="flex justify-between items-center pb-3 border-b border-dark-700">
            <h3 className="font-bold text-sm text-white">Doctor Availability by Department</h3>
            <span className="text-xs font-mono text-gray-400">On-Duty Matrix</span>
          </div>

          <div className="space-y-3">
            {docAvailability.map((item, idx) => (
              <div key={idx} className="flex justify-between items-center p-2.5 bg-dark-900/60 rounded-lg border border-dark-700/50 text-xs">
                <span className="font-medium text-gray-200">{item.department}</span>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-cyan-400 font-semibold">{item.available} / {item.total} available</span>
                  <span className={`w-2 h-2 rounded-full ${item.available > 0 ? 'bg-emerald-400' : 'bg-rose-400'}`}></span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom Grid: Recent Appointments, Active Emergencies & AI Stream */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Appointments */}
        <div className="bg-dark-800 border border-dark-700/80 rounded-xl p-5 shadow-lg">
          <div className="flex justify-between items-center pb-3 mb-3 border-b border-dark-700">
            <h3 className="font-bold text-sm text-white">Recent Appointments</h3>
            <span className="text-xs font-mono text-gray-400">Latest 5</span>
          </div>

          <div className="space-y-2.5">
            {recentAppts.map((appt, idx) => (
              <div key={idx} className="p-3 bg-dark-900/60 rounded-lg border border-dark-700/50 flex items-center justify-between text-xs">
                <div>
                  <div className="font-semibold text-white font-mono">{appt.appointment_id} ({appt.department})</div>
                  <div className="text-[11px] text-gray-400">Patient: {appt.patient_id} | Doctor: {appt.doctor_id}</div>
                </div>
                <StatusBadge status={appt.status} />
              </div>
            ))}
          </div>
        </div>

        {/* Active Emergencies */}
        <div className="bg-dark-800 border border-dark-700/80 rounded-xl p-5 shadow-lg">
          <div className="flex justify-between items-center pb-3 mb-3 border-b border-dark-700">
            <h3 className="font-bold text-sm text-white">Active Triage Cases</h3>
            <span className="text-xs font-mono text-gray-400">High Priority</span>
          </div>

          <div className="space-y-2.5">
            {activeEmgs.map((emg, idx) => (
              <div key={idx} className="p-3 bg-dark-900/60 rounded-lg border border-dark-700/50 flex items-center justify-between text-xs">
                <div>
                  <div className="font-semibold text-white font-mono flex items-center gap-2">
                    <span>{emg.emergency_id}</span>
                    <StatusBadge status={emg.priority} />
                  </div>
                  <div className="text-[11px] text-gray-400 mt-1">Req: {emg.required_department} ({emg.required_bed_type})</div>
                </div>
                <StatusBadge status={emg.status} />
              </div>
            ))}
          </div>
        </div>

        {/* AI Activity Timeline Panel */}
        <div>
          <ActivityTimeline
            steps={lastWorkflowEvent?.steps || []}
            agentUsed={lastWorkflowEvent?.agent_used}
            status={lastWorkflowEvent?.status}
            requestText={lastWorkflowEvent?.original_request}
          />
        </div>
      </div>
    </div>
  );
}
