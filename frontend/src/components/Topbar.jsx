import React, { useState, useEffect } from 'react';
import { RefreshCw, Server, User, LogOut, Radio } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { NotificationCenter } from './NotificationCenter';
import { wsClient } from '../services/websocket';

export function Topbar({ title, onRefresh, isRefreshing, onLogout }) {
  const { user, role, logout } = useAuth();
  const [time, setTime] = useState(new Date().toLocaleTimeString());
  const [wsOnline, setWsOnline] = useState(wsClient.isConnected);

  useEffect(() => {
    const timer = setInterval(() => {
      setTime(new Date().toLocaleTimeString());
      setWsOnline(wsClient.isConnected);
    }, 1000);

    const unsubConn = wsClient.on('connected', () => setWsOnline(true));
    const unsubDisconn = wsClient.on('disconnected', () => setWsOnline(false));

    return () => {
      clearInterval(timer);
      unsubConn();
      unsubDisconn();
    };
  }, []);

  const handleLogout = () => {
    logout();
    if (onLogout) onLogout();
  };

  const rolePillColors = {
    ADMIN: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30',
    DOCTOR: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    RECEPTIONIST: 'bg-purple-500/10 text-purple-400 border-purple-500/30',
    NURSE: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    PATIENT: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
  };

  return (
    <header className="h-16 border-b border-dark-700/80 bg-dark-800/80 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-20 shrink-0">
      <div className="flex items-center gap-4">
        <h2 className="text-lg font-bold text-white tracking-tight capitalize">{title}</h2>
        <span className="hidden md:inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-mono bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
          <Server className="w-3 h-3" />
          <span>CARECOORD CORE</span>
        </span>
      </div>

      <div className="flex items-center gap-4 text-xs">
        {/* Real-time WebSocket Status Indicator */}
        <div 
          title={wsOnline ? 'Real-time WebSocket connected' : 'WebSocket disconnected'}
          className={`hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-lg border font-mono text-[11px] ${
            wsOnline 
              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' 
              : 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'
          }`}
        >
          <span className={`w-2 h-2 rounded-full ${wsOnline ? 'bg-emerald-400 animate-pulse' : 'bg-yellow-400'}`}></span>
          <span>{wsOnline ? 'LIVE WS' : 'CONNECTING'}</span>
        </div>

        {/* Refresh button */}
        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-dark-700 hover:bg-dark-600 border border-dark-600 rounded-lg text-gray-300 transition-colors duration-150 disabled:opacity-50"
            title="Refresh Hospital Data"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-cyan-400' : ''}`} />
            <span className="hidden sm:inline">Sync</span>
          </button>
        )}

        {/* Live Clock */}
        <div className="hidden sm:flex items-center gap-2 font-mono text-gray-300 bg-dark-900/60 px-3 py-1.5 rounded-lg border border-dark-700">
          <span className="text-gray-500">TIME:</span>
          <span className="text-cyan-400 font-semibold">{time}</span>
        </div>

        {/* Environment Badge */}
        <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-mono text-xs">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>DEMO ENVIRONMENT</span>
        </div>

        {/* Notification Center with live unread badge */}
        <NotificationCenter />

        {/* User Profile Badge */}
        <div className="flex items-center gap-2.5 border-l border-dark-700 pl-3">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-cyan-600 to-blue-600 border border-cyan-400/30 flex items-center justify-center text-white font-semibold text-xs shrink-0">
            {user?.full_name ? user.full_name.charAt(0).toUpperCase() : <User className="w-4 h-4" />}
          </div>
          <div className="hidden xl:block text-left">
            <div className="font-semibold text-white leading-none text-xs">{user?.full_name || 'CareCoord User'}</div>
            <div className="flex items-center gap-1 mt-1">
              <span className={`px-1.5 py-0.2 rounded text-[9px] font-mono border ${rolePillColors[role] || 'bg-gray-800 text-gray-400'}`}>
                {role || 'USER'}
              </span>
            </div>
          </div>
          <button
            onClick={handleLogout}
            title="Log Out"
            className="p-1.5 text-gray-400 hover:text-red-400 hover:bg-dark-700 rounded-lg transition-colors"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
}