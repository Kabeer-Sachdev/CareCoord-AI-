import React from 'react';

export function ProgressBar({ label, percentage, total, occupied, color = 'cyan' }) {
  let barColor = 'bg-cyan-500';
  if (percentage >= 80) barColor = 'bg-rose-500';
  else if (percentage >= 50) barColor = 'bg-amber-500';
  else barColor = 'bg-emerald-500';

  return (
    <div className="space-y-1.5">
      <div className="flex justify-between text-xs text-gray-300">
        <span className="font-medium text-gray-200">{label}</span>
        <span className="font-mono text-gray-400">
          {occupied !== undefined && total !== undefined ? `${occupied}/${total} (${percentage}%)` : `${percentage}%`}
        </span>
      </div>
      <div className="w-full h-2 bg-dark-700 rounded-full overflow-hidden p-0.5 border border-dark-600/50">
        <div 
          className={`h-full rounded-full transition-all duration-500 ease-out ${barColor}`} 
          style={{ width: `${Math.min(100, Math.max(0, percentage))}%` }}
        />
      </div>
    </div>
  );
}
