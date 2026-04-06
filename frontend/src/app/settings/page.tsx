"use client";
import { useQuery } from "@tanstack/react-query";
import { fetchApi } from "@/lib/utils";
import { Settings as SettingsIcon, Save, Bell, Gauge, Clock, Mail } from "lucide-react";
import { useState } from "react";

export default function SettingsPage() {
  const { data: settings } = useQuery({
    queryKey: ["settings"],
    queryFn: () => fetchApi<any>("/api/settings"),
  });

  const [variancePct, setVariancePct] = useState(settings?.variance_threshold_pct || 10);
  const [varianceAmt, setVarianceAmt] = useState(settings?.variance_threshold_amt || 50000);

  return (
    <div className="space-y-6 max-w-[800px] mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Settings</h1>
        <p className="text-sm text-slate-500 mt-1">Configure agent thresholds, scheduling, and notifications</p>
      </div>

      {/* Variance Thresholds */}
      <div className="glass-card p-6">
        <div className="flex items-center gap-2 mb-4">
          <Gauge className="w-5 h-5 text-violet-400" />
          <h3 className="text-lg font-semibold text-slate-200">Variance Thresholds</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1">Percentage Threshold (%)</label>
            <input type="number" value={variancePct}
              onChange={(e) => setVariancePct(Number(e.target.value))}
              className="w-full bg-slate-800 border border-slate-700 text-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-violet-500" />
            <p className="text-xs text-slate-600 mt-1">Variances above this % are flagged as material</p>
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">Amount Threshold ($)</label>
            <input type="number" value={varianceAmt}
              onChange={(e) => setVarianceAmt(Number(e.target.value))}
              className="w-full bg-slate-800 border border-slate-700 text-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-violet-500" />
            <p className="text-xs text-slate-600 mt-1">Variances above this $ amount are flagged</p>
          </div>
        </div>
      </div>

      {/* Scheduling */}
      <div className="glass-card p-6">
        <div className="flex items-center gap-2 mb-4">
          <Clock className="w-5 h-5 text-amber-400" />
          <h3 className="text-lg font-semibold text-slate-200">Autonomous Scheduling</h3>
        </div>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 rounded-lg bg-slate-800/30">
            <div>
              <p className="text-sm text-slate-300">Daily Close Check</p>
              <p className="text-xs text-slate-500">Runs every day at configured hour</p>
            </div>
            <span className="text-sm text-slate-400">{settings?.daily_close_hour || 9}:00 UTC</span>
          </div>
          <div className="flex items-center justify-between p-3 rounded-lg bg-slate-800/30">
            <div>
              <p className="text-sm text-slate-300">Monitoring Interval</p>
              <p className="text-xs text-slate-500">Data change detection frequency</p>
            </div>
            <span className="text-sm text-slate-400">{settings?.monitoring_interval_minutes || 5} min</span>
          </div>
          <div className="flex items-center justify-between p-3 rounded-lg bg-slate-800/30">
            <div>
              <p className="text-sm text-slate-300">Max Agent Retries</p>
              <p className="text-xs text-slate-500">Retry count with exponential backoff</p>
            </div>
            <span className="text-sm text-slate-400">{settings?.max_agent_retries || 3}</span>
          </div>
        </div>
      </div>

      {/* Email */}
      <div className="glass-card p-6">
        <div className="flex items-center gap-2 mb-4">
          <Mail className="w-5 h-5 text-blue-400" />
          <h3 className="text-lg font-semibold text-slate-200">Email Notifications</h3>
        </div>
        <div className="flex items-center justify-between p-3 rounded-lg bg-slate-800/30">
          <div>
            <p className="text-sm text-slate-300">Email Delivery</p>
            <p className="text-xs text-slate-500">Requires Resend API key in .env</p>
          </div>
          <span className={`px-3 py-1 rounded-lg text-xs font-medium ${settings?.email_enabled ? "bg-emerald-500/10 text-emerald-400" : "bg-slate-500/10 text-slate-400"}`}>
            {settings?.email_enabled ? "Enabled" : "Preview Mode"}
          </span>
        </div>
      </div>

      {/* LLM Config */}
      <div className="glass-card p-6">
        <div className="flex items-center gap-2 mb-4">
          <SettingsIcon className="w-5 h-5 text-indigo-400" />
          <h3 className="text-lg font-semibold text-slate-200">LLM Configuration</h3>
        </div>
        <div className="flex items-center justify-between p-3 rounded-lg bg-slate-800/30">
          <div>
            <p className="text-sm text-slate-300">Active Model</p>
            <p className="text-xs text-slate-500">Used for all agent reasoning</p>
          </div>
          <span className="px-3 py-1 rounded-lg text-xs font-medium bg-violet-500/10 text-violet-400">
            {settings?.llm_model || "claude-sonnet-4-20250514"}
          </span>
        </div>
      </div>
    </div>
  );
}
