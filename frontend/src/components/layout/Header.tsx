"use client";
import { Bell, Wifi, WifiOff, Menu } from "lucide-react";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useState, useEffect } from "react";
import { fetchApi } from "@/lib/utils";

interface HeaderProps {
  onMenuToggle?: () => void;
}

export function Header({ onMenuToggle }: HeaderProps) {
  const { connected, lastUpdate } = useWebSocket();
  const [unreadCount, setUnreadCount] = useState(0);
  const [showNotif, setShowNotif] = useState(false);

  useEffect(() => {
    fetchApi<any>("/api/notifications?limit=1")
      .then((data) => setUnreadCount(data.unread_count || 0))
      .catch(() => {});
  }, [lastUpdate]);

  return (
    <header className="h-14 sm:h-16 border-b border-slate-800 bg-[#0f172a]/80 backdrop-blur-md flex items-center justify-between px-3 sm:px-6 gap-2">
      {/* Left: hamburger (mobile) + title */}
      <div className="flex items-center gap-2 sm:gap-4 min-w-0">
        {/* Hamburger – only on mobile */}
        <button
          onClick={onMenuToggle}
          className="lg:hidden p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 transition flex-shrink-0"
          aria-label="Open menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        <h2 className="text-sm sm:text-base font-semibold text-slate-200 truncate">
          Portfolio Close Dashboard
        </h2>

        {/* Live update pill — hidden on very small screens */}
        {lastUpdate && (
          <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-full bg-violet-600/10 border border-violet-500/20 fade-in flex-shrink-0">
            <div className="w-1.5 h-1.5 rounded-full bg-violet-500 pulse-dot" />
            <span className="text-xs text-violet-400 max-w-[200px] truncate">
              {lastUpdate.message}
            </span>
          </div>
        )}
      </div>

      {/* Right: status + notifications + period */}
      <div className="flex items-center gap-2 flex-shrink-0">
        {/* Connection Status */}
        <div
          className={`flex items-center gap-1 sm:gap-1.5 px-2 sm:px-3 py-1 sm:py-1.5 rounded-lg text-xs font-medium ${
            connected
              ? "bg-emerald-500/10 text-emerald-400"
              : "bg-red-500/10 text-red-400"
          }`}
        >
          {connected ? (
            <Wifi className="w-3 sm:w-3.5 h-3 sm:h-3.5" />
          ) : (
            <WifiOff className="w-3 sm:w-3.5 h-3 sm:h-3.5" />
          )}
          <span className="hidden xs:inline">
            {connected ? "Live" : "Offline"}
          </span>
        </div>

        {/* Notifications */}
        <button
          onClick={() => setShowNotif(!showNotif)}
          className="relative p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 transition"
        >
          <Bell className="w-4 sm:w-5 h-4 sm:h-5" />
          {unreadCount > 0 && (
            <span className="notification-badge">
              {unreadCount > 99 ? "99+" : unreadCount}
            </span>
          )}
        </button>

        {/* Period Selector — hidden on small mobile */}
        <select className="hidden sm:block bg-slate-800 border border-slate-700 text-slate-300 text-xs sm:text-sm rounded-lg px-2 sm:px-3 py-1 sm:py-1.5 focus:outline-none focus:ring-1 focus:ring-violet-500">
          <option value="2026-01">Jan 2026</option>
          <option value="2025-12">Dec 2025</option>
          <option value="2025-11">Nov 2025</option>
        </select>
      </div>
    </header>
  );
}
