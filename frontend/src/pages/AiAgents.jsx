import React from 'react';
import { Bot, UserCheck, Calendar, Users, BedDouble, Siren, BookOpen, BarChart3, Network } from 'lucide-react';
import { AgentStatusCard } from '../components/AgentStatusCard';

export function AiAgentsPage() {
  const agents = [
    {
      name: 'Patient Agent',
      status: 'Active',
      phase: 'Phase 2',
      toolsCount: 3,
      description: 'Queries patient health history, department records, and past/upcoming appointment lists directly through the patient service layer.',
      icon: Users
    },
    {
      name: 'Doctor Agent',
      status: 'Active',
      phase: 'Phase 2',
      toolsCount: 4,
      description: 'Checks real-time doctor availability on shift, specializations, shift schedules, and current patient workloads across departments.',
      icon: UserCheck
    },
    {
      name: 'Appointment Agent',
      status: 'Active',
      phase: 'Phase 2',
      toolsCount: 4,
      description: 'Calculates optimal appointment slots based on doctor availability, patient department, and shift hours. Enforces validation rules.',
      icon: Calendar
    },
    {
      name: 'Coordinator Agent',
      status: 'Phase 3',
      phase: 'Phase 3',
      toolsCount: 0,
      description: 'LangGraph state graph engine that routes incoming requests across agents and orchestrates multi-agent conversation graphs.',
      icon: Network
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
      description: 'Prioritizes incoming CRITICAL and HIGH priority emergency cases, reserving required bed types and on-call specialist doctors.',
      icon: Siren
    },
    {
      name: 'RAG Policy Agent',
      status: 'Phase 5',
      phase: 'Phase 5',
      toolsCount: 0,
      description: 'Retrieves hospital operational policies, admission guidelines, and administrative protocols via ChromaDB vector index.',
      icon: BookOpen
    },
    {
      name: 'Resource Prediction Agent',
      status: 'Phase 6',
      phase: 'Phase 6',
      toolsCount: 0,
      description: 'Machine learning model predicting bed demand surges and ER admission rates using historical hospital trends.',
      icon: BarChart3
    }
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center bg-dark-800 border border-dark-700/80 p-6 rounded-2xl shadow-xl">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Bot className="w-5 h-5 text-cyan-400" />
            <span>AI Agents Ecosystem</span>
          </h1>
          <p className="text-xs text-gray-400 mt-1">Multi-agent architecture matrix showing active tools vs future LangGraph nodes.</p>
        </div>

        <div className="flex items-center gap-3 text-xs font-mono">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
            <span>3 Active Agents</span>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
            <span>5 Planned Nodes</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
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
  );
}
