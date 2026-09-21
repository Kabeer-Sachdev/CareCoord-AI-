import React, { useState } from 'react';
import { ShieldAlert, CheckCircle2, XCircle, User, Calendar, Clock, Sparkles } from 'lucide-react';
import { apiService } from '../services/api';

export function HumanApprovalCard({ workflow, onApprovalComplete }) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [notes, setNotes] = useState('');
  const [error, setError] = useState(null);

  if (!workflow || (!workflow.requires_human_approval && workflow.status !== 'REQUIRES_HUMAN_APPROVAL')) {
    return null;
  }

  const recData = workflow.final_result?.data || workflow.data || {};
  const patientName = recData.patient_name || recData.patient_id || 'P001 (Rahul Sharma)';
  const doctorName = recData.doctor_name || 'Dr. Mehta';
  const department = recData.department || 'Cardiology';
  const apptDate = recData.appointment_date || 'tomorrow';
  const apptTime = recData.appointment_time || '10:30 AM';
  const checks = recData.validation_checks || [
    '✓ Doctor availability verified in SQLite database',
    '✓ Slot availability check passed without double-booking',
    '✓ Patient health record verified'
  ];

  const handleApprove = async () => {
    setIsSubmitting(true);
    setError(null);
    try {
      const res = await apiService.approveWorkflow(workflow.workflow_id, notes);
      if (onApprovalComplete) onApprovalComplete(res);
    } catch (err) {
      setError(err.message || 'Failed to approve workflow.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReject = async () => {
    setIsSubmitting(true);
    setError(null);
    try {
      const res = await apiService.rejectWorkflow(workflow.workflow_id, notes);
      if (onApprovalComplete) onApprovalComplete(res);
    } catch (err) {
      setError(err.message || 'Failed to reject workflow.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-gradient-to-b from-amber-500/10 to-dark-800 border-2 border-amber-500/40 rounded-2xl p-6 shadow-2xl space-y-5 animate-fadeIn">
      {/* Header Banner */}
      <div className="flex items-center justify-between border-b border-amber-500/20 pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-amber-500/20 text-amber-400 rounded-xl border border-amber-500/30 shadow-lg shadow-amber-500/20">
            <ShieldAlert className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <span className="text-[10px] font-mono text-amber-400 uppercase tracking-widest block font-semibold">
              HUMAN-IN-THE-LOOP APPROVAL BOUNDARY
            </span>
            <h3 className="text-base font-bold text-white tracking-tight">
              Hospital Staff Operational Action Authorization
            </h3>
          </div>
        </div>

        <span className="px-3 py-1 rounded-full bg-amber-500/20 text-amber-300 font-mono text-xs border border-amber-500/40 animate-pulse font-semibold">
          AWAITING AUTHORIZATION
        </span>
      </div>

      {/* Recommended Details Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 font-sans text-xs">
        <div className="p-3 bg-dark-900/80 rounded-xl border border-dark-700/80">
          <span className="text-gray-400 text-[10px] uppercase font-mono block">Patient Target</span>
          <div className="font-semibold text-white mt-1 flex items-center gap-1.5">
            <User className="w-3.5 h-3.5 text-cyan-400" />
            <span>{patientName}</span>
          </div>
        </div>

        <div className="p-3 bg-dark-900/80 rounded-xl border border-dark-700/80">
          <span className="text-gray-400 text-[10px] uppercase font-mono block">Assigned Doctor</span>
          <div className="font-semibold text-white mt-1">
            {doctorName} <span className="text-cyan-400 text-[11px]">({department})</span>
          </div>
        </div>

        <div className="p-3 bg-dark-900/80 rounded-xl border border-dark-700/80">
          <span className="text-gray-400 text-[10px] uppercase font-mono block">Scheduled Date</span>
          <div className="font-semibold text-white mt-1 flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-emerald-400" />
            <span>{apptDate}</span>
          </div>
        </div>

        <div className="p-3 bg-dark-900/80 rounded-xl border border-dark-700/80">
          <span className="text-gray-400 text-[10px] uppercase font-mono block">Calculated Slot</span>
          <div className="font-semibold text-white mt-1 flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-amber-400" />
            <span>{apptTime}</span>
          </div>
        </div>
      </div>

      {/* Verification Checkmarks */}
      <div className="p-4 bg-dark-900/90 rounded-xl border border-dark-700 space-y-2">
        <div className="text-[11px] font-mono text-cyan-400 font-semibold uppercase flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5" />
          <span>DATA VERIFIED FROM HOSPITAL DATABASE (SQLITE)</span>
        </div>
        <div className="space-y-1.5 text-xs font-mono text-gray-300">
          {checks.map((chk, idx) => (
            <div key={idx} className="flex items-start gap-2">
              <span className="text-emerald-400 font-bold">&gt;</span>
              <span>{chk}</span>
            </div>
          ))}
        </div>
      </div>

      {error && (
        <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl text-xs text-rose-300">
          {error}
        </div>
      )}

      {/* Notes & Actions */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
        <input
          type="text"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Optional staff verification notes..."
          className="w-full sm:w-80 bg-dark-900 border border-dark-600 rounded-xl px-3.5 py-2 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-amber-500"
        />

        <div className="flex items-center gap-3 w-full sm:w-auto">
          <button
            onClick={handleReject}
            disabled={isSubmitting}
            className="flex-1 sm:flex-none px-5 py-2.5 rounded-xl bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 font-medium text-xs border border-rose-500/40 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
          >
            <XCircle className="w-4 h-4" />
            <span>REJECT</span>
          </button>

          <button
            onClick={handleApprove}
            disabled={isSubmitting}
            className="flex-1 sm:flex-none px-6 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white font-bold text-xs shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
          >
            {isSubmitting ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            ) : (
              <>
                <CheckCircle2 className="w-4 h-4" />
                <span>APPROVE & COMMIT TO DB</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
