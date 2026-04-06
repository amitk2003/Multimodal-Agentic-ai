"use client";
import { useEffect, useRef, useState, useCallback } from "react";
import { io, Socket } from "socket.io-client";
import { WS_URL } from "@/lib/utils";

export interface AgentUpdate {
  type: string;
  agent_type: string;
  agent_name: string;
  company_id?: string;
  status: string;
  message: string;
  timestamp: string;
  duration_ms?: number;
  findings_count?: number;
}

export function useWebSocket() {
  const socketRef = useRef<Socket | null>(null);
  const [connected, setConnected] = useState(false);
  const [updates, setUpdates] = useState<AgentUpdate[]>([]);
  const [lastUpdate, setLastUpdate] = useState<AgentUpdate | null>(null);

  useEffect(() => {
    const socket = io(WS_URL, {
      transports: ["websocket", "polling"],
      reconnection: true,
      reconnectionDelay: 2000,
      reconnectionAttempts: 10,
    });

    socket.on("connect", () => {
      setConnected(true);
      console.log("[WS] Connected to server");
    });

    socket.on("disconnect", () => {
      setConnected(false);
      console.log("[WS] Disconnected");
    });

    socket.on("agent_update", (update: AgentUpdate) => {
      setLastUpdate(update);
      setUpdates((prev) => [update, ...prev].slice(0, 200));
    });

    socket.on("connection_established", (data) => {
      console.log("[WS] Server greeting:", data.message);
    });

    socketRef.current = socket;

    return () => {
      socket.disconnect();
    };
  }, []);

  const triggerAgent = useCallback((agentType: string, companyId?: string, period: string = "2026-01") => {
    socketRef.current?.emit("trigger_agent", {
      agent_type: agentType,
      company_id: companyId,
      period,
    });
  }, []);

  return { connected, updates, lastUpdate, triggerAgent };
}
