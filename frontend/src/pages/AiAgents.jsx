import React, { useState, useEffect } from 'react';
import { Bot, UserCheck, Calendar, Users, BedDouble, Siren, BookOpen, BarChart3, Network, ShieldCheck, RefreshCw } from 'lucide-react';
import { AgentStatusCard } from '../components/AgentStatusCard';
import { WorkflowGraphVisualizer } from '../components/WorkflowGraphVisualizer';
import { apiService } from '../services/api';

export function AiAgentsPage() {
  const [latestWorkflow, setLatestWorkflow] = useState(null);
  const [events, setEvents] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchActiveState = async () => {
    setIsLoading(true);
    try {
      const history = await apiService.getWorkflows();
      if (history && history.length > 0) {
        const top = history[0];
        setLatestWorkflow(top);
        const evs = await apiService.getWorkflowEvents(top.workflow_id);
        setEvents(evs);
      }
    } catch (err) {
      console.error("Failed to load workflow state:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchActiveState();
  }, []);

  const agents = [
    {
      name: 'Coordinator Agent',
      status: 'Active (LangGraph)',
      phase: 'Phase 3',
      toolsCount: 12,
      description: 'LangGraph state graph engine that routes incoming requests across agents and orchestrates multi-agent handoffs.',
      icon: Network
    },
    {
      name: 'Patient Agent',
      status: 'Active Node',
      phase: 'Phase 3',
      toolsCount: 3,
      description: 'Queries patient health history, department records, and past/upcoming appointment lists directly through SQLite patient tools.',
      icon: Users
    },
    {
      name: 'Doctor Agent',
      status: 'Active Node',
      phase: 'Phase 3',
      toolsCount: 4,
      description: 'Checks real-time doctor availability on shift, specializations, shift schedules, and workload through SQLite doctor tools.',
      icon: UserCheck
    },
    {
      name: 'Appointment Agent',
      status: 'Active Node',
      phase: 'Phase 3',
      toolsCount: 5,
      description: 'Calculates optimal appointment slots based on doctor shift data and enforces validation before human-in-the-loop approval.',
      icon: Calendar
    },
    {
      name: 'Validation Node',
      status: 'Active Safety Node',
      phase: 'Phase 3',
      toolsCount: 3,
      description: 'Validates operational parameters, doctor/patient existence, slot availability, and enforces human sign-off boundary.',
      icon: ShieldCheck
    },
    {
      name: 'Bed & Allocation Agent',
      status: 'Phase 4',
      phase: 'Phase 4',
      toolsCount: 0,
      description: 'Monitors ICU, Emergency, and General ward bed utilization and handles automated bed reservation and step-down transfers.',
      icon: BedDouble
    },
    {
      name: 'Emergency Triage Agent',
      status: 'Phase 4',
      phase: 'Phase 4',
      toolsCount: 0,
      description: 'Prioritizes incoming CRITICAL emergency cases, reserving required bed types and on-call specialist doctors.',
      icon: Siren
    },
    {
      name: 'RAG Policy Agent',
      status: 'Phase 5',
      phase: 'Phase 5',
      toolsCount: 0,
      description: 'Retrieves hospital operational policies and administrative protocols via ChromaDB vector index.',
      icon: BookOpen
    }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center bg-dark-800 border border-dark-700/80 p-6 rounded-2xl shadow-xl">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Bot className="w-5 h-5 text-cyan-400" />
            <span>Multi-Agent Workflow Ecosystem</span>
          </h1>
          <p className="text-xs text-gray-400 mt-1">Live LangGraph state graph engine, tool grounding, and operational agent matrix.</p>
        </div>

        <button
          onClick={fetchActiveState}
          disabled={isLoading}
          className="px-3.5 py-2 bg-dark-700 hover:bg-dark-600 text-white font-mono text-xs rounded-xl flex items-center gap-2 border border-dark-600 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>Sync State</span>
        </button>
      </div>

      {/* Live State Graph Visualizer */}
      <WorkflowGraphVisualizer currentWorkflow={latestWorkflow} events={events} />

      {/* Agents Matrix */}
      <div className="space-y-3">
        <h2 className="text-xs font-mono text-gray-400 uppercase tracking-wider">SPECIALIZED AGENTS MATRIX</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {agents.map((agent, idx) => (
            <AgentStatusCard
              key={idx}
              name={agent.name}
              status={agent.status}
              phase={agent.phase}
              toolsCount={agent.toolsCount}
              description={agent.description}
              activeIcon={agent.icon}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
