"use client";
import { useState, useEffect } from "react";
import { fetchApi } from "@/lib/utils";
import { TrendingUp, TrendingDown, Shield } from "lucide-react";

interface CompanyRisk {
  company_id: string;
  company_name: string;
  risk_score: number;
  risk_level: "low" | "medium" | "high" | "critical";
  breakdown: {
    critical_issues: number;
    error_issues: number;
    warning_issues: number;
    close_progress: number;
  };
}

const RISK_CONFIG = {
  low:      { color: "text-emerald-400", bg: "bg-emerald-500/10", bar: "bg-emerald-500" },
  medium:   { color: "text-yellow-400",  bg: "bg-yellow-500/10",  bar: "bg-yellow-500"  },
  high:     { color: "text-orange-400",  bg: "bg-orange-500/10",  bar: "bg-orange-500"  },
  critical: { color: "text-red-400",     bg: "bg-red-500/10",     bar: "bg-red-500"     },
};

export function RiskScorePanel() {
  const [data, setData] = useState<{ portfolio_risk_score: number; portfolio_risk_level: string; companies: CompanyRisk[] } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchApi("/api/risk-score")
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="glass-card p-5 shimmer h-48 rounded-xl" />;
  if (!data) return null;

  const portfolioConfig = RISK_CONFIG[data.portfolio_risk_level as keyof typeof RISK_CONFIG] || RISK_CONFIG.low;

  return (
    <div className="glass-card p-5">
      <div className="flex items-center gap-2 mb-4">
        <Shield className="w-5 h-5 text-indigo-400" />
        <div>
          <h3 className="text-sm font-semibold text-slate-100">Portfolio Risk Score</h3>
          <p className="text-xs text-slate-500">Composite financial risk across all companies</p>
        </div>
        <div className={`ml-auto px-3 py-1 rounded-full text-xs font-bold uppercase ${portfolioConfig.bg} ${portfolioConfig.color}`}>
          {data.portfolio_risk_level}
        </div>
      </div>

      {/* Portfolio Risk Gauge */}
      <div className="mb-5 p-4 bg-slate-900/50 rounded-xl border border-slate-700/50">
        <div className="flex items-end justify-between mb-2">
          <span className="text-xs text-slate-500">Portfolio Risk</span>
          <span className={`text-3xl font-black ${portfolioConfig.color}`}>{data.portfolio_risk_score}</span>
        </div>
        <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-700 ${portfolioConfig.bar}`}
            style={{ width: `${data.portfolio_risk_score}%` }}
          />
        </div>
        <div className="flex justify-between mt-1">
          <span className="text-xs text-slate-600">Low</span>
          <span className="text-xs text-slate-600">Critical</span>
        </div>
      </div>

      {/* Per-company scores */}
      <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
        {data.companies.map((c) => {
          const cfg = RISK_CONFIG[c.risk_level] || RISK_CONFIG.low;
          return (
            <div key={c.company_id} className="flex items-center gap-3 group">
              <div className="w-24 text-xs text-slate-400 truncate group-hover:text-slate-200 transition">
                {c.company_name.split(" ")[0]}
              </div>
              <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${cfg.bar}`}
                  style={{ width: `${c.risk_score}%` }}
                />
              </div>
              <div className="w-8 text-right">
                <span className={`text-xs font-bold ${cfg.color}`}>{c.risk_score}</span>
              </div>
              <div className="w-16 flex items-center gap-1 justify-end">
                {c.breakdown.critical_issues > 0 && (
                  <span className="text-xs bg-red-500/10 text-red-400 px-1 rounded">{c.breakdown.critical_issues}C</span>
                )}
                {c.breakdown.error_issues > 0 && (
                  <span className="text-xs bg-orange-500/10 text-orange-400 px-1 rounded">{c.breakdown.error_issues}E</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
