import React, { useState, useEffect } from 'react';
import { History, Filter, RefreshCw, Eye, CheckCircle2, ShieldAlert, FileText } from 'lucide-react';
import { StatusBadge } from '../components/StatusBadge';
import { WorkflowDetailDrawer } from '../components/WorkflowDetailDrawer';
import { apiService } from '../services/api';

export function WorkflowHistoryPage() {
  const [workflows, setWorkflows] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState('ALL');
  const [selectedWorkflow, setSelectedWorkflow] = useState(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const fetchWorkflows = async () => {
    setIsLoading(true);
    try {
      const data = await apiService.getWorkflows();
      setWorkflows(data);
    } catch (err) {
      console.error("Failed to fetch workflow history:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkflows();
  }, []);

  const handleOpenDrawer = async (wf) => {
    try {
      const detail = await apiService.getWorkflowById(wf.workflow_id);
      setSelectedWorkflow(detail);
      setIsDrawerOpen(true);
    } catch (err) {
      setSelectedWorkflow(wf);
      setIsDrawerOpen(true);
    }
  };

  const filteredWorkflows = workflows.filter(wf => {
    if (filter === 'APPROVAL') return wf.requires_human_approval || wf.status === 'REQUIRES_HUMAN_APPROVAL';
    if (filter === 'COMPLETED') return wf.status === 'COMPLETED' || wf.status === 'APPROVED' || wf.status === 'success';
    if (filter === 'CLARIFICATION') return wf.status === 'NEEDS_CLARIFICATION' || wf.status === 'clarification_required';
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-dark-800 border border-dark-700/80 p-6 rounded-2xl shadow-xl">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-cyan-500/10 text-cyan-400 rounded-xl border border-cyan-500/20">
            <History className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">Workflow Execution Audit History</h1>
            <p className="text-xs text-gray-400 mt-1">Audit log of all LangGraph stateful multi-agent executions, tool calls, and human approvals.</p>
          </div>
        </div>

        <button
          onClick={fetchWorkflows}
          disabled={isLoading}
          className="px-4 py-2 bg-dark-700 hover:bg-dark-600 text-white font-medium text-xs rounded-xl flex items-center gap-2 border border-dark-600 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>Refresh Audit Logs</span>
        </button>
      </div>

      {/* Filter Tabs & Counter */}
      <div className="flex justify-between items-center bg-dark-800 border border-dark-700/80 p-4 rounded-xl shadow-lg">
        <div className="flex flex-wrap gap-2 text-xs font-mono">
          {[
            { id: 'ALL', label: 'All Runs' },
            { id: 'APPROVAL', label: 'Awaiting Approval' },
            { id: 'COMPLETED', label: 'Completed' },
            { id: 'CLARIFICATION', label: 'Clarification' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setFilter(tab.id)}
              className={`px-3 py-1.5 rounded-lg border transition-all ${
                filter === tab.id
                  ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400 font-bold'
                  : 'bg-dark-900 border-dark-700 text-gray-400 hover:text-white'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <span className="text-xs font-mono text-gray-400">
          Total Recorded: <strong className="text-white">{filteredWorkflows.length}</strong>
        </span>
      </div>

      {/* Workflow Table */}
      <div className="bg-dark-800 border border-dark-700/80 rounded-2xl shadow-xl overflow-hidden">
        {isLoading ? (
          <div className="p-12 text-center text-gray-400 text-xs font-mono space-y-2">
            <div className="w-6 h-6 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mx-auto"></div>
            <div>Loading workflow execution logs from SQLite...</div>
          </div>
        ) : filteredWorkflows.length === 0 ? (
          <div className="p-12 text-center text-gray-500 text-xs font-mono">
            No workflow executions match the selected filter.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-sans">
              <thead className="bg-dark-900/80 border-b border-dark-700 text-[10px] font-mono text-gray-400 uppercase tracking-wider">
                <tr>
                  <th className="py-3.5 px-4">Workflow ID</th>
                  <th className="py-3.5 px-4">Request Query</th>
                  <th className="py-3.5 px-4">Type</th>
                  <th className="py-3.5 px-4">Primary Agent</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4">Timestamp</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-700/50">
                {filteredWorkflows.map((wf) => (
                  <tr key={wf.id} className="hover:bg-dark-700/30 transition-colors">
                    <td className="py-3.5 px-4 font-mono font-bold text-cyan-400 whitespace-nowrap">
                      {wf.workflow_id}
                    </td>
                    <td className="py-3.5 px-4 font-medium text-white max-w-xs truncate">
                      "{wf.original_request}"
                    </td>
                    <td className="py-3.5 px-4 font-mono text-gray-400 uppercase">
                      {wf.workflow_type}
                    </td>
                    <td className="py-3.5 px-4 font-mono text-emerald-400">
                      {wf.agent_used || 'Coordinator'}
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <StatusBadge status={wf.status} />
                    </td>
                    <td className="py-3.5 px-4 font-mono text-gray-500 text-[11px] whitespace-nowrap">
                      {wf.started_at ? wf.started_at.split('.')[0] : 'N/A'}
                    </td>
                    <td className="py-3.5 px-4 text-right whitespace-nowrap">
                      <button
                        onClick={() => handleOpenDrawer(wf)}
                        className="px-3 py-1.5 bg-dark-900 hover:bg-dark-700 text-gray-300 border border-dark-700 rounded-lg font-mono text-[11px] flex items-center gap-1.5 ml-auto transition-colors"
                      >
                        <Eye className="w-3.5 h-3.5 text-cyan-400" />
                        <span>Inspect Log</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Detail Drawer Modal */}
      {isDrawerOpen && (
        <WorkflowDetailDrawer
          workflow={selectedWorkflow}
          onClose={() => setIsDrawerOpen(false)}
          onApprovalComplete={() => {
            fetchWorkflows();
            setIsDrawerOpen(false);
          }}
        />
      )}
    </div>
  );
}
