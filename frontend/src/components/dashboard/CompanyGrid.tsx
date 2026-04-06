"use client";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { fetchApi, formatCurrency, cn, getTrafficLight } from "@/lib/utils";
import { ArrowUpRight, AlertCircle, CheckCircle2, Clock, Loader2 } from "lucide-react";

interface CompanyData {
  id: string;
  name: string;
  industry: string;
  revenue: number;
  ebitda: number;
  cash: number;
  margin: number;
  close_status: string;
  close_progress: number;
  open_issues: number;
  traffic_light: string;
}

export function CompanyGrid() {
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => fetchApi<any>("/api/dashboard/summary?period=2026-01"),
  });

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(8)].map((_, i) => (
          <div key={i} className="glass-card p-5 h-48 shimmer" />
        ))}
      </div>
    );
  }

  const companies: CompanyData[] = data?.companies || [];

  return (
    <div>
      <h3 className="text-lg font-semibold text-slate-200 mb-4">Portfolio Companies</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {companies.map((company, i) => (
          <Link key={company.id} href={`/companies/${company.id}`}>
            <div className="glass-card p-5 card-hover fade-in cursor-pointer" style={{ animationDelay: `${i * 30}ms` }}>
              {/* Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className={cn("w-2.5 h-2.5 rounded-full", getTrafficLight(company.traffic_light))} />
                  <h4 className="text-sm font-semibold text-slate-200 truncate max-w-[140px]">{company.name}</h4>
                </div>
                <ArrowUpRight className="w-4 h-4 text-slate-500" />
              </div>

              {/* Industry Badge */}
              <span className="inline-block px-2 py-0.5 text-[10px] font-medium text-slate-400 bg-slate-800 rounded-md mb-3">
                {company.industry}
              </span>

              {/* Metrics */}
              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-500">Revenue</span>
                  <span className="text-slate-300 font-medium">{formatCurrency(company.revenue)}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-slate-500">EBITDA</span>
                  <span className={cn("font-medium", company.ebitda >= 0 ? "text-emerald-400" : "text-red-400")}>
                    {formatCurrency(company.ebitda)}
                  </span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-slate-500">Margin</span>
                  <span className="text-slate-300 font-medium">{company.margin}%</span>
                </div>
              </div>

              {/* Progress & Status */}
              <div className="mt-3 pt-3 border-t border-slate-700/50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    {company.close_status === "completed" ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    ) : company.close_status === "in_progress" ? (
                      <Loader2 className="w-3.5 h-3.5 text-amber-400 animate-spin" />
                    ) : (
                      <Clock className="w-3.5 h-3.5 text-slate-500" />
                    )}
                    <span className="text-[11px] text-slate-400 capitalize">{company.close_status.replace("_", " ")}</span>
                  </div>
                  {company.open_issues > 0 && (
                    <div className="flex items-center gap-1 text-amber-400">
                      <AlertCircle className="w-3 h-3" />
                      <span className="text-[11px] font-medium">{company.open_issues}</span>
                    </div>
                  )}
                </div>
                <div className="mt-2 w-full bg-slate-700/50 rounded-full h-1">
                  <div
                    className={cn(
                      "h-1 rounded-full transition-all duration-700",
                      company.close_progress >= 100
                        ? "bg-emerald-500"
                        : company.close_progress > 50
                        ? "bg-amber-500"
                        : "bg-violet-500"
                    )}
                    style={{ width: `${Math.min(company.close_progress, 100)}%` }}
                  />
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
