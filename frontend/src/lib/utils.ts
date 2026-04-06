import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "http://localhost:8000";

export async function fetchApi<T = any>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${endpoint}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) throw new Error(`API Error: ${res.status}`);
  return res.json();
}

export function formatCurrency(amount: number): string {
  if (Math.abs(amount) >= 1_000_000) {
    return `$${(amount / 1_000_000).toFixed(1)}M`;
  }
  if (Math.abs(amount) >= 1_000) {
    return `$${(amount / 1_000).toFixed(0)}K`;
  }
  return `$${amount.toFixed(0)}`;
}

export function formatNumber(num: number): string {
  return new Intl.NumberFormat("en-US").format(num);
}

export function formatPercent(pct: number): string {
  return `${pct >= 0 ? "+" : ""}${pct.toFixed(1)}%`;
}

export function getStatusColor(status: string): string {
  switch (status) {
    case "completed": case "green": return "text-emerald-400";
    case "in_progress": case "running": case "yellow": return "text-amber-400";
    case "failed": case "error": case "red": return "text-red-400";
    default: return "text-slate-400";
  }
}

export function getStatusBg(status: string): string {
  switch (status) {
    case "completed": case "green": return "bg-emerald-500/10 border-emerald-500/20";
    case "in_progress": case "running": case "yellow": return "bg-amber-500/10 border-amber-500/20";
    case "failed": case "error": case "red": return "bg-red-500/10 border-red-500/20";
    default: return "bg-slate-500/10 border-slate-500/20";
  }
}

export function getTrafficLight(status: string): string {
  switch (status) {
    case "green": return "bg-emerald-500";
    case "yellow": return "bg-amber-500";
    case "red": return "bg-red-500";
    default: return "bg-slate-500";
  }
}

export function timeAgo(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}
