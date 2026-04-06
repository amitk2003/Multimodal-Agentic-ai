"use client";
import { PortfolioOverview } from "@/components/dashboard/PortfolioOverview";
import { CompanyGrid } from "@/components/dashboard/CompanyGrid";
import { AgentStatusPanel } from "@/components/dashboard/AgentStatusPanel";
import { AgentActivityFeed } from "@/components/dashboard/AgentActivityFeed";
import { fetchApi } from "@/lib/utils";

export default function DashboardPage() {
  const handleRunClose = async () => {
    try {
      const result = await fetchApi("/api/agents/run-all?period=2026-01", { method: "POST" });
      console.log("Close workflow triggered:", result);
    } catch (e) {
      console.error("Failed to trigger close:", e);
    }
  };

  const handleSeedData = async () => {
    try {
      const result = await fetchApi("/api/seed", { method: "POST" });
      console.log("Database seeded:", result);
      window.location.reload();
    } catch (e) {
      console.error("Failed to seed:", e);
    }
  };

  return (
    <div className="space-y-6 max-w-[1600px] mx-auto">
      {/* Quick Actions */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Executive Dashboard</h1>
          <p className="text-sm text-slate-500 mt-1">Apex Capital Partners &bull; Month-End Close Orchestration</p>
        </div>
        <div className="flex gap-3">
          <button onClick={handleSeedData}
            className="px-4 py-2 text-sm font-medium text-slate-400 bg-slate-800 border border-slate-700 rounded-lg hover:bg-slate-700 transition">
            Seed Data
          </button>
          <button onClick={handleRunClose}
            className="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-violet-600 to-indigo-600 rounded-lg hover:from-violet-500 hover:to-indigo-500 transition shadow-lg shadow-violet-500/25">
            Run Full Close
          </button>
        </div>
      </div>

      {/* KPI Metrics */}
      <PortfolioOverview />

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Company Grid - 2 cols */}
        <div className="lg:col-span-2">
          <CompanyGrid />
        </div>

        {/* Agent Status - 1 col */}
        <div className="space-y-6">
          <AgentStatusPanel />
          <AgentActivityFeed maxItems={15} />
        </div>
      </div>
    </div>
  );
}
