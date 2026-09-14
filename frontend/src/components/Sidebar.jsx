import React from 'react';
import { 
  LayoutDashboard, 
  Users, 
  UserCheck, 
  Calendar, 
  BedDouble, 
  Siren, 
  Bot, 
  Terminal, 
  BarChart3, 
  BookOpen, 
  Settings, 
  Activity 
} from 'lucide-react';

export function Sidebar({ currentPage, setCurrentPage }) {
  const mainNav = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'patients', label: 'Patients', icon: Users },
    { id: 'doctors', label: 'Doctors', icon: UserCheck },
    { id: 'appointments', label: 'Appointments', icon: Calendar },
    { id: 'ai-agents', label: 'AI Agents', icon: Bot },
    { id: 'workflow', label: 'Workflow Terminal', icon: Terminal, highlight: true },
  ];

  const futureNav = [
    { id: 'beds', label: 'Beds & Resource', icon: BedDouble, badge: 'Phase 4' },
    { id: 'emergency', label: 'Emergency Center', icon: Siren, badge: 'Phase 4' },
    { id: 'analytics', label: 'ML Analytics', icon: BarChart3, badge: 'Phase 6' },
    { id: 'policies', label: 'RAG Policies', icon: BookOpen, badge: 'Phase 5' },
    { id: 'settings', label: 'Settings', icon: Settings, badge: 'Phase 8' },
  ];

  return (
    <aside className="w-64 bg-dark-800 border-r border-dark-700/80 flex flex-col justify-between h-screen sticky top-0 z-30 select-none shrink-0">
      <div>
        {/* Brand Header */}
        <div className="h-16 flex items-center px-6 border-b border-dark-700/80 gap-3">
          <div className="p-2 bg-gradient-to-tr from-cyan-500 to-blue-600 rounded-lg shadow-lg shadow-cyan-500/20 text-white">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <h1 className="font-bold tracking-tight text-white text-base">CareCoord <span className="text-cyan-400 font-mono text-xs">AI</span></h1>
            <p className="text-[10px] text-gray-400 font-mono uppercase tracking-wider">Hospital Ops Terminal</p>
          </div>
        </div>

        {/* Navigation Sections */}
        <div className="p-4 space-y-6 overflow-y-auto max-h-[calc(100vh-140px)]">
          <div>
            <div className="px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-widest font-mono mb-2">Core Workflow</div>
            <nav className="space-y-1">
              {mainNav.map((item) => {
                const Icon = item.icon;
                const active = currentPage === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setCurrentPage(item.id)}
                    className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-all duration-150 ${
                      active
                        ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 shadow-sm'
                        : 'text-gray-300 hover:bg-dark-700/60 hover:text-white border border-transparent'
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <Icon className={`w-4 h-4 ${active ? 'text-cyan-400' : 'text-gray-400'}`} />
                      <span>{item.label}</span>
                    </div>
                    {item.highlight && (
                      <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
                    )}
                  </button>
                );
              })}
            </nav>
          </div>

          <div>
            <div className="px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-widest font-mono mb-2">Planned Modules</div>
            <nav className="space-y-1">
              {futureNav.map((item) => {
                const Icon = item.icon;
                return (
                  <div
                    key={item.id}
                    className="flex items-center justify-between px-3 py-2.5 rounded-lg text-xs text-gray-500 opacity-60 cursor-not-allowed border border-transparent"
                  >
                    <div className="flex items-center gap-2.5">
                      <Icon className="w-4 h-4 text-gray-600" />
                      <span>{item.label}</span>
                    </div>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-dark-700 text-gray-400 border border-dark-600">
                      {item.badge}
                    </span>
                  </div>
                );
              })}
            </nav>
          </div>
        </div>
      </div>

      {/* System Status Footer */}
      <div className="p-4 border-t border-dark-700/80 bg-dark-900/40">
        <div className="flex items-center justify-between px-3 py-2 bg-dark-800 rounded-lg border border-dark-700 text-xs">
          <div className="flex items-center gap-2 font-mono text-gray-300">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>SYSTEM ONLINE</span>
          </div>
          <span className="text-[10px] font-mono text-gray-500">v1.0.0</span>
        </div>
      </div>
    </aside>
  );
}
