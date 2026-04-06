"use client";
import { useState, useEffect } from "react";
import { PortfolioOverview } from "@/components/dashboard/PortfolioOverview";
import { CompanyGrid } from "@/components/dashboard/CompanyGrid";
import { AgentStatusPanel } from "@/components/dashboard/AgentStatusPanel";
import { AgentActivityFeed } from "@/components/dashboard/AgentActivityFeed";
import { fetchApi, cn } from "@/lib/utils";
import { Loader2, AlertCircle, Play, Database, CheckCircle2 } from "lucide-react";

export default function DashboardPage() {
  const [isSeeding, setIsSeeding] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [hasData, setHasData] = useState(true);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  useEffect(() => {
    // Check if there's any data
    fetchApi("/api/companies").then(res => {
      setHasData(res.total > 0);
    }).catch(() => setHasData(false));
  }, []);

  const handleRunClose = async () => {
    if (!hasData) {
      setStatusMessage("Error: You must seed data before running a close workflow.");
      return;
    }
    
    setIsRunning(true);
    setStatusMessage("Triggering month-end close workflow...");
    try {
      const result = await fetchApi("/api/agents/run-all?period=2026-01", { method: "POST" });
      console.log("Close workflow triggered:", result);
      setStatusMessage("Success: Full close workflow initiated!");
      setTimeout(() => setStatusMessage(null), 5000);
    } catch (e) {
      console.error("Failed to trigger close:", e);
      setStatusMessage("Error: Failed to initiate workflow.");
    } finally {
      setIsRunning(false);
    }
  };

  const handleSeedData = async () => {
    setIsSeeding(true);
    setStatusMessage("Seeding database with sample portfolios...");
    try {
      const result = await fetchApi("/api/seed", { method: "POST" });
      console.log("Database seeded:", result);
      setHasData(true);
      setStatusMessage("Success: Database seeded successfully!");
      // Short delay for the user to see the success message
      setTimeout(() => window.location.reload(), 1500);
    } catch (e) {
      console.error("Failed to seed:", e);
      setStatusMessage("Error: Failed to seed data.");
      setIsSeeding(false);
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
          <button 
            onClick={handleSeedData}
            disabled={isSeeding || isRunning}
            className={cn(
              "flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition",
              "text-slate-400 bg-slate-800 border border-slate-700 hover:bg-slate-700",
              (isSeeding || isRunning) && "opacity-50 cursor-not-allowed"
            )}>
            {isSeeding ? <Loader2 className="w-4 h-4 animate-spin" /> : <Database className="w-4 h-4" />}
            Seed Data
          </button>
          <button 
            onClick={handleRunClose}
            disabled={isSeeding || isRunning}
            className={cn(
              "flex items-center gap-2 px-4 py-2 text-sm font-medium text-white rounded-lg transition shadow-lg",
              "bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 shadow-violet-500/25",
              (isSeeding || isRunning) && "opacity-50 cursor-not-allowed"
            )}>
            {isRunning ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            Run Full Close
          </button>
        </div>
      </div>

      {statusMessage && (
        <div className={cn(
          "flex items-center gap-3 p-4 rounded-xl text-sm font-medium animate-in fade-in slide-in-from-top-4",
          statusMessage.includes("Error") ? "bg-red-500/10 text-red-400 border border-red-500/20" : 
          statusMessage.includes("Success") ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" :
          "bg-violet-500/10 text-violet-400 border border-violet-500/20 shadow-lg shadow-violet-500/10"
        )}>
          {statusMessage.includes("Error") ? <AlertCircle className="w-5 h-5" /> : 
           statusMessage.includes("Success") ? <CheckCircle2 className="w-5 h-5" /> :
           <Loader2 className="w-5 h-5 animate-spin" />}
          {statusMessage}
        </div>
      )}

      {!hasData && !statusMessage && (
        <div className="flex items-center gap-4 p-5 bg-amber-500/10 border border-amber-500/20 rounded-2xl">
          <div className="w-12 h-12 rounded-full bg-amber-500/20 flex items-center justify-center flex-shrink-0">
            <AlertCircle className="w-6 h-6 text-amber-500" />
          </div>
          <div>
            <h4 className="text-amber-500 font-semibold">Database is empty</h4>
            <p className="text-sm text-slate-400 mt-0.5">Please click "Seed Data" to populate portfolio companies and financial records before starting the orchestration.</p>
          </div>
        </div>
      )}

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
