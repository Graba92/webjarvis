"use client";

import React, { useState, useEffect, useRef } from "react";
import { DevLogEntry } from "@/lib/types";
import { socketManager } from "@/lib/websocket";
import { 
  Terminal, Trash2, ChevronDown, ChevronUp, X, Filter, 
  Move, Maximize2, Shield, Wrench, AlertTriangle, Bug
} from "lucide-react";

interface DevConsoleProps {
  isOpen: boolean;
  onClose: () => void;
}

export const DevConsole: React.FC<DevConsoleProps> = ({ isOpen, onClose }) => {
  const [logs, setLogs] = useState<DevLogEntry[]>([]);
  const [filter, setFilter] = useState<string>("");
  const [categoryFilter, setCategoryFilter] = useState<"ALL" | "ERRORS" | "SYS" | "TOOLS" | "SANDBOX">("ALL");
  const [isMinimized, setIsMinimized] = useState<boolean>(false);
  const [aiName, setAiName] = useState<string>("CYPHER");

  // Draggable Position & Resizable Size
  const [pos, setPos] = useState<{ x: number; y: number } | null>(null);
  const [size, setSize] = useState<{ width: number; height: number }>({ width: 640, height: 420 });

  const scrollRef = useRef<HTMLDivElement>(null);
  const draggingRef = useRef<{ startX: number; startY: number; posX: number; posY: number } | null>(null);
  const resizingRef = useRef<{ startX: number; startY: number; startW: number; startH: number } | null>(null);

  // Initial Position festlegen
  useEffect(() => {
    if (typeof window !== "undefined" && pos === null) {
      setPos({
        x: Math.max(20, window.innerWidth - 680),
        y: Math.max(60, window.innerHeight - 520)
      });
    }
  }, [pos]);

  useEffect(() => {
    const unsubLog = socketManager.onDevLog((entry) => {
      setLogs((prev) => [...prev.slice(-300), entry]);
    });
    const unsubAiName = socketManager.onAiName((name) => {
      if (name) setAiName(name);
    });
    return () => {
      unsubLog();
      unsubAiName();
    };
  }, []);

  useEffect(() => {
    if (scrollRef.current && !isMinimized) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, isMinimized]);

  if (!isOpen) return null;

  // --- Dragging Handler ---
  const handleHeaderMouseDown = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest("button") || (e.target as HTMLElement).closest("input")) return;
    e.preventDefault();
    const currentX = pos ? pos.x : 100;
    const currentY = pos ? pos.y : 100;
    draggingRef.current = {
      startX: e.clientX,
      startY: e.clientY,
      posX: currentX,
      posY: currentY,
    };

    const handleMouseMove = (ev: MouseEvent) => {
      if (!draggingRef.current) return;
      const dx = ev.clientX - draggingRef.current.startX;
      const dy = ev.clientY - draggingRef.current.startY;
      setPos({
        x: Math.max(10, Math.min(window.innerWidth - 120, draggingRef.current.posX + dx)),
        y: Math.max(10, Math.min(window.innerHeight - 60, draggingRef.current.posY + dy)),
      });
    };

    const handleMouseUp = () => {
      draggingRef.current = null;
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };

    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
  };

  // --- Resizing Handler ---
  const handleResizeMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    resizingRef.current = {
      startX: e.clientX,
      startY: e.clientY,
      startW: size.width,
      startH: size.height,
    };

    const handleMouseMove = (ev: MouseEvent) => {
      if (!resizingRef.current) return;
      const dw = ev.clientX - resizingRef.current.startX;
      const dh = ev.clientY - resizingRef.current.startY;
      setSize({
        width: Math.max(380, Math.min(window.innerWidth - 40, resizingRef.current.startW + dw)),
        height: Math.max(180, Math.min(window.innerHeight - 60, resizingRef.current.startH + dh)),
      });
    };

    const handleMouseUp = () => {
      resizingRef.current = null;
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };

    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
  };

  // --- Filterung der Logs ---
  const filteredLogs = logs.filter((log) => {
    const textLower = log.text.toLowerCase();
    const speakerLower = log.speaker.toLowerCase();

    if (categoryFilter === "ERRORS") {
      if (!speakerLower.includes("err") && !textLower.includes("error") && !textLower.includes("exception")) return false;
    } else if (categoryFilter === "TOOLS") {
      if (!textLower.includes("tool") && !textLower.includes("mcp_") && !speakerLower.includes("action")) return false;
    } else if (categoryFilter === "SANDBOX") {
      if (!textLower.includes("sandbox") && !textLower.includes("bwrap") && !textLower.includes("vollzugriff") && !textLower.includes("os")) return false;
    } else if (categoryFilter === "SYS") {
      if (speakerLower !== "sys" && speakerLower !== "core") return false;
    }

    if (filter) {
      const q = filter.toLowerCase();
      if (!textLower.includes(q) && !speakerLower.includes(q)) return false;
    }
    return true;
  });

  return (
    <div
      style={{
        position: "fixed",
        left: pos ? `${pos.x}px` : "auto",
        top: pos ? `${pos.y}px` : "auto",
        width: isMinimized ? "320px" : `${size.width}px`,
        height: isMinimized ? "42px" : `${size.height}px`,
        zIndex: 45,
      }}
      className="rounded-2xl glass-panel-glow border border-[#00d4ff]/40 shadow-2xl bg-[#080a0f]/95 font-mono flex flex-col overflow-hidden select-none animate-in fade-in duration-100"
    >
      {/* Draggable Header */}
      <div
        onMouseDown={handleHeaderMouseDown}
        className="flex items-center justify-between px-3.5 py-2.5 border-b border-[#1f242d] bg-[#0d1117] cursor-grab active:cursor-grabbing shrink-0"
      >
        <div className="flex items-center gap-2 pointer-events-none">
          <Terminal className="w-4 h-4 text-[#00d4ff]" />
          <span className="text-xs font-black text-white tracking-wider flex items-center gap-1.5">
            <span>{aiName.toUpperCase()} DEV-CONSOLE</span>
            <span className="text-[10px] text-gray-500 font-normal">| Live Terminal</span>
          </span>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#00d4ff]/15 text-[#00d4ff] font-bold border border-[#00d4ff]/30">
            {logs.length}
          </span>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => setLogs([])}
            title="Konsole leeren"
            className="p-1 rounded text-gray-400 hover:text-red-400 hover:bg-white/5 transition-colors cursor-pointer"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            title={isMinimized ? "Maximieren" : "Minimieren"}
            className="p-1 rounded text-gray-400 hover:text-white hover:bg-white/5 transition-colors cursor-pointer"
          >
            {isMinimized ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
          <button
            onClick={onClose}
            title="Schließen"
            className="p-1 rounded text-gray-400 hover:text-red-400 hover:bg-red-500/10 transition-colors cursor-pointer"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {!isMinimized && (
        <>
          {/* Sub-Header / Schnellfilter & Search */}
          <div className="flex flex-col gap-1.5 p-2 bg-[#0a0d14] border-b border-[#1f242d] shrink-0">
            <div className="flex items-center gap-2">
              <div className="relative flex-1 flex items-center bg-[#080a0f] border border-[#1f242d] rounded-lg px-2.5 py-1">
                <Filter className="w-3 h-3 text-gray-500 mr-2" />
                <input
                  type="text"
                  placeholder="Filter logs, tool calls, tracebacks..."
                  value={filter}
                  onChange={(e) => setFilter(e.target.value)}
                  className="flex-1 bg-transparent text-xs text-gray-200 placeholder-gray-600 focus:outline-none"
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
            </div>

            {/* Filter-Kategorie-Chips */}
            <div className="flex items-center gap-1.5 overflow-x-auto text-[10px] font-sans font-bold">
              {(["ALL", "ERRORS", "TOOLS", "SANDBOX", "SYS"] as const).map((cat) => (
                <button
                  key={cat}
                  onClick={() => setCategoryFilter(cat)}
                  className={`px-2 py-0.5 rounded-md border transition-all cursor-pointer ${
                    categoryFilter === cat
                      ? "bg-[#00d4ff]/20 text-[#00d4ff] border-[#00d4ff]/50 shadow-sm shadow-[#00d4ff]/20"
                      : "bg-white/5 text-gray-400 border-transparent hover:text-white"
                  }`}
                >
                  {cat === "ALL" && "Alle"}
                  {cat === "ERRORS" && "⚠️ Fehler"}
                  {cat === "TOOLS" && "⚡ Tool-Calls"}
                  {cat === "SANDBOX" && "🛡️ Sandbox/OS"}
                  {cat === "SYS" && "SYS Core"}
                </button>
              ))}
            </div>
          </div>

          {/* Log Stream Body */}
          <div
            ref={scrollRef}
            className="flex-1 overflow-y-auto p-3 flex flex-col gap-1 text-[11px] select-text"
          >
            {filteredLogs.length === 0 ? (
              <div className="text-gray-500 italic p-6 text-center text-xs">
                Keine Entwickler-Logs für diesen Filter. Alle internen Tool-Aufrufe, Sandbox-Events und Tracebacks werden hier ungefiltert gestreamt.
              </div>
            ) : (
              filteredLogs.map((item, idx) => {
                const isErr = item.speaker.includes("ERR") || item.text.toLowerCase().includes("error") || item.text.toLowerCase().includes("exception");
                const isWarn = item.speaker.includes("WARN") || item.text.toLowerCase().includes("warn");
                const isTool = item.text.toLowerCase().includes("tool-aufruf") || item.text.toLowerCase().includes("tool-antwort") || item.text.includes("[SANDBOX EXEC]") || item.text.includes("[OS ROOT EXEC]");
                
                return (
                  <div
                    key={idx}
                    className={`flex items-start gap-2 py-1 px-1.5 rounded leading-tight hover:bg-white/[0.03] transition-colors ${
                      isErr 
                        ? "text-red-300 bg-red-500/[0.08] border border-red-500/20" 
                        : isWarn 
                        ? "text-amber-300 bg-amber-500/[0.05]" 
                        : isTool
                        ? "text-cyan-200 bg-[#00d4ff]/[0.04]"
                        : "text-gray-300"
                    }`}
                  >
                    <span className="text-[10px] text-gray-500 shrink-0 select-none font-mono">
                      [{item.ts}]
                    </span>
                    <span
                      className={`font-bold shrink-0 text-[9px] px-1.5 py-0.5 rounded font-mono ${
                        isErr
                          ? "bg-red-500/20 text-red-300 border border-red-500/40"
                          : isWarn
                          ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                          : isTool
                          ? "bg-[#00d4ff]/20 text-[#00d4ff] border border-[#00d4ff]/40"
                          : item.speaker === "SYS"
                          ? "bg-blue-500/15 text-blue-300"
                          : "bg-purple-500/15 text-purple-300"
                      }`}
                    >
                      {item.speaker}
                    </span>
                    <span className="break-all whitespace-pre-wrap flex-1 font-mono leading-relaxed">
                      {item.text}
                    </span>
                  </div>
                );
              })
            )}
          </div>

          {/* Footer mit Resize Handle */}
          <div className="relative px-3 py-1 bg-[#0a0d14] border-t border-[#1f242d] flex items-center justify-between text-[10px] text-gray-500 shrink-0">
            <span className="flex items-center gap-1.5">
              <Move className="w-3 h-3 text-gray-500" />
              <span>Fenster frei verschiebbar & in der Größe anpassbar</span>
            </span>

            {/* Resize Handle unten rechts */}
            <div
              onMouseDown={handleResizeMouseDown}
              className="w-4 h-4 cursor-se-resize flex items-center justify-center text-gray-400 hover:text-[#00d4ff] transition-colors"
              title="Klicken & Ziehen zum Ändern der Fenstergröße"
            >
              <svg width="10" height="10" viewBox="0 0 10 10" fill="currentColor">
                <circle cx="8" cy="8" r="1.2" />
                <circle cx="8" cy="4" r="1.2" />
                <circle cx="4" cy="8" r="1.2" />
              </svg>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
