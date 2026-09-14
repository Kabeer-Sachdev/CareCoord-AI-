import React from 'react';

export function KpiCard({ title, value, subtitle, icon: Icon, color = 'cyan', statusText }) {
  const colorMap = {
    cyan: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20',
    emerald: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
    amber: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
    rose: 'text-rose-400 bg-rose-500/10 border-rose-500/20',
  };

  const badgeStyle = colorMap[color] || colorMap.cyan;

  return (
    <div className="bg-dark-800 border border-dark-700/80 rounded-xl p-5 shadow-lg relative overflow-hidden group hover:border-dark-600 transition-all duration-200">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold tracking-wider text-gray-400 uppercase">{title}</span>
        {Icon && (
          <div className={`p-2.5 rounded-lg border ${badgeStyle}`}>
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>

      <div className="mt-3">
        <div className="text-3xl font-bold font-mono tracking-tight text-white">{value}</div>
        {subtitle && <p className="text-xs text-gray-400 mt-1">{subtitle}</p>}
      </div>

      {statusText && (
        <div className="mt-4 pt-3 border-t border-dark-700/50 flex items-center gap-1.5 text-xs text-gray-400 font-mono">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>{statusText}</span>
        </div>
      )}
    </div>
  );
}
