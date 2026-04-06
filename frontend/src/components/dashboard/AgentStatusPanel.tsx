"use client";
import { useQuery } from "@tanstack/react-query";
import { fetchApi, cn, timeAgo } from "@/lib/utils";
import { Bot, CheckCircle2, XCircle, Loader2, Clock } from "lucide-react";

const agentIcons: Record<string, string> = {
  orchestrator: "🎯",
  trial_balance_validator: "⚖️",
  variance_analysis: "📊",
  accrual_verification: "📋",
  intercompany_elimination: "🔄",
  revenue_recognition: "💰",
  expense_categorization: "🏷️",
  cash_flow_reconciliation: "🏦",
  consolidation: "📦",
  reporting_communication: "📧",
};

export function AgentStatusPanel() {
  const { data, isLoading } = useQuery({
    queryKey: ["agent-status"],
    queryFn: () => fetchApi<any>("/api/agents/status"),
  });

  if (isLoading) {
    return (
      <div className="glass-card p-5">
        <h3 className="text-lg font-semibold text-slate-200 mb-4">Agent Status</h3>
        <div className="space-y-2">
          {[...Array(5)].map((_, i) => <div key={i} className="h-10 shimmer rounded-lg" />)}
        </div>
      </div>
    );
  }

  const agents = data?.agents || [];

  return (
    <div className="glass-card p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-slate-200">Agent Status</h3>
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <Bot className="w-4 h-4" />
          {agents.length} agents
        </div>
      </div>

      <div className="space-y-2 max-h-[400px] overflow-y-auto">
        {agents.map((agent: any) => (
          <div key={agent.agent_type}
            className={cn(
              "flex items-center justify-between p-3 rounded-lg border transition",
              agent.status === "running"
                ? "bg-violet-500/5 border-violet-500/20"
                : agent.status === "completed"
                ? "bg-slate-800/30 border-slate-700/30"
                : agent.status === "failed"
                ? "bg-red-500/5 border-red-500/20"
                : "bg-slate-800/20 border-slate-800"
            )}>
            <div className="flex items-center gap-3 min-w-0">
              <span className="text-lg">{agentIcons[agent.agent_type] || "🤖"}</span>
              <div className="min-w-0">
                <p className="text-sm font-medium text-slate-300 truncate">{agent.display_name}</p>
                <p className="text-[11px] text-slate-500 truncate">
                  {agent.last_action || "Idle"}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3 flex-shrink-0">
              <div className="text-right">
                <div className="flex items-center gap-1.5">
                  {agent.status === "running" ? (
                    <Loader2 className="w-3.5 h-3.5 text-violet-400 animate-spin" />
                  ) : agent.status === "completed" ? (
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  ) : agent.status === "failed" ? (
                    <XCircle className="w-3.5 h-3.5 text-red-400" />
                  ) : (
                    <Clock className="w-3.5 h-3.5 text-slate-500" />
                  )}
                  <span className={cn("text-xs font-medium capitalize",
                    agent.status === "running" ? "text-violet-400" :
                    agent.status === "completed" ? "text-emerald-400" :
                    agent.status === "failed" ? "text-red-400" : "text-slate-500"
                  )}>{agent.status}</span>
                </div>
                {agent.last_run && (
                  <p className="text-[10px] text-slate-600 mt-0.5">{timeAgo(agent.last_run)}</p>
                )}
              </div>
              <div className="text-right min-w-[50px]">
                <p className="text-xs text-emerald-400 font-medium">{agent.completed_count}</p>
                <p className="text-[10px] text-slate-600">done</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
