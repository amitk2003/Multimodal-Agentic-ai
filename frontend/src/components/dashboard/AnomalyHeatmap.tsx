"use client";
import { useState, useEffect } from "react";
import { fetchApi } from "@/lib/utils";
import { Activity } from "lucide-react";

interface HeatmapRow {
  company_id: string;
  company_name: string;
  overall_risk: number;
  scores: Record<string, number>;
}

const DIMENSION_LABELS: Record<string, string> = {
  revenue_recognition: "Revenue",
  trial_balance: "Trial Bal.",
  variance_analysis: "Variance",
  accrual_verification: "Accruals",
  intercompany_elimination: "Interco.",
  cash_flow: "Cash Flow",
};

function getHeatColor(score: number): string {
  if (score === 0) return "bg-emerald-500/20 text-emerald-300";
  if (score <= 25) return "bg-yellow-500/20 text-yellow-300";
  if (score <= 55) return "bg-orange-500/20 text-orange-300";
  return "bg-red-500/25 text-red-300";
}

function getHeatBorder(score: number): string {
  if (score === 0) return "border-emerald-500/20";
  if (score <= 25) return "border-yellow-500/20";
  if (score <= 55) return "border-orange-500/30";
  return "border-red-500/40";
}

export function AnomalyHeatmap() {
  const [heatmap, setHeatmap] = useState<HeatmapRow[]>([]);
  const [dimensions, setDimensions] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchApi("/api/anomaly-heatmap")
      .then((data) => {
        setHeatmap(data.heatmap || []);
        setDimensions(data.dimensions || []);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="glass-card p-5">
      <div className="flex items-center gap-2 mb-4">
        <Activity className="w-5 h-5 text-violet-400" />
        <div>
          <h3 className="text-sm font-semibold text-slate-100">Anomaly Heatmap</h3>
          <p className="text-xs text-slate-500">Risk score per company × financial dimension</p>
        </div>
        {/* Legend */}
        <div className="ml-auto flex items-center gap-2">
          {[
            { label: "Clean", cls: "bg-emerald-500/30" },
            { label: "Low", cls: "bg-yellow-500/30" },
            { label: "Med", cls: "bg-orange-500/30" },
            { label: "High", cls: "bg-red-500/30" },
          ].map((l) => (
            <div key={l.label} className="flex items-center gap-1">
              <div className={`w-3 h-3 rounded-sm ${l.cls}`} />
              <span className="text-xs text-slate-500">{l.label}</span>
            </div>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="shimmer h-48 rounded-xl" />
      ) : heatmap.length === 0 ? (
        <div className="flex items-center justify-center h-32 text-slate-500 text-sm">
          No data — seed the database first.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr>
                <th className="text-left text-slate-500 font-medium pb-2 pr-4 whitespace-nowrap">Company</th>
                {dimensions.map((d) => (
                  <th key={d} className="text-center text-slate-500 font-medium pb-2 px-1 whitespace-nowrap">
                    {DIMENSION_LABELS[d] || d}
                  </th>
                ))}
                <th className="text-center text-slate-500 font-medium pb-2 pl-2 whitespace-nowrap">Overall</th>
              </tr>
            </thead>
            <tbody className="space-y-1">
              {heatmap.map((row) => (
                <tr key={row.company_id} className="group">
                  <td className="pr-4 py-1 text-slate-300 font-medium whitespace-nowrap group-hover:text-slate-100 transition">
                    {row.company_name.length > 14 ? row.company_name.slice(0, 14) + "…" : row.company_name}
                  </td>
                  {dimensions.map((d) => {
                    const score = row.scores[d] ?? 0;
                    return (
                      <td key={d} className="px-1 py-1 text-center">
                        <div
                          className={`rounded-md px-2 py-1.5 font-bold border ${getHeatColor(score)} ${getHeatBorder(score)} transition hover:scale-110 cursor-default`}
                          title={`${DIMENSION_LABELS[d] || d}: ${score}/100`}
                        >
                          {score}
                        </div>
                      </td>
                    );
                  })}
                  <td className="pl-2 py-1 text-center">
                    <div
                      className={`rounded-md px-2 py-1.5 font-black border ${getHeatColor(row.overall_risk)} ${getHeatBorder(row.overall_risk)}`}
                    >
                      {row.overall_risk}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
