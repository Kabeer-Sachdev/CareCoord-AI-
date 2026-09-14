import React, { useState, useEffect } from 'react';
import { Bell, RefreshCw, Server, User } from 'lucide-react';

export function Topbar({ title, onRefresh, isRefreshing }) {
  const [time, setTime] = useState(new Date().toLocaleTimeString());

  useEffect(() => {
    const timer = setInterval(() => {
      setTime(new Date().toLocaleTimeString());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="h-16 border-b border-dark-700/80 bg-dark-800/80 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-20 shrink-0">
      <div className="flex items-center gap-4">
        <h2 className="text-lg font-bold text-white tracking-tight capitalize">{title}</h2>
        <span className="hidden md:inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-mono bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
          <Server className="w-3 h-3" />
          <span>CARECOORD CORE</span>
        </span>
      </div>

      <div className="flex items-center gap-5 text-xs">
        {/* Refresh button */}
        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-dark-700 hover:bg-dark-600 border border-dark-600 rounded-lg text-gray-300 transition-colors duration-150 disabled:opacity-50"
            title="Refresh Hospital Data"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-cyan-400' : ''}`} />
            <span className="hidden sm:inline">Sync Data</span>
          </button>
        )}

        {/* Live Clock */}
        <div className="hidden sm:flex items-center gap-2 font-mono text-gray-300 bg-dark-900/60 px-3 py-1.5 rounded-lg border border-dark-700">
          <span className="text-gray-500">TIME:</span>
          <span className="text-cyan-400 font-semibold">{time}</span>
        </div>

        {/* Environment Badge */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-mono text-xs">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span className="hidden md:inline">DEMO ENVIRONMENT</span>
          <span className="md:hidden">DEMO</span>
        </div>

        {/* Notifications Icon */}
        <div className="p-2 rounded-lg bg-dark-700/60 text-gray-400 border border-dark-600 cursor-pointer hover:text-white transition-colors relative">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-cyan-400"></span>
        </div>

        {/* User Profile Placeholder */}
        <div className="flex items-center gap-2 border-l border-dark-700 pl-4">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-gray-700 to-gray-600 border border-gray-500 flex items-center justify-center text-white font-semibold text-xs">
            <User className="w-4 h-4" />
          </div>
          <div className="hidden xl:block text-left">
            <div className="font-semibold text-white leading-none">Ops Command</div>
            <div className="text-[10px] text-gray-400 font-mono">Duty Staff</div>
          </div>
        </div>
      </div>
    </header>
  );
}
