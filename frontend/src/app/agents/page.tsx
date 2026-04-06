"use client";
import { useQuery } from "@tanstack/react-query";
import { fetchApi, cn, timeAgo } from "@/lib/utils";
import { useWebSocket } from "@/hooks/useWebSocket";
import { Bot, Filter, Download, CheckCircle2, XCircle, Loader2, Clock, Info, AlertTriangle } from "lucide-react";
import { useState } from "react";

const AGENT_TYPES = [
  { value: "", label: "All Agents" },
  { value: "orchestrator", label: "Orchestrator" },
  { value: "trial_balance_validator", label: "Trial Balance" },
  { value: "variance_analysis", label: "Variance Analysis" },
  { value: "accrual_verification", label: "Accrual Verification" },
  { value: "intercompany_elimination", label: "IC Elimination" },
  { value: "revenue_recognition", label: "Revenue Recognition" },
  { value: "expense_categorization", label: "Expense Categorization" },
  { value: "cash_flow_reconciliation", label: "Cash Flow" },
  { value: "consolidation", label: "Consolidation" },
  { value: "reporting_communication", label: "Reporting" },
];

const SEVERITY_COLORS: Record<string, string> = {
  info: "text-blue-400 bg-blue-500/10",
  warning: "text-amber-400 bg-amber-500/10",
  error: "text-red-400 bg-red-500/10",
  critical: "text-red-500 bg-red-500/20",
};

export default function AgentsPage() {
  const [agentFilter, setAgentFilter] = useState("");
  const [severityFilter, setSeverityFilter] = useState("");
  const { updates, connected } = useWebSocket();

  const { data: logs, isLoading } = useQuery({
    queryKey: ["agent-logs-full", agentFilter, severityFilter],
    queryFn: () => {
      let url = "/api/agents/logs?limit=100";
      if (agentFilter) url += `&agent_type=${agentFilter}`;
      if (severityFilter) url += `&severity=${severityFilter}`;
      return fetchApi<any>(url);
    },
  });

  const { data: statusData } = useQuery({
    queryKey: ["agent-status"],
    queryFn: () => fetchApi<any>("/api/agents/status"),
  });

  const agents = statusData?.agents || [];
  const allLogs = logs?.logs || [];

  // Stats
  const totalCompleted = agents.reduce((s: number, a: any) => s + (a.completed_count || 0), 0);
  const totalFailed = agents.reduce((s: number, a: any) => s + (a.failed_count || 0), 0);
  const totalRunning = agents.reduce((s: number, a: any) => s + (a.running_count || 0), 0);

  return (
    <div className="space-y-6 max-w-[1600px] mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Agent Activity</h1>
          <p className="text-sm text-slate-500 mt-1">Monitor all AI agent operations in real-time</p>
        </div>
        <div className="flex items-center gap-2">
          <div className={cn("flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium",
            connected ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400"
          )}>
            <div className={cn("w-1.5 h-1.5 rounded-full", connected ? "bg-emerald-500 pulse-dot" : "bg-red-500")} />
            {connected ? "Live" : "Disconnected"}
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: "Total Agents", value: agents.length, icon: Bot, color: "text-violet-400" },
          { label: "Completed", value: totalCompleted, icon: CheckCircle2, color: "text-emerald-400" },
          { label: "Running", value: totalRunning, icon: Loader2, color: "text-amber-400" },
          { label: "Failed", value: totalFailed, icon: XCircle, color: "text-red-400" },
        ].map((s, i) => (
          <div key={i} className="glass-card p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-500">{s.label}</p>
                <p className={cn("text-2xl font-bold mt-1", s.color)}>{s.value}</p>
              </div>
              <s.icon className={cn("w-5 h-5", s.color)} />
            </div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <Filter className="w-4 h-4 text-slate-500" />
        <select value={agentFilter} onChange={(e) => setAgentFilter(e.target.value)}
          className="bg-slate-800 border border-slate-700 text-slate-300 text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-violet-500">
          {AGENT_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
        </select>
        <select value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)}
          className="bg-slate-800 border border-slate-700 text-slate-300 text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-violet-500">
          <option value="">All Severities</option>
          <option value="info">Info</option>
          <option value="warning">Warning</option>
          <option value="error">Error</option>
          <option value="critical">Critical</option>
        </select>
      </div>

      {/* Activity Log Table */}
      <div className="glass-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-700 bg-slate-800/50">
                <th className="text-left py-3 px-4 text-xs text-slate-500 font-medium">Status</th>
                <th className="text-left py-3 px-4 text-xs text-slate-500 font-medium">Agent</th>
                <th className="text-left py-3 px-4 text-xs text-slate-500 font-medium">Action</th>
                <th className="text-left py-3 px-4 text-xs text-slate-500 font-medium">Company</th>
                <th className="text-left py-3 px-4 text-xs text-slate-500 font-medium">Severity</th>
                <th className="text-right py-3 px-4 text-xs text-slate-500 font-medium">Duration</th>
                <th className="text-right py-3 px-4 text-xs text-slate-500 font-medium">Time</th>
              </tr>
            </thead>
            <tbody>
              {allLogs.map((log: any) => (
                <tr key={log.id} className="border-b border-slate-800/50 hover:bg-slate-800/30 transition">
                  <td className="py-2.5 px-4">
                    {log.status === "completed" ? <CheckCircle2 className="w-4 h-4 text-emerald-400" /> :
                     log.status === "running" ? <Loader2 className="w-4 h-4 text-violet-400 animate-spin" /> :
                     log.status === "failed" ? <XCircle className="w-4 h-4 text-red-400" /> :
                     <Clock className="w-4 h-4 text-slate-500" />}
                  </td>
                  <td className="py-2.5 px-4 text-slate-300">{log.agent_type?.replace(/_/g, " ")}</td>
                  <td className="py-2.5 px-4 text-slate-400 max-w-[300px] truncate">{log.action}</td>
                  <td className="py-2.5 px-4 text-slate-500">{log.company_id || "—"}</td>
                  <td className="py-2.5 px-4">
                    <span className={cn("px-2 py-0.5 rounded text-[11px] font-medium", SEVERITY_COLORS[log.severity] || SEVERITY_COLORS.info)}>
                      {log.severity}
                    </span>
                  </td>
                  <td className="py-2.5 px-4 text-right text-slate-500 text-xs">{log.duration_ms ? `${log.duration_ms}ms` : "—"}</td>
                  <td className="py-2.5 px-4 text-right text-slate-600 text-xs">{log.created_at ? timeAgo(log.created_at) : ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {allLogs.length === 0 && (
            <div className="text-center py-12 text-slate-500">
              <Bot className="w-8 h-8 mx-auto mb-2 opacity-30" />
              <p>No agent activity recorded yet.</p>
              <p className="text-xs mt-1">Run the close workflow to see agents in action.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
