"use client";

import React, { useState, useEffect, useRef } from "react";
import { socketManager } from "@/lib/websocket";
import { MCPServerMap, MCPServerConfig } from "@/lib/types";
import { Puzzle, ChevronDown, ChevronUp, AlertCircle, CheckCircle2, AlertTriangle, X, Power, RefreshCw } from "lucide-react";

export const SkillMatrixDropdown: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [servers, setServers] = useState<MCPServerMap>({});
  const [filter, setFilter] = useState<"all" | "ok" | "warn" | "err">("all");
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const unsub = socketManager.onMcpServers((data) => {
      setServers(data || {});
    });
    socketManager.requestMcpServers();
    return () => unsub();
  }, []);

  // Klick außerhalb schließt Dropdown
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isOpen]);

  const serverEntries = Object.entries(servers);

  // Zähle Ampel-Status
  const okCount = serverEntries.filter(([_, s]) => s.enabled && !s.error && !s.warning).length;
  const warnCount = serverEntries.filter(([_, s]) => (!s.enabled && !s.error) || s.warning).length;
  const errCount = serverEntries.filter(([_, s]) => !!s.error).length;

  const getStatus = (server: MCPServerConfig) => {
    if (server.error) return "err";
    if (server.enabled) return "ok";
    return "warn"; // Deaktiviert oder Standby = Gelb
  };

  const filtered = serverEntries.filter(([_, s]) => {
    const st = getStatus(s);
    if (filter === "ok") return st === "ok";
    if (filter === "warn") return st === "warn";
    if (filter === "err") return st === "err";
    return true;
  });

  const handleToggle = (id: string, current: boolean) => {
    socketManager.toggleMcpServer(id, !current);
  };

  return (
    <div className="relative inline-block" ref={dropdownRef}>
      {/* Aufklapp-Button mit Ampel-Indikatoren */}
      <button
        onClick={() => setIsOpen((prev) => !prev)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-full glass-panel border border-[#00d4ff]/40 hover:border-[#00d4ff] bg-[#0a0d14]/85 text-xs text-white hover:bg-white/10 transition-all shadow-[0_0_12px_rgba(0,212,255,0.2)]"
        title="Alle Skills und Status anzeigen"
      >
        <Puzzle className="w-3.5 h-3.5 text-[#00d4ff]" />
        <span className="font-bold tracking-wider text-[11px] uppercase">SKILLS</span>
        
        {/* Ampel-Badges */}
        <div className="flex items-center gap-1.5 text-[10px] font-mono font-bold">
          <span className="flex items-center gap-0.5 text-[#00ff88]" title="Grün: Aktiv & betriebsbereit">
            <span className="w-2 h-2 rounded-full bg-[#00ff88]" />
            {okCount}
          </span>
          <span className="flex items-center gap-0.5 text-yellow-400" title="Gelb: Standby / Warnung">
            <span className="w-2 h-2 rounded-full bg-yellow-400" />
            {warnCount}
          </span>
          <span className="flex items-center gap-0.5 text-red-400" title="Rot: Fehler / Nicht geladen">
            <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
            {errCount}
          </span>
        </div>

        {isOpen ? <ChevronUp className="w-3.5 h-3.5 text-gray-400" /> : <ChevronDown className="w-3.5 h-3.5 text-gray-400" />}
      </button>

      {/* Aufgeklapptes Dropdown / Panel */}
      {isOpen && (
        <div className="absolute top-full mt-2 left-0 w-80 sm:w-96 rounded-2xl glass-panel-glow bg-[#0a0d14]/95 border border-[#00d4ff]/40 shadow-2xl p-4 z-50 animate-in fade-in zoom-in-95 duration-150">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-[#1f242d] pb-2.5 mb-3">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[#00d4ff] animate-ping" />
              <h3 className="text-xs font-black tracking-wider uppercase text-white">
                Skill & Tool Matrix Status
              </h3>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="p-1 rounded-md text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Filter-Leiste (Ampel-Filter) */}
          <div className="flex items-center gap-1.5 mb-3 text-[10px] font-bold">
            <button
              onClick={() => setFilter("all")}
              className={`px-2 py-0.5 rounded-md transition-colors ${
                filter === "all" ? "bg-[#00d4ff]/20 text-[#00d4ff] border border-[#00d4ff]/40" : "text-gray-400 hover:text-white"
              }`}
            >
              Alle ({serverEntries.length})
            </button>
            <button
              onClick={() => setFilter("ok")}
              className={`flex items-center gap-1 px-2 py-0.5 rounded-md transition-colors ${
                filter === "ok" ? "bg-[#00ff88]/20 text-[#00ff88] border border-[#00ff88]/40" : "text-gray-400 hover:text-white"
              }`}
            >
              <span className="w-1.5 h-1.5 rounded-full bg-[#00ff88]" />
              Super ({okCount})
            </button>
            <button
              onClick={() => setFilter("warn")}
              className={`flex items-center gap-1 px-2 py-0.5 rounded-md transition-colors ${
                filter === "warn" ? "bg-yellow-400/20 text-yellow-400 border border-yellow-400/40" : "text-gray-400 hover:text-white"
              }`}
            >
              <span className="w-1.5 h-1.5 rounded-full bg-yellow-400" />
              Standby ({warnCount})
            </button>
            <button
              onClick={() => setFilter("err")}
              className={`flex items-center gap-1 px-2 py-0.5 rounded-md transition-colors ${
                filter === "err" ? "bg-red-500/20 text-red-400 border border-red-500/40" : "text-gray-400 hover:text-white"
              }`}
            >
              <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
              Fehler ({errCount})
            </button>
          </div>

          {/* Liste der Skills */}
          <div className="max-h-64 overflow-y-auto space-y-2 pr-1">
            {filtered.length === 0 ? (
              <div className="text-center py-6 text-xs text-gray-500">
                Keine Skills in dieser Kategorie.
              </div>
            ) : (
              filtered.map(([id, server]) => {
                const status = getStatus(server);
                const isEnabled = !!server.enabled;

                return (
                  <div
                    key={id}
                    className={`p-2.5 rounded-xl border transition-all ${
                      status === "ok"
                        ? "bg-[#081a24]/60 border-[#00d4ff]/30"
                        : status === "err"
                        ? "bg-[#24080b]/60 border-red-500/40"
                        : "bg-[#14151a]/50 border-gray-800"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2 min-w-0">
                        {/* Status-Punkt */}
                        <div
                          className={`w-2.5 h-2.5 rounded-full shrink-0 ${
                            status === "ok"
                              ? "bg-[#00ff88] shadow-[0_0_8px_#00ff88]"
                              : status === "err"
                              ? "bg-red-500 shadow-[0_0_8px_red] animate-pulse"
                              : "bg-yellow-400 shadow-[0_0_8px_yellow]"
                          }`}
                        />
                        <div className="truncate">
                          <div className="flex items-center gap-1.5">
                            <span className="text-xs font-bold text-white tracking-wide truncate">
                              {id}
                            </span>
                            {server.category && (
                              <span className="text-[9px] px-1.5 py-0.2 rounded bg-black/40 text-gray-400 border border-white/5">
                                {server.category}
                              </span>
                            )}
                          </div>
                          <p className="text-[10px] text-gray-400 truncate max-w-[200px]">
                            {server.description || "MCP Tool / Funktion"}
                          </p>
                        </div>
                      </div>

                      {/* Toggle-Button */}
                      <button
                        onClick={() => handleToggle(id, isEnabled)}
                        className={`p-1.5 rounded-lg border transition-all shrink-0 ${
                          isEnabled
                            ? "bg-[#00d4ff]/20 border-[#00d4ff]/50 text-[#00d4ff] hover:bg-red-500/20 hover:text-red-400"
                            : "bg-gray-800/60 border-gray-700 text-gray-400 hover:bg-[#00ff88]/20 hover:text-[#00ff88]"
                        }`}
                        title={isEnabled ? "Skill deaktivieren" : "Skill aktivieren"}
                      >
                        <Power className="w-3.5 h-3.5" />
                      </button>
                    </div>

                    {/* Fehlerhinweis bei Status Rot */}
                    {server.error && (
                      <div className="mt-1.5 text-[9px] font-mono text-red-400 bg-red-950/40 p-1 rounded border border-red-900/50">
                        Fehler: {server.error}
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>

          {/* Footer */}
          <div className="mt-3 pt-2 border-t border-[#1f242d] flex items-center justify-between text-[10px] text-gray-400">
            <span>🟢 Super · 🟡 Standby · 🔴 Fehler</span>
            <button
              onClick={() => socketManager.requestMcpServers()}
              className="flex items-center gap-1 text-[#00d4ff] hover:underline"
            >
              <RefreshCw className="w-2.5 h-2.5" />
              Aktualisieren
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
