"use client";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { fetchApi, formatCurrency, cn, getStatusColor } from "@/lib/utils";
import { ArrowLeft, TrendingUp, TrendingDown, AlertTriangle, CheckCircle2 } from "lucide-react";
import Link from "next/link";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
  PieChart, Pie, Cell, LineChart, Line
} from "recharts";

const COLORS = ["#8b5cf6", "#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#ec4899", "#06b6d4", "#84cc16"];

export default function CompanyDetailPage() {
  const params = useParams();
  const companyId = params.id as string;

  const { data: company } = useQuery({
    queryKey: ["company", companyId],
    queryFn: () => fetchApi<any>(`/api/companies/${companyId}`),
  });

  const { data: financials } = useQuery({
    queryKey: ["financials", companyId],
    queryFn: () => fetchApi<any>(`/api/companies/${companyId}/financials?period=2026-01`),
  });

  const { data: logs } = useQuery({
    queryKey: ["company-logs", companyId],
    queryFn: () => fetchApi<any>(`/api/agents/logs?company_id=${companyId}&limit=20`),
  });

  const summary = financials?.summary;
  const incomeStatement = financials?.income_statement || [];

  // Build chart data
  const plChartData = incomeStatement
    .filter((l: any) => l.account_type !== "Revenue")
    .map((l: any) => ({
      name: l.account_name.length > 20 ? l.account_name.slice(0, 20) + "..." : l.account_name,
      actual: Math.abs(l.debit || 0),
      prior: Math.abs(l.prior_balance || 0),
    }))
    .slice(0, 8);

  // Revenue breakdown for pie chart
  const revenueData = incomeStatement
    .filter((l: any) => l.account_type === "Revenue")
    .map((l: any, i: number) => ({
      name: l.account_name,
      value: Math.abs(l.credit || 0),
      color: COLORS[i % COLORS.length],
    }));

  return (
    <div className="space-y-6 max-w-[1600px] mx-auto">
      {/* Back Button + Header */}
      <div className="flex items-center gap-4">
        <Link href="/" className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 transition">
          <ArrowLeft className="w-4 h-4 text-slate-400" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-slate-100">{company?.name || companyId}</h1>
          <p className="text-sm text-slate-500">{company?.industry} &bull; {company?.employees} employees</p>
        </div>
        <span className={cn(
          "ml-auto px-3 py-1 rounded-lg text-xs font-medium capitalize border",
          company?.close_status === "completed" ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" :
          company?.close_status === "in_progress" ? "bg-amber-500/10 text-amber-400 border-amber-500/20" :
          "bg-slate-500/10 text-slate-400 border-slate-500/20"
        )}>{company?.close_status?.replace("_", " ") || "Not Started"}</span>
      </div>

      {/* Financial Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "Revenue", value: summary.revenue, color: "text-violet-400" },
            { label: "Gross Profit", value: summary.gross_profit, subtitle: `${summary.gross_margin}% margin`, color: "text-blue-400" },
            { label: "EBITDA", value: summary.ebitda, subtitle: `${summary.ebitda_margin}% margin`, color: "text-emerald-400" },
            { label: "COGS", value: summary.cogs, color: "text-amber-400" },
          ].map((m, i) => (
            <div key={i} className="glass-card p-4 fade-in">
              <p className="text-xs text-slate-500 uppercase tracking-wider">{m.label}</p>
              <p className={cn("text-xl font-bold mt-1", m.color)}>{formatCurrency(m.value)}</p>
              {m.subtitle && <p className="text-xs text-slate-500 mt-0.5">{m.subtitle}</p>}
            </div>
          ))}
        </div>
      )}

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Expense Comparison Chart */}
        <div className="glass-card p-5">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Expenses: Current vs Prior Period</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={plChartData} barGap={2}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#64748b' }} />
              <YAxis tick={{ fontSize: 10, fill: '#64748b' }} tickFormatter={(v) => `$${(v/1000).toFixed(0)}K`} />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8, fontSize: 12 }} />
              <Bar dataKey="actual" fill="#8b5cf6" radius={[4, 4, 0, 0]} name="Current" />
              <Bar dataKey="prior" fill="#334155" radius={[4, 4, 0, 0]} name="Prior" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Revenue Breakdown */}
        <div className="glass-card p-5">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Revenue Breakdown</h3>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie data={revenueData} cx="50%" cy="50%" innerRadius={60} outerRadius={100} dataKey="value" paddingAngle={3}>
                {revenueData.map((entry: any, idx: number) => (
                  <Cell key={idx} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8, fontSize: 12 }}
                formatter={(value: any) => formatCurrency(Number(value))} />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-3 justify-center mt-2">
            {revenueData.map((r: any, i: number) => (
              <div key={i} className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full" style={{ background: r.color }} />
                <span className="text-[11px] text-slate-400">{r.name}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Income Statement Table */}
      <div className="glass-card p-5">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">Income Statement - January 2026</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left py-2 px-3 text-xs text-slate-500 font-medium">Account</th>
                <th className="text-right py-2 px-3 text-xs text-slate-500 font-medium">Code</th>
                <th className="text-right py-2 px-3 text-xs text-slate-500 font-medium">Current</th>
                <th className="text-right py-2 px-3 text-xs text-slate-500 font-medium">Prior</th>
                <th className="text-right py-2 px-3 text-xs text-slate-500 font-medium">Change</th>
              </tr>
            </thead>
            <tbody>
              {incomeStatement.map((line: any, i: number) => (
                <tr key={i} className="border-b border-slate-800/50 hover:bg-slate-800/30 transition">
                  <td className="py-2 px-3 text-slate-300">{line.account_name}</td>
                  <td className="py-2 px-3 text-right text-slate-500">{line.account_code}</td>
                  <td className="py-2 px-3 text-right text-slate-300 font-medium">
                    {formatCurrency(Math.abs(line.debit || line.credit || 0))}
                  </td>
                  <td className="py-2 px-3 text-right text-slate-500">
                    {line.prior_balance ? formatCurrency(Math.abs(line.prior_balance)) : "—"}
                  </td>
                  <td className={cn("py-2 px-3 text-right font-medium",
                    (line.change_pct || 0) > 0 ? "text-red-400" : (line.change_pct || 0) < 0 ? "text-emerald-400" : "text-slate-500"
                  )}>
                    {line.change_pct ? `${line.change_pct > 0 ? "+" : ""}${line.change_pct}%` : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Agent Audit Trail */}
      <div className="glass-card p-5">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">Agent Audit Trail</h3>
        <div className="space-y-2">
          {(logs?.logs || []).map((log: any) => (
            <div key={log.id} className="flex items-center gap-3 p-2.5 rounded-lg bg-slate-800/30">
              {log.status === "completed" ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
              ) : log.status === "failed" ? (
                <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0" />
              ) : (
                <div className="w-4 h-4 rounded-full border-2 border-slate-600 flex-shrink-0" />
              )}
              <div className="flex-1 min-w-0">
                <p className="text-sm text-slate-300 truncate">{log.action}</p>
                <p className="text-[10px] text-slate-500">{log.agent_type?.replace(/_/g, " ")} &bull; {log.created_at}</p>
              </div>
              {log.duration_ms && (
                <span className="text-[11px] text-slate-500">{log.duration_ms}ms</span>
              )}
            </div>
          ))}
          {(!logs?.logs || logs.logs.length === 0) && (
            <p className="text-sm text-slate-500 text-center py-4">No agent activity for this company yet.</p>
          )}
        </div>
      </div>
    </div>
  );
}
