import React from 'react';

export function StatusBadge({ status }) {
  if (!status) return null;

  const s = String(status).toLowerCase();

  let colorClasses = 'bg-gray-800 text-gray-300 border-gray-700';

  if (['scheduled', 'available', 'healthy', 'active', 'completed', 'allocated', 'low'].includes(s)) {
    colorClasses = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
  } else if (['pending', 'waiting', 'being_processed', 'maintenance', 'medium', 'warning', 'urgent', 'clarification_required'].includes(s)) {
    colorClasses = 'bg-amber-500/10 text-amber-400 border-amber-500/20';
  } else if (['occupied', 'cancelled', 'critical', 'high', 'error', 'offline'].includes(s)) {
    colorClasses = 'bg-rose-500/10 text-rose-400 border-rose-500/20';
  } else if (['info', 'planned', 'idle'].includes(s)) {
    colorClasses = 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20';
  }

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${colorClasses}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
      {status.toUpperCase()}
    </span>
  );
}
