"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard, Building2, Bot, FileBarChart,
  Settings, Activity, Bell, ChevronLeft, TrendingUp
} from "lucide-react";
import { useState } from "react";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/agents", label: "Agent Activity", icon: Bot },
  { href: "/reports", label: "Reports", icon: FileBarChart },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside className={cn(
      "h-screen flex flex-col bg-[#0f172a] border-r border-slate-800 transition-all duration-300",
      collapsed ? "w-[68px]" : "w-[260px]"
    )}>
      {/* Logo */}
      <div className="flex items-center gap-3 p-5 border-b border-slate-800">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center flex-shrink-0">
          <TrendingUp className="w-5 h-5 text-white" />
        </div>
        {!collapsed && (
          <div className="overflow-hidden">
            <h1 className="text-sm font-bold gradient-text whitespace-nowrap">Apex Capital</h1>
            <p className="text-[10px] text-slate-500 whitespace-nowrap">Month-End Close</p>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
          return (
            <Link key={item.href} href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all",
                isActive
                  ? "bg-violet-600/15 text-violet-400 border border-violet-500/20"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
              )}>
              <item.icon className={cn("w-5 h-5 flex-shrink-0", isActive && "text-violet-400")} />
              {!collapsed && <span>{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Collapse Button */}
      <button onClick={() => setCollapsed(!collapsed)}
        className="m-3 p-2 rounded-lg text-slate-500 hover:text-slate-300 hover:bg-slate-800/50 transition flex items-center justify-center">
        <ChevronLeft className={cn("w-4 h-4 transition-transform", collapsed && "rotate-180")} />
      </button>

      {/* System Status */}
      <div className={cn("p-4 border-t border-slate-800", collapsed && "px-2")}>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-500 pulse-dot" />
          {!collapsed && <span className="text-xs text-slate-500">System Active</span>}
        </div>
      </div>
    </aside>
  );
}
