"use client";
import { Bell, Wifi, WifiOff, Search } from "lucide-react";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useState, useEffect } from "react";
import { fetchApi } from "@/lib/utils";

export function Header() {
  const { connected, lastUpdate } = useWebSocket();
  const [unreadCount, setUnreadCount] = useState(0);
  const [showNotif, setShowNotif] = useState(false);

  useEffect(() => {
    fetchApi<any>("/api/notifications?limit=1")
      .then((data) => setUnreadCount(data.unread_count || 0))
      .catch(() => {});
  }, [lastUpdate]);

  return (
    <header className="h-16 border-b border-slate-800 bg-[#0f172a]/80 backdrop-blur-md flex items-center justify-between px-6">
      <div className="flex items-center gap-4">
        <h2 className="text-lg font-semibold text-slate-200">
          Portfolio Close Dashboard
        </h2>
        {lastUpdate && (
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-violet-600/10 border border-violet-500/20 fade-in">
            <div className="w-1.5 h-1.5 rounded-full bg-violet-500 pulse-dot" />
            <span className="text-xs text-violet-400 max-w-[300px] truncate">
              {lastUpdate.message}
            </span>
          </div>
        )}
      </div>

      <div className="flex items-center gap-3">
        {/* Connection Status */}
        <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium ${
          connected ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400"
        }`}>
          {connected ? <Wifi className="w-3.5 h-3.5" /> : <WifiOff className="w-3.5 h-3.5" />}
          {connected ? "Live" : "Offline"}
        </div>

        {/* Notifications */}
        <button
          onClick={() => setShowNotif(!showNotif)}
          className="relative p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 transition"
        >
          <Bell className="w-5 h-5" />
          {unreadCount > 0 && (
            <span className="notification-badge">{unreadCount > 99 ? "99+" : unreadCount}</span>
          )}
        </button>

        {/* Period Selector */}
        <select className="bg-slate-800 border border-slate-700 text-slate-300 text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-violet-500">
          <option value="2026-01">Jan 2026</option>
          <option value="2025-12">Dec 2025</option>
          <option value="2025-11">Nov 2025</option>
        </select>
      </div>
    </header>
  );
}
