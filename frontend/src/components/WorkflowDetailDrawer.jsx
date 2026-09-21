import React from 'react';
import { X, Network, Database, Clock, CheckCircle2, ShieldCheck, Terminal } from 'lucide-react';
import { StatusBadge } from './StatusBadge';

export function WorkflowDetailDrawer({ workflow, onClose, onApprovalComplete }) {
  if (!workflow) return null;

  const events = workflow.events || [];
  const rec = workflow.final_result || {};

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm animate-fadeIn">
      <div className="w-full max-w-2xl bg-dark-800 border-l border-dark-700/80 h-full flex flex-col justify-between shadow-2xl overflow-hidden">
        {/* Drawer Header */}
        <div className="p-6 border-b border-dark-700 flex justify-between items-center bg-dark-900/60">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-cyan-500/10 text-cyan-400 rounded-lg border border-cyan-500/20">
              <Network className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-bold text-white text-base tracking-tight">{workflow.workflow_id}</h2>
                <StatusBadge status={workflow.status} />
              </div>
              <p className="text-xs text-gray-400 font-mono mt-0.5">Workflow Execution Audit Drawer</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-dark-700 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Drawer Content */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1 text-xs">
          {/* Query Summary */}
          <div className="p-4 bg-dark-900 rounded-xl border border-dark-700 space-y-1.5">
            <span className="text-[10px] font-mono text-gray-500 uppercase tracking-widest block">ORIGINAL INPUT REQUEST</span>
            <div className="text-sm font-semibold text-white">"{workflow.original_request}"</div>
            <div className="flex items-center gap-4 text-[11px] font-mono text-gray-400 pt-2 border-t border-dark-800">
              <span>Type: <strong className="text-cyan-400">{workflow.workflow_type}</strong></span>
              <span>Primary Agent: <strong className="text-emerald-400">{workflow.agent_used || 'Coordinator Agent'}</strong></span>
              <span>Started: <strong className="text-gray-300">{workflow.started_at?.split('.')[0]}</strong></span>
            </div>
          </div>

          {/* Database Recommendation */}
          {workflow.recommendation && (
            <div className="p-4 bg-cyan-500/10 border border-cyan-500/20 rounded-xl space-y-2">
              <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-widest block flex items-center gap-1.5 font-semibold">
                <Database className="w-3.5 h-3.5" />
                <span>SQLITE DATABASE-BACKED RECOMMENDATION</span>
              </span>
              <p className="text-sm text-white font-medium leading-relaxed">{workflow.recommendation}</p>
            </div>
          )}

          {/* Live Event Execution Timeline */}
          <div className="space-y-3">
            <h3 className="font-mono text-xs text-gray-300 uppercase tracking-wider flex items-center gap-2">
              <Terminal className="w-4 h-4 text-cyan-400" />
              <span>LANGGRAPH EXECUTION EVENT LOG ({events.length} STEPS)</span>
            </h3>

            <div className="space-y-2.5 font-mono">
              {events.length === 0 ? (
                <div className="p-4 bg-dark-900 rounded-xl border border-dark-700 text-gray-500 text-center">
                  No detailed execution logs recorded.
                </div>
              ) : (
                events.map((ev, idx) => (
                  <div key={idx} className="p-3.5 bg-dark-900/80 rounded-xl border border-dark-700/80 space-y-2">
                    <div className="flex justify-between items-center text-[11px]">
                      <div className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
                        <span className="font-bold text-white">{ev.agent_name}</span>
                        <span className="text-gray-500">[{ev.node_name}]</span>
                      </div>
                      <div className="flex items-center gap-2 text-gray-400">
                        <span>{ev.execution_time_ms ? `${ev.execution_time_ms} ms` : '0 ms'}</span>
                        <span className="px-1.5 py-0.5 rounded bg-dark-800 text-[9px] uppercase border border-dark-700 text-emerald-400">
                          {ev.status}
                        </span>
                      </div>
                    </div>

                    <div className="text-gray-300 font-sans text-xs pl-4 border-l-2 border-cyan-500/30">
                      {ev.details?.summary || ev.event_type}
                    </div>

                    {ev.tool_name && (
                      <div className="text-[10px] text-gray-400 bg-dark-950 p-2 rounded-lg border border-dark-800 flex justify-between items-center">
                        <span>Tool Invoked: <code className="text-cyan-300">{ev.tool_name}</code></span>
                        <span>Data Source: <strong className="text-emerald-400">SQLite</strong></span>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Drawer Footer */}
        <div className="p-4 border-t border-dark-700 bg-dark-900/60 flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl bg-dark-700 hover:bg-dark-600 text-white font-medium text-xs transition-colors"
          >
            Close Audit Drawer
          </button>
        </div>
      </div>
    </div>
  );
}
