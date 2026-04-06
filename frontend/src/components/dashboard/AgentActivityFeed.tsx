"use client";
import { useWebSocket, AgentUpdate } from "@/hooks/useWebSocket";
import { cn, timeAgo } from "@/lib/utils";
import { useQuery } from "@tanstack/react-query";
import { fetchApi } from "@/lib/utils";
import { Activity, Filter } from "lucide-react";
import { useState } from "react";

export function AgentActivityFeed({ maxItems = 20 }: { maxItems?: number }) {
  const { updates } = useWebSocket();
  const [filter, setFilter] = useState<string>("");

  // Also fetch from API for persistence
  const { data: apiLogs } = useQuery({
    queryKey: ["agent-logs"],
    queryFn: () => fetchApi<any>("/api/agents/logs?limit=30"),
  });

  // Merge WebSocket updates with API logs
  const allItems = [
    ...updates.map((u) => ({
      id: `ws-${u.timestamp}`,
      agent_type: u.agent_type,
      agent_name: u.agent_name,
      company_id: u.company_id,
      status: u.status,
      action: u.message,
      severity: u.status === "failed" ? "error" : "info",
      created_at: u.timestamp,
      isLive: true,
    })),
    ...(apiLogs?.logs || []).map((l: any) => ({ ...l, isLive: false })),
  ].slice(0, maxItems);

  const filtered = filter
    ? allItems.filter((item) => item.agent_type === filter)
    : allItems;

  return (
    <div className="glass-card p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-violet-400" />
          <h3 className="text-lg font-semibold text-slate-200">Activity Feed</h3>
          {updates.length > 0 && (
            <span className="px-2 py-0.5 text-[10px] font-medium bg-violet-500/20 text-violet-400 rounded-full">
              LIVE
            </span>
          )}
        </div>
      </div>

      <div className="space-y-1.5 max-h-[350px] overflow-y-auto">
        {filtered.length === 0 ? (
          <p className="text-sm text-slate-500 text-center py-8">No activity yet. Trigger agents to see updates.</p>
        ) : (
          filtered.map((item, i) => (
            <div key={item.id || i}
              className={cn(
                "flex items-start gap-3 p-2.5 rounded-lg transition fade-in",
                item.isLive && "bg-violet-500/5 border border-violet-500/10",
                !item.isLive && "hover:bg-slate-800/30"
              )}>
              <div className={cn(
                "w-2 h-2 rounded-full mt-1.5 flex-shrink-0",
                item.status === "running" ? "bg-violet-500 pulse-dot" :
                item.status === "completed" ? "bg-emerald-500" :
                item.status === "failed" ? "bg-red-500" : "bg-slate-500"
              )} />
              <div className="min-w-0 flex-1">
                <p className="text-sm text-slate-300 truncate">{item.action}</p>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-[10px] text-slate-500">{item.agent_type?.replace(/_/g, " ")}</span>
                  {item.company_id && (
                    <>
                      <span className="text-[10px] text-slate-600">•</span>
                      <span className="text-[10px] text-slate-500">{item.company_id}</span>
                    </>
                  )}
                  <span className="text-[10px] text-slate-600">•</span>
                  <span className="text-[10px] text-slate-600">{item.created_at ? timeAgo(item.created_at) : ""}</span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
