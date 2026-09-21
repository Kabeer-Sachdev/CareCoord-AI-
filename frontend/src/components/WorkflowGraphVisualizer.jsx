import React from 'react';
import { Network, CheckCircle2, Clock, AlertTriangle, ShieldCheck, UserCheck, Bot, Terminal } from 'lucide-react';

export function WorkflowGraphVisualizer({ currentWorkflow, events = [] }) {
  const executedNodes = new Set(events.map(e => e.node_name));
  const activeNode = currentWorkflow?.agent_used || (events.length > 0 ? events[events.length - 1].agent_name : 'Coordinator Agent');
  const isAwaitingApproval = currentWorkflow?.requires_human_approval || currentWorkflow?.status === 'REQUIRES_HUMAN_APPROVAL';
  const isCompleted = currentWorkflow?.status === 'COMPLETED' || currentWorkflow?.status === 'success';

  const nodes = [
    { id: 'parse_request', label: 'Request Parser', type: 'System', icon: Terminal },
    { id: 'coordinator', label: 'Coordinator Agent', type: 'Orchestrator', icon: Network },
    { id: 'doctor_agent', label: 'Doctor Agent', type: 'Specialized', icon: UserCheck },
    { id: 'appointment_agent', label: 'Appointment Agent', type: 'Specialized', icon: Bot },
    { id: 'validation', label: 'Validation Node', type: 'Safety Boundary', icon: ShieldCheck },
    { id: 'human_review', label: 'Human Review', type: 'Approval', icon: Clock }
  ];

  const getNodeState = (node) => {
    if (!currentWorkflow) return 'IDLE';
    if (node.id === 'human_review') {
      if (isAwaitingApproval) return 'REQUIRES_APPROVAL';
      if (isCompleted) return 'COMPLETED';
      return 'IDLE';
    }
    if (executedNodes.has(node.id)) return 'COMPLETED';
    if (isCompleted) return 'COMPLETED';
    if (activeNode.toLowerCase().includes(node.label.toLowerCase().replace(' agent', ''))) return 'RUNNING';
    return 'IDLE';
  };

  const getStatusStyle = (state) => {
    switch (state) {
      case 'COMPLETED':
        return 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400';
      case 'RUNNING':
        return 'bg-cyan-500/20 border-cyan-500/50 text-cyan-300 animate-pulse shadow-lg shadow-cyan-500/20';
      case 'REQUIRES_APPROVAL':
        return 'bg-amber-500/20 border-amber-500/50 text-amber-300 animate-pulse shadow-lg shadow-amber-500/20';
      case 'FAILED':
        return 'bg-rose-500/10 border-rose-500/30 text-rose-400';
      default:
        return 'bg-dark-900/60 border-dark-700/80 text-gray-500 opacity-70';
    }
  };

  return (
    <div className="bg-dark-800 border border-dark-700/80 rounded-2xl p-6 shadow-xl space-y-5">
      <div className="flex justify-between items-center pb-3 border-b border-dark-700">
        <div className="flex items-center gap-2.5">
          <Network className="w-5 h-5 text-cyan-400" />
          <h2 className="text-sm font-bold text-white tracking-tight uppercase font-mono">
            LangGraph Multi-Agent Workflow Visualizer
          </h2>
        </div>
        <div className="flex items-center gap-2 font-mono text-[11px]">
          <span className="text-gray-400">Workflow ID:</span>
          <span className="px-2 py-0.5 rounded bg-dark-900 text-cyan-400 border border-dark-700 font-semibold">
            {currentWorkflow?.workflow_id || 'WF-LIVE'}
          </span>
        </div>
      </div>

      {/* Graph Nodes Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {nodes.map((node, idx) => {
          const state = getNodeState(node);
          const style = getStatusStyle(state);
          const Icon = node.icon;

          return (
            <div
              key={idx}
              className={`p-3.5 rounded-xl border flex flex-col justify-between space-y-2.5 transition-all duration-200 ${style}`}
            >
              <div className="flex items-center justify-between">
                <Icon className="w-4 h-4" />
                <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-dark-900/80 border border-dark-700 uppercase">
                  {state}
                </span>
              </div>
              <div>
                <div className="font-bold text-xs leading-snug">{node.label}</div>
                <div className="text-[10px] text-gray-400 font-mono mt-0.5">{node.type}</div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
