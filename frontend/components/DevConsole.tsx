"use client";

import React, { useState, useEffect, useRef } from "react";
import { DevLogEntry } from "@/lib/types";
import { socketManager } from "@/lib/websocket";
import { Terminal, Trash2, ChevronDown, ChevronUp, X, Filter } from "lucide-react";

interface DevConsoleProps {
  isOpen: boolean;
  onClose: () => void;
}

export const DevConsole: React.FC<DevConsoleProps> = ({ isOpen, onClose }) => {
  const [logs, setLogs] = useState<DevLogEntry[]>([]);
  const [filter, setFilter] = useState<string>("");
  const [onlyErrors, setOnlyErrors] = useState<boolean>(false);
  const [isMinimized, setIsMinimized] = useState<boolean>(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const unsub = socketManager.onDevLog((entry) => {
      setLogs((prev) => [...prev.slice(-250), entry]);
    });
    return () => unsub();
  }, []);

  useEffect(() => {
    if (scrollRef.current && !isMinimized) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, isMinimized]);

  if (!isOpen) return null;

  const filteredLogs = logs.filter((log) => {
    if (onlyErrors && !log.speaker.includes("ERR") && !log.text.toLowerCase().includes("error") && !log.text.toLowerCase().includes("exception")) {
      return false;
    }
    if (filter && !log.text.toLowerCase().includes(filter.toLowerCase()) && !log.speaker.toLowerCase().includes(filter.toLowerCase())) {
      return false;
    }
    return true;
  });

  return (
    <div
      className={`fixed bottom-24 right-6 z-40 transition-all duration-300 rounded-xl glass-panel border border-[#00d4ff]/30 shadow-2xl bg-[#080a0f]/95 font-mono ${
        isMinimized ? "w-80 h-11" : "w-[600px] h-[380px]"
      } flex flex-col overflow-hidden`}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-[#1f242d] bg-[#0d1117] select-none">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-[#00d4ff]" />
          <span className="text-xs font-bold text-white tracking-wide">CYPHER DEV-CONSOLE</span>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#00d4ff]/10 text-[#00d4ff] font-bold">
            {logs.length} EVENTS
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          <button
            onClick={() => setOnlyErrors(!onlyErrors)}
            title="Nur Fehler filtern"
            className={`p-1 rounded text-[10px] px-1.5 border transition-colors ${
              onlyErrors
                ? "bg-red-500/20 text-red-400 border-red-500/40"
                : "text-gray-400 border-transparent hover:text-white"
            }`}
          >
            ERR ONLY
          </button>
          <button
            onClick={() => setLogs([])}
            title="Konsole leeren"
            className="p-1 text-gray-400 hover:text-red-400 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            title={isMinimized ? "Maximieren" : "Minimieren"}
            className="p-1 text-gray-400 hover:text-white transition-colors"
          >
            {isMinimized ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
          <button
            onClick={onClose}
            title="Schließen"
            className="p-1 text-gray-400 hover:text-red-400 transition-colors"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {!isMinimized && (
        <>
          {/* Sub-Header / Search filter */}
          <div className="flex items-center gap-2 px-3 py-1.5 bg-[#0a0d14] border-b border-[#1f242d]">
            <Filter className="w-3 h-3 text-gray-500" />
            <input
              type="text"
              placeholder="Filter logs / tracebacks..."
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="flex-1 bg-transparent text-[11px] text-gray-200 placeholder-gray-600 focus:outline-none"
            />
            {filter && (
              <button
                onClick={() => setFilter("")}
                className="text-[10px] text-gray-400 hover:text-white"
              >
                Clear
              </button>
            )}
          </div>

          {/* Log Body */}
          <div
            ref={scrollRef}
            className="flex-1 overflow-y-auto p-2.5 flex flex-col gap-1 text-[11px] select-text"
          >
            {filteredLogs.length === 0 ? (
              <div className="text-gray-500 italic p-4 text-center">
                Keine Logs aufgezeichnet. Backend-Aktivitäten werden hier ungefiltert gestreamt.
              </div>
            ) : (
              filteredLogs.map((item, idx) => {
                const isErr = item.speaker.includes("ERR") || item.text.toLowerCase().includes("error") || item.text.toLowerCase().includes("exception");
                const isWarn = item.text.toLowerCase().includes("warning") || item.text.toLowerCase().includes("warn");
                return (
                  <div
                    key={idx}
                    className={`flex items-start gap-2 py-0.5 leading-tight hover:bg-white/[0.02] px-1 rounded ${
                      isErr ? "text-red-400 bg-red-500/[0.06]" : isWarn ? "text-amber-300" : "text-gray-300"
                    }`}
                  >
                    <span className="text-[10px] text-gray-500 shrink-0 select-none">
                      [{item.ts}]
                    </span>
                    <span
                      className={`font-bold shrink-0 text-[10px] px-1 rounded ${
                        isErr
                          ? "bg-red-500/20 text-red-300"
                          : item.speaker === "SYS"
                          ? "bg-[#00d4ff]/10 text-[#00d4ff]"
                          : item.speaker === "BACKUP"
                          ? "bg-[#22c55e]/10 text-[#22c55e]"
                          : "bg-purple-500/10 text-purple-300"
                      }`}
                    >
                      {item.speaker}
                    </span>
                    <span className="break-all whitespace-pre-wrap flex-1">{item.text}</span>
                  </div>
                );
              })
            )}
          </div>
        </>
      )}
    </div>
  );
};
