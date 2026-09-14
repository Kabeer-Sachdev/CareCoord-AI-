import React from 'react';
import { Terminal, CheckCircle2, Clock, AlertTriangle } from 'lucide-react';

export function ActivityTimeline({ steps = [], agentUsed, status, requestText }) {
  return (
    <div className="bg-dark-800 border border-dark-700/80 rounded-xl p-5 shadow-lg">
      <div className="flex items-center justify-between pb-4 mb-4 border-b border-dark-700">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-cyan-400" />
          <h3 className="font-bold text-sm text-white">Live AI Activity Log</h3>
        </div>
        {agentUsed && (
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
            {agentUsed}
          </span>
        )}
      </div>

      {requestText && (
        <div className="mb-4 p-3 bg-dark-900 rounded-lg border border-dark-700 font-mono text-xs text-gray-300">
          <span className="text-gray-500">RAW QUERY &gt;</span> "{requestText}"
        </div>
      )}

      {steps.length === 0 ? (
        <div className="py-8 text-center text-xs font-mono text-gray-500">
          No workflow events processed yet. Submit a query in the Workflow Terminal to stream live agent steps.
        </div>
      ) : (
        <div className="space-y-3 font-mono text-xs">
          {steps.map((step, idx) => (
            <div key={idx} className="flex items-start gap-3 text-gray-300">
              <div className="mt-0.5 text-cyan-400">
                {status === 'error' && idx === steps.length - 1 ? (
                  <AlertTriangle className="w-4 h-4 text-rose-400" />
                ) : (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                )}
              </div>
              <div className="flex-1">
                <span className="text-gray-500 text-[10px] mr-2">Step {idx + 1}:</span>
                <span>{step}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
