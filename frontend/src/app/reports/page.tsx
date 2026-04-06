"use client";
import { useQuery } from "@tanstack/react-query";
import { fetchApi, cn, timeAgo, formatCurrency } from "@/lib/utils";
import { FileBarChart, Download, Eye, Clock } from "lucide-react";

export default function ReportsPage() {
  const { data: reportsData } = useQuery({
    queryKey: ["reports"],
    queryFn: () => fetchApi<any>("/api/reports"),
  });

  const { data: notifData } = useQuery({
    queryKey: ["notifications"],
    queryFn: () => fetchApi<any>("/api/notifications?limit=30"),
  });

  const reports = reportsData?.reports || [];
  const notifications = notifData?.notifications || [];

  const handleExport = async (companyId: string) => {
    window.open(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/export/trial-balance/${companyId}?period=2026-01`, "_blank");
  };

  const COMPANIES = [
    "techforge_saas", "precisionmfg_inc", "retailco", "healthservices_plus",
    "logisticspro", "industrialsupply_co", "dataanalytics_corp", "ecopackaging_ltd"
  ];

  return (
    <div className="space-y-6 max-w-[1600px] mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Reports & Exports</h1>
        <p className="text-sm text-slate-500 mt-1">Generated reports, exports, and notifications</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Reports */}
        <div className="glass-card p-5">
          <div className="flex items-center gap-2 mb-4">
            <FileBarChart className="w-4 h-4 text-violet-400" />
            <h3 className="text-lg font-semibold text-slate-200">Generated Reports</h3>
          </div>
          <div className="space-y-2">
            {reports.length === 0 ? (
              <p className="text-sm text-slate-500 text-center py-8">No reports generated yet. Run the close workflow first.</p>
            ) : (
              reports.map((report: any) => (
                <div key={report.id} className="flex items-center justify-between p-3 rounded-lg bg-slate-800/30 hover:bg-slate-800/50 transition">
                  <div className="flex items-center gap-3">
                    <FileBarChart className="w-4 h-4 text-indigo-400" />
                    <div>
                      <p className="text-sm text-slate-300">{report.title}</p>
                      <p className="text-[11px] text-slate-500">{report.report_type} &bull; {report.period}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] text-slate-500">{report.created_at ? timeAgo(report.created_at) : ""}</span>
                    <button className="p-1.5 rounded-lg text-slate-400 hover:text-violet-400 hover:bg-violet-500/10 transition">
                      <Eye className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Exports */}
        <div className="glass-card p-5">
          <div className="flex items-center gap-2 mb-4">
            <Download className="w-4 h-4 text-emerald-400" />
            <h3 className="text-lg font-semibold text-slate-200">Export Data</h3>
          </div>
          <p className="text-sm text-slate-500 mb-4">Download trial balance data as CSV for each company.</p>
          <div className="space-y-2">
            {COMPANIES.map((companyId) => (
              <button key={companyId} onClick={() => handleExport(companyId)}
                className="w-full flex items-center justify-between p-3 rounded-lg bg-slate-800/30 hover:bg-slate-800/50 transition text-left">
                <span className="text-sm text-slate-300">{companyId.replace(/_/g, " ")}</span>
                <Download className="w-4 h-4 text-slate-400" />
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Notification Log */}
      <div className="glass-card p-5">
        <h3 className="text-lg font-semibold text-slate-200 mb-4">Notification History</h3>
        <div className="space-y-2 max-h-[400px] overflow-y-auto">
          {notifications.length === 0 ? (
            <p className="text-sm text-slate-500 text-center py-8">No notifications yet.</p>
          ) : (
            notifications.map((n: any) => (
              <div key={n.id} className={cn(
                "p-3 rounded-lg border transition",
                n.is_read ? "bg-slate-800/20 border-slate-800" : "bg-slate-800/40 border-slate-700"
              )}>
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm text-slate-300 font-medium">{n.title}</p>
                    <p className="text-xs text-slate-500 mt-0.5">{n.message}</p>
                  </div>
                  <span className={cn("px-2 py-0.5 rounded text-[11px] font-medium",
                    n.severity === "error" || n.severity === "critical" ? "bg-red-500/10 text-red-400" :
                    n.severity === "warning" ? "bg-amber-500/10 text-amber-400" :
                    "bg-blue-500/10 text-blue-400"
                  )}>{n.severity}</span>
                </div>
                <p className="text-[10px] text-slate-600 mt-1">{n.agent_type?.replace(/_/g, " ")} &bull; {n.created_at ? timeAgo(n.created_at) : ""}</p>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
