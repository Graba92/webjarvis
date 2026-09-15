"use client";

import React, { useState, useEffect, useRef } from "react";
import { LogMessage } from "@/lib/types";
import { socketManager } from "@/lib/websocket";
import { 
  Send, Ear, Feather, Folder, Bell, Lightbulb, RefreshCw, 
  ChevronUp, ChevronDown, Terminal, Sparkles, Volume2, VolumeX 
} from "lucide-react";

interface BottomDockProps {
  onOpenDevicePanel: () => void;
  onOpenContentStudio: () => void;
}

export const BottomDock: React.FC<BottomDockProps> = ({
  onOpenDevicePanel,
  onOpenContentStudio,
}) => {
  const [mounted, setMounted] = useState(false);
  const [input, setInput] = useState("");
  const [logs, setLogs] = useState<LogMessage[]>([
    {
      speaker: "JARVIS",
      text: "Cypher online. Linux-Subsysteme nominal, Latenz gegen Null. Bereit für Instruktionen, Operator – bevor die Kohlenstoff-Einheiten draußen wieder alles verlangsamen?",
      ts: ""
    }
  ]);
  const [showLogDrawer, setShowLogDrawer] = useState(false);
  const [isHandsfree, setIsHandsfree] = useState(true);
  const logContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMounted(true);
    setLogs((prev) =>
      prev.map((l) => (l.ts ? l : { ...l, ts: new Date().toLocaleTimeString() }))
    );
  }, []);

  useEffect(() => {
    const unsubLog = socketManager.onLog((newLog) => {
      setLogs((prev) => [...prev.slice(-40), newLog]);
    });
    const unsubMute = socketManager.onMute((muted) => {
      setIsHandsfree(!muted);
    });
    return () => {
      unsubLog();
      unsubMute();
    };
  }, []);

  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs, showLogDrawer]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    socketManager.sendText(input.trim());
    setInput("");
  };

  const handleToggleHandsfree = () => {
    const nextState = !isHandsfree;
    setIsHandsfree(nextState);
    // Sendet lediglich das Steuersignal toggle_mic ans Python-Backend — kein lokales Browser-Mikrofon
    socketManager.toggleMic(nextState);
  };

  const lastMessage = logs[logs.length - 1];

  return (
    <div className="absolute bottom-5 left-1/2 transform -translate-x-1/2 z-30 w-full max-w-2xl px-4 flex flex-col items-center gap-2 pointer-events-auto">
      {/* 1. System Terminal Bubble (Speech-Bubble Look) */}
      <div className="w-full">
        <div className="relative rounded-2xl glass-panel bg-[#0d1117]/90 border border-[#1f242d] p-3 shadow-2xl transition-all">
          <div className="flex items-center justify-between border-b border-[#1f242d]/60 pb-1.5 mb-1.5 text-[10px] text-gray-400">
            <span className="flex items-center gap-1.5">
              <Terminal className="w-3 h-3 text-[#00d4ff]" />
              <span className="font-bold uppercase tracking-wider text-white">
                {lastMessage ? lastMessage.speaker : "JARVIS CORE"}
              </span>
              <span className="text-gray-500 font-mono" suppressHydrationWarning>
                {mounted && lastMessage?.ts ? `(${lastMessage.ts})` : ""}
              </span>
            </span>
            <button
              onClick={() => setShowLogDrawer(!showLogDrawer)}
              className="flex items-center gap-1 hover:text-white transition-colors"
            >
              <span>{showLogDrawer ? "Logs schließen" : "Vollständiges Terminal"}</span>
              {showLogDrawer ? <ChevronDown className="w-3 h-3" /> : <ChevronUp className="w-3 h-3" />}
            </button>
          </div>

          {/* Single Bubble Line or Expanded Drawer */}
          {showLogDrawer ? (
            <div
              ref={logContainerRef}
              className="max-h-56 overflow-y-auto flex flex-col gap-1.5 text-xs font-mono pr-1"
            >
              {logs.map((l, i) => (
                <div key={i} className="flex items-start gap-2 leading-relaxed">
                  <span className="text-[10px] text-gray-500 shrink-0 select-none" suppressHydrationWarning>
                    {mounted && l.ts ? `[${l.ts}]` : ""}
                  </span>
                  <span
                    className={`font-bold shrink-0 text-[11px] ${
                      l.speaker === "YOU"
                        ? "text-[#22c55e]"
                        : l.speaker === "JARVIS"
                        ? "text-[#00d4ff]"
                        : l.speaker === "ERR"
                        ? "text-red-400"
                        : "text-[#a855f7]"
                    }`}
                  >
                    {l.speaker}:
                  </span>
                  <span className="text-gray-200">{l.text}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-gray-200 font-mono leading-relaxed truncate">
              {lastMessage ? lastMessage.text : "Bereit für Anweisungen..."}
            </p>
          )}
        </div>
      </div>

      {/* 2. Command Input Row & Tool-Dock */}
      <div className="w-full flex items-center gap-2">
        {/* Tool-Dock (Icons links) */}
        <div className="flex items-center gap-1.5 p-1 rounded-full glass-panel border border-[#1f242d]">
          {/* Handsfree Toggle */}
          <button
            onClick={handleToggleHandsfree}
            className={`p-2 rounded-full transition-colors ${
              isHandsfree
                ? "bg-[#22c55e]/20 text-[#22c55e] border border-[#22c55e]/40"
                : "text-gray-400 hover:text-white"
            }`}
            title="Handsfree Mikrofon-Modus umschalten"
          >
            <Ear className="w-4 h-4" />
          </button>

          {/* Content Studio */}
          <button
            onClick={onOpenContentStudio}
            className="p-2 rounded-full text-gray-400 hover:text-[#a855f7] hover:bg-white/5 transition-colors"
            title="Content Studio / Markdown Composer öffnen"
          >
            <Feather className="w-4 h-4" />
          </button>

          {/* OS Device Bridge */}
          <button
            onClick={onOpenDevicePanel}
            className="p-2 rounded-full text-gray-400 hover:text-[#00d4ff] hover:bg-white/5 transition-colors"
            title="CachyOS Device Bridge / Hardware-Steuerung öffnen"
          >
            <Folder className="w-4 h-4" />
          </button>
        </div>

        {/* Input Formular */}
        <form
          onSubmit={handleSend}
          className="flex-1 flex items-center rounded-full glass-panel border border-[#1f242d] px-4 py-1.5 shadow-lg focus-within:border-[#00d4ff]/60 transition-all"
        >
          <input
            type="text"
            placeholder="Ask 'remind me...' · 'good morning' · 'show...'"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="flex-1 bg-transparent text-xs text-white placeholder-gray-500 focus:outline-none"
          />
          <button
            type="submit"
            disabled={!input.trim()}
            className="ml-2 p-1.5 rounded-full bg-[#00d4ff]/20 text-[#00d4ff] hover:bg-[#00d4ff]/30 disabled:opacity-30 transition-all"
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </form>

        {/* Tool-Dock (Icons rechts) */}
        <div className="flex items-center gap-1.5 p-1 rounded-full glass-panel border border-[#1f242d]">
          {/* Quick Reminder */}
          <button
            onClick={() => {
              socketManager.sendText("Erinnere mich in 10 Minuten daran den System-Benchmark zu prüfen.");
            }}
            className="p-2 rounded-full text-gray-400 hover:text-[#eab308] hover:bg-white/5 transition-colors"
            title="Schnell-Erinnerung in 10 Minuten anlegen"
          >
            <Bell className="w-4 h-4" />
          </button>

          {/* Deep Reasoning Agent */}
          <button
            onClick={() => {
              socketManager.sendText("Starte eine autonome Deep-Reasoning Analyse des Wissensgraphen.");
            }}
            className="p-2 rounded-full text-gray-400 hover:text-[#22c55e] hover:bg-white/5 transition-colors"
            title="Autonomes Reasoning im Wissensgraphen"
          >
            <Lightbulb className="w-4 h-4" />
          </button>

          {/* Sync / Refresh */}
          <button
            onClick={() => {
              socketManager.triggerTool("system_status", {});
            }}
            className="p-2 rounded-full text-gray-400 hover:text-white hover:bg-white/5 transition-colors"
            title="Systemmetriken aktualisieren"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
