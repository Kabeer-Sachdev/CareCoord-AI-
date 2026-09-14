import React from 'react';
import { Bot, Cpu, ArrowRight } from 'lucide-react';
import { StatusBadge } from './StatusBadge';

export function AgentStatusCard({ name, status, description, toolsCount, phase, activeIcon: Icon = Bot }) {
  const isActive = status.toLowerCase() === 'active';

  return (
    <div className={`p-5 rounded-xl border transition-all duration-200 ${
      isActive 
        ? 'bg-dark-800 border-cyan-500/30 shadow-lg shadow-cyan-500/5 hover:border-cyan-500/50' 
        : 'bg-dark-800/60 border-dark-700/60 opacity-80 hover:opacity-100'
    }`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className={`p-2.5 rounded-lg border ${
            isActive ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30' : 'bg-dark-700 text-gray-400 border-dark-600'
          }`}>
            <Icon className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-white text-sm">{name}</h3>
            <span className="text-[10px] font-mono text-gray-400">Target Phase: {phase}</span>
          </div>
        </div>

        <StatusBadge status={status} />
      </div>

      <p className="text-xs text-gray-300 mb-4 leading-relaxed">{description}</p>

      <div className="pt-3 border-t border-dark-700/60 flex items-center justify-between text-[11px] font-mono text-gray-400">
        <span className="flex items-center gap-1.5">
          <Cpu className="w-3.5 h-3.5 text-cyan-400" />
          <span>{toolsCount} Tool Function(s)</span>
        </span>
        <span className="flex items-center gap-1 text-cyan-400">
          <span>Details</span>
          <ArrowRight className="w-3 h-3" />
        </span>
      </div>
    </div>
  );
}
