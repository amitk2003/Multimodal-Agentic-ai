"use client";
import { useQuery } from "@tanstack/react-query";
import { fetchApi, formatCurrency, cn } from "@/lib/utils";
import { TrendingUp, DollarSign, Building2, AlertTriangle, CheckCircle2, Clock } from "lucide-react";

interface PortfolioData {
  portfolio: {
    total_revenue: number;
    total_ebitda: number;
    total_companies: number;
    companies_completed: number;
    companies_in_progress: number;
    overall_progress: number;
  };
  unread_notifications: number;
}

export function PortfolioOverview() {
  const { data, isLoading } = useQuery<PortfolioData>({
    queryKey: ["dashboard"],
    queryFn: () => fetchApi("/api/dashboard/summary?period=2026-01"),
  });

  if (isLoading || !data) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="glass-card p-5 h-28 shimmer" />
        ))}
      </div>
    );
  }

  const p = data.portfolio;

  const metrics = [
    {
      label: "Total Revenue",
      value: formatCurrency(p.total_revenue),
      icon: DollarSign,
      color: "from-violet-500 to-indigo-600",
      textColor: "text-violet-400",
    },
    {
      label: "Total EBITDA",
      value: formatCurrency(p.total_ebitda),
      icon: TrendingUp,
      color: "from-emerald-500 to-teal-600",
      textColor: "text-emerald-400",
    },
    {
      label: "Close Progress",
      value: `${p.overall_progress.toFixed(0)}%`,
      icon: p.overall_progress >= 100 ? CheckCircle2 : Clock,
      color: "from-amber-500 to-orange-600",
      textColor: "text-amber-400",
      subtitle: `${p.companies_completed}/${p.total_companies} done`,
    },
    {
      label: "Open Alerts",
      value: data.unread_notifications.toString(),
      icon: AlertTriangle,
      color: data.unread_notifications > 0 ? "from-red-500 to-rose-600" : "from-slate-500 to-slate-600",
      textColor: data.unread_notifications > 0 ? "text-red-400" : "text-slate-400",
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {metrics.map((m, i) => (
        <div key={i} className="glass-card p-5 card-hover fade-in" style={{ animationDelay: `${i * 50}ms` }}>
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">{m.label}</p>
              <p className={cn("text-2xl font-bold mt-1", m.textColor)}>{m.value}</p>
              {m.subtitle && <p className="text-xs text-slate-500 mt-1">{m.subtitle}</p>}
            </div>
            <div className={cn("w-10 h-10 rounded-xl bg-gradient-to-br flex items-center justify-center", m.color)}>
              <m.icon className="w-5 h-5 text-white" />
            </div>
          </div>

          {/* Progress bar for close progress */}
          {m.label === "Close Progress" && (
            <div className="mt-3 w-full bg-slate-700/50 rounded-full h-1.5">
              <div
                className="h-1.5 rounded-full bg-gradient-to-r from-amber-500 to-orange-500 transition-all duration-1000"
                style={{ width: `${Math.min(p.overall_progress, 100)}%` }}
              />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
