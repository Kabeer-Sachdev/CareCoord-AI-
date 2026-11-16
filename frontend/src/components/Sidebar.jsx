import React from 'react';
import { 
  LayoutDashboard, 
  Users, 
  UserCheck, 
  Calendar, 
  Bot, 
  Terminal, 
  History,
  Activity,
  LogOut,
  Stethoscope,
  Heart,
  User,
  ShieldAlert,
  BookOpen,
  TrendingUp,
  Sliders,
  Share2
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export function Sidebar({ currentPage, setCurrentPage, onLogout }) {
  const { user, role, logout } = useAuth();

  const handleLogout = () => {
    logout();
    if (onLogout) onLogout();
  };

  // Role-based Nav links
  const getNavItems = () => {
    if (role === 'DOCTOR') {
      return [
        { id: 'doctor-portal', label: 'Doctor Schedule', icon: Stethoscope, highlight: true },
        { id: 'integrations', label: 'External Integrations', icon: Share2 },
        { id: 'optimization', label: 'Resource Optimization', icon: Sliders },
        { id: 'predictions', label: 'Predictive Analytics', icon: TrendingUp },
        { id: 'policies', label: 'Hospital Policies', icon: BookOpen },
        { id: 'overview', label: 'Hospital Overview', icon: LayoutDashboard },
        { id: 'workflows', label: 'Workflow History', icon: History },
      ];
    }
    if (role === 'RECEPTIONIST') {
      return [
        { id: 'reception-portal', label: 'Reception Desk', icon: UserCheck, highlight: true },
        { id: 'integrations', label: 'External Integrations', icon: Share2 },
        { id: 'optimization', label: 'Resource Optimization', icon: Sliders },
        { id: 'predictions', label: 'Predictive Analytics', icon: TrendingUp },
        { id: 'policies', label: 'Hospital Policies', icon: BookOpen },
        { id: 'patients', label: 'Patients', icon: Users },
        { id: 'doctors', label: 'Doctors', icon: Stethoscope },
        { id: 'appointments', label: 'Appointments', icon: Calendar },
        { id: 'workflow', label: 'Workflow Terminal', icon: Terminal },
        { id: 'workflows', label: 'Workflow History', icon: History },
      ];
    }
    if (role === 'NURSE') {
      return [
        { id: 'nurse-portal', label: 'Nurse Station', icon: Heart, highlight: true },
        { id: 'optimization', label: 'Resource Optimization', icon: Sliders },
        { id: 'predictions', label: 'Predictive Analytics', icon: TrendingUp },
        { id: 'policies', label: 'Hospital Policies', icon: BookOpen },
        { id: 'overview', label: 'Hospital Overview', icon: LayoutDashboard },
      ];
    }
    if (role === 'PATIENT') {
      return [
        { id: 'patient-portal', label: 'Patient Portal', icon: User, highlight: true },
        { id: 'policies', label: 'Hospital Policies', icon: BookOpen },
        { id: 'overview', label: 'Hospital Overview', icon: LayoutDashboard },
      ];
    }

    // Default / ADMIN navigation
    return [
      { id: 'overview', label: 'Command Center', icon: LayoutDashboard },
      { id: 'integrations', label: 'External Integrations', icon: Share2, highlight: true },
      { id: 'optimization', label: 'Resource Optimization', icon: Sliders },
      { id: 'predictions', label: 'Predictive Analytics', icon: TrendingUp },
      { id: 'policies', label: 'Hospital Policies', icon: BookOpen },
      { id: 'reception-portal', label: 'Reception Portal', icon: UserCheck },
      { id: 'doctor-portal', label: 'Doctor Portal', icon: Stethoscope },
      { id: 'nurse-portal', label: 'Nurse Portal', icon: Heart },
      { id: 'patient-portal', label: 'Patient Portal', icon: User },
      { id: 'patients', label: 'Patients', icon: Users },
      { id: 'doctors', label: 'Doctors', icon: UserCheck },
      { id: 'appointments', label: 'Appointments', icon: Calendar },
      { id: 'ai-agents', label: 'AI Agents', icon: Bot },
      { id: 'workflow', label: 'Workflow Terminal', icon: Terminal },
      { id: 'workflows', label: 'Workflow History', icon: History },
    ];
  };

  const navItems = getNavItems();

  const rolePillColors = {
    ADMIN: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30',
    DOCTOR: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    RECEPTIONIST: 'bg-purple-500/10 text-purple-400 border-purple-500/30',
    NURSE: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    PATIENT: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
  };

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
        <div className="p-4 space-y-4 overflow-y-auto max-h-[calc(100vh-200px)]">
          <div>
            <div className="px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-widest font-mono mb-2">
              {role ? `${role} Navigation` : 'Core Navigation'}
            </div>
            <nav className="space-y-1">
              {navItems.map((item) => {
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
        </div>
      </div>

      {/* User Footer & Logout */}
      <div className="p-3 border-t border-dark-700/80 bg-dark-900/40 space-y-2">
        <div className="flex items-center justify-between px-3 py-2 bg-dark-800 rounded-lg border border-dark-700">
          <div className="min-w-0 flex-1">
            <div className="font-semibold text-white text-xs truncate">
              {user?.full_name || 'Anonymous User'}
            </div>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className={`px-1.5 py-0.2 rounded text-[9px] font-mono border ${rolePillColors[role] || 'bg-gray-800 text-gray-400'}`}>
                {role || 'USER'}
              </span>
              <span className="text-[10px] text-gray-500 font-mono truncate">{user?.username}</span>
            </div>
          </div>
          <button
            onClick={handleLogout}
            title="Log Out"
            className="p-1.5 text-gray-400 hover:text-red-400 hover:bg-dark-700 rounded-lg transition-colors ml-2"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>

        <div className="flex items-center justify-between px-3 py-1 text-[10px] text-gray-500 font-mono">
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
            LIVE WS
          </span>
          <span>CareCoord v1.0</span>
        </div>
      </div>
    </aside>
  );
}