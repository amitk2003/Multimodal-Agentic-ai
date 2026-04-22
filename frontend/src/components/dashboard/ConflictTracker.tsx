"use client";
import { useState, useEffect } from "react";
import { fetchApi, timeAgo } from "@/lib/utils";
import { AlertTriangle, ShieldAlert, CheckCircle2, RefreshCw, Mail } from "lucide-react";

interface Conflict {
  id: number;
  title: string;
  message: string;
  company_name: string;
  severity: string;
  conflict_score: number;
  resolution_status: string;
  agent_type: string;
  created_at: string;
}

export function ConflictTracker() {
  const [conflicts, setConflicts] = useState<Conflict[]>([]);
  const [loading, setLoading] = useState(true);
  const [digestSending, setDigestSending] = useState(false);
  const [digestMsg, setDigestMsg] = useState<string | null>(null);
  const [stats, setStats] = useState({ critical_count: 0, error_count: 0, total: 0 });

  const load = async () => {
    setLoading(true);
    try {
      const data = await fetchApi("/api/conflicts");
      setConflicts(data.conflicts || []);
      setStats({ critical_count: data.critical_count, error_count: data.error_count, total: data.total });
    } catch (e) {
      console.error("Failed to load conflicts:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleDigest = async () => {
    setDigestSending(true);
    setDigestMsg(null);
    try {
      const res = await fetchApi("/api/smart-digest", { method: "POST" });
      setDigestMsg(res.sent ? `✓ Smart digest sent (${res.alerts_included} alerts)` : "No unread alerts to send.");
      await load();
    } catch {
      setDigestMsg("✗ Failed to send digest");
    } finally {
      setDigestSending(false);
      setTimeout(() => setDigestMsg(null), 5000);
    }
  };

  const severityConfig: Record<string, { color: string; bg: string; icon: React.ReactNode }> = {
    critical: { color: "text-red-400", bg: "bg-red-500/10 border-red-500/30", icon: <ShieldAlert className="w-4 h-4 text-red-400" /> },
    error: { color: "text-orange-400", bg: "bg-orange-500/10 border-orange-500/30", icon: <AlertTriangle className="w-4 h-4 text-orange-400" /> },
  };

  return (
    <div className="glass-card p-5">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="relative">
            <ShieldAlert className="w-5 h-5 text-red-400" />
            {stats.critical_count > 0 && (
              <span className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full pulse-dot" />
            )}
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-100">Conflict Tracker</h3>
            <p className="text-xs text-slate-500">Real-time transaction conflicts</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleDigest}
            disabled={digestSending}
            title="Send Smart Alert Digest Email"
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-violet-300 bg-violet-500/10 border border-violet-500/20 rounded-lg hover:bg-violet-500/20 transition disabled:opacity-50"
          >
            <Mail className="w-3 h-3" />
            {digestSending ? "Sending…" : "Smart Digest"}
          </button>
          <button onClick={load} className="p-1.5 text-slate-400 hover:text-slate-200 transition">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 text-center">
          <p className="text-xl font-bold text-red-400">{stats.critical_count}</p>
          <p className="text-xs text-slate-500 mt-0.5">Critical</p>
        </div>
        <div className="bg-orange-500/10 border border-orange-500/20 rounded-lg p-3 text-center">
          <p className="text-xl font-bold text-orange-400">{stats.error_count}</p>
          <p className="text-xs text-slate-500 mt-0.5">Errors</p>
        </div>
        <div className="bg-slate-500/10 border border-slate-500/20 rounded-lg p-3 text-center">
          <p className="text-xl font-bold text-slate-300">{stats.total}</p>
          <p className="text-xs text-slate-500 mt-0.5">Total</p>
        </div>
      </div>

      {digestMsg && (
        <div className="mb-3 px-3 py-2 bg-violet-500/10 border border-violet-500/20 rounded-lg text-xs text-violet-300">
          {digestMsg}
        </div>
      )}

      {/* Conflict List */}
      <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
        {loading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="shimmer h-16 rounded-lg" />
          ))
        ) : conflicts.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-10 text-center">
            <CheckCircle2 className="w-8 h-8 text-emerald-500 mb-2" />
            <p className="text-sm text-slate-400">No active conflicts</p>
            <p className="text-xs text-slate-600 mt-1">All intercompany transactions are balanced</p>
          </div>
        ) : (
          conflicts.map((c) => {
            const cfg = severityConfig[c.severity] || severityConfig.error;
            return (
              <div key={c.id} className={`flex items-start gap-3 p-3 rounded-xl border ${cfg.bg} transition hover:brightness-110`}>
                <div className="mt-0.5 flex-shrink-0">{cfg.icon}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <p className={`text-xs font-semibold truncate ${cfg.color}`}>{c.title}</p>
                    <span className="text-xs text-slate-600 whitespace-nowrap flex-shrink-0">{timeAgo(c.created_at)}</span>
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5 line-clamp-2">{c.message}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs text-slate-600 bg-slate-800 px-1.5 py-0.5 rounded">{c.company_name}</span>
                    <span className="text-xs text-slate-600 bg-slate-800 px-1.5 py-0.5 rounded">{c.agent_type?.replace(/_/g, ' ')}</span>
                    {c.resolution_status === "open" && (
                      <span className="text-xs text-red-400 bg-red-500/10 px-1.5 py-0.5 rounded">OPEN</span>
                    )}
                  </div>
                </div>
                <div className="flex-shrink-0 text-right">
                  <span className={`text-lg font-black ${c.conflict_score >= 90 ? "text-red-400" : "text-orange-400"}`}>
                    {c.conflict_score}
                  </span>
                  <p className="text-xs text-slate-600">score</p>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
