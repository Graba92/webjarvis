"use client";

import React, { useState, useEffect } from "react";
import { AssistantState } from "@/lib/types";
import { socketManager } from "@/lib/websocket";
import { 
  Activity, 
  CheckCircle2, 
  Loader2, 
  ChevronDown, 
  ChevronUp, 
  AlertTriangle, 
  Wrench, 
  Brain, 
  Volume2, 
  Mic, 
  ShieldCheck 
} from "lucide-react";

interface ActiveTask {
  id: string;
  title: string;
  progress: number;
  details: string;
  type: "tool" | "thinking" | "speaking" | "system";
  updatedAt: number;
}

interface ActivityProgressHUDProps {
  state: AssistantState;
}

export const ActivityProgressHUD: React.FC<ActivityProgressHUDProps> = ({ state }) => {
  const [tasks, setTasks] = useState<ActiveTask[]>([]);
  const [isExpanded, setIsExpanded] = useState<boolean>(false);
  const [isHudCollapsed, setIsHudCollapsed] = useState<boolean>(false);

  // 1. WebSocket Log-Listener für Tool-Ausführungen & Hintergrundprozesse
  useEffect(() => {
    const unsubLog = socketManager.onLog((log) => {
      const text = log.text || "";

      // Tool-Start erkennen
      if (text.startsWith("Tool-Aufruf:")) {
        const parts = text.replace("Tool-Aufruf:", "").trim();
        const toolName = parts.split("(")[0].trim();
        let paramPreview = "";
        const parenIdx = parts.indexOf("(");
        if (parenIdx !== -1) {
          paramPreview = parts.slice(parenIdx + 1, -1).trim();
          if (paramPreview.length > 45) paramPreview = paramPreview.slice(0, 42) + "...";
        }

        setTasks((prev) => {
          const filtered = prev.filter((t) => t.id !== toolName);
          const newTask: ActiveTask = {
            id: toolName,
            title: `Tool: ${toolName}`,
            progress: 35,
            details: paramPreview ? `Parameter: ${paramPreview}` : "Wird ausgeführt...",
            type: "tool",
            updatedAt: Date.now()
          };
          return [newTask, ...filtered].slice(0, 3);
        });
      }

      // Tool-Abschluss erkennen
      else if (text.startsWith("Tool-Antwort")) {
        const matchedName = text.match(/Tool-Antwort\s*\(([^)]+)\)/);
        const toolName = matchedName ? matchedName[1] : null;

        setTasks((prev) => {
          return prev.map((t) => {
            if (!toolName || t.id === toolName) {
              return { ...t, progress: 100, details: "Erfolgreich abgeschlossen", updatedAt: Date.now() };
            }
            return t;
          });
        });

        // Nach 1 Sekunde abgeschlossenen Task entfernen
        setTimeout(() => {
          setTasks((prev) => prev.filter((t) => (toolName ? t.id !== toolName : t.progress < 100)));
        }, 1200);
      }

      // Fehler im Log erkennen
      else if (log.speaker === "ERR" || text.includes("ERR") || text.includes("Fehler")) {
        setTasks((prev) => {
          const errTask: ActiveTask = {
            id: `err-${Date.now()}`,
            title: "System-Meldung",
            progress: 100,
            details: text.slice(0, 60),
            type: "system",
            updatedAt: Date.now()
          };
          return [errTask, ...prev].slice(0, 3);
        });

        setTimeout(() => {
          setTasks((prev) => prev.filter((t) => !t.id.startsWith("err-")));
        }, 4000);
      }
    });

    return () => unsubLog();
  }, []);

  // 2. Lebenszyklus des AssistantState (THINKING / SPEAKING sauber auflösen!)
  useEffect(() => {
    if (state === "THINKING") {
      setTasks((prev) => {
        if (prev.some((t) => t.id === "ai-thinking" || t.type === "tool")) return prev;
        const thinkingTask: ActiveTask = {
          id: "ai-thinking",
          title: "Neural-Kognition",
          progress: 50,
          details: "Analysiere Benutzer-Input & plane Handlungen...",
          type: "thinking",
          updatedAt: Date.now()
        };
        return [thinkingTask, ...prev.filter((t) => t.id !== "ai-speaking")].slice(0, 3);
      });
    } else if (state === "SPEAKING") {
      setTasks((prev) => {
        const filtered = prev.filter((t) => t.id !== "ai-thinking");
        if (filtered.some((t) => t.id === "ai-speaking")) return filtered;
        const speakingTask: ActiveTask = {
          id: "ai-speaking",
          title: "Sprachausgabe & Audio-Stream",
          progress: 85,
          details: "PipeWire Audio wird übertragen...",
          type: "speaking",
          updatedAt: Date.now()
        };
        return [speakingTask, ...filtered].slice(0, 3);
      });
    } else {
      // Wenn der State wieder ONLINE, LISTENING, IDLE etc. ist:
      // Thinking und Speaking SOFORT entfernen, damit er niemals bei 75% hängen bleibt!
      setTasks((prev) => prev.filter((t) => t.id !== "ai-thinking" && t.id !== "ai-speaking"));
    }
  }, [state]);

  // Haupt-Task ermitteln
  const primaryTask = tasks[0] || null;
  const isIdle = !primaryTask && (state === "ONLINE" || state === "LISTENING" || state === "IDLE");
  const isDisconnected = state === "OFFLINE" || state === "ERROR";

  // Berechne Hauptbalken
  const mainProgress = isDisconnected ? 0 : isIdle ? 100 : primaryTask ? primaryTask.progress : 100;
  const mainTitle = isDisconnected
    ? "Verbindung getrennt"
    : isIdle
    ? state === "LISTENING"
      ? "Höre auf Spracheingabe..."
      : "Bereit für Instruktionen"
    : primaryTask?.title;
  const mainDetails = isDisconnected
    ? "Warte auf Reconnect..."
    : isIdle
    ? "Alle Subsysteme im Standby (0 aktive Jobs)"
    : primaryTask?.details;

  const getTaskIcon = (type: ActiveTask["type"]) => {
    switch (type) {
      case "tool": return <Wrench className="w-3.5 h-3.5 text-[#00d4ff]" />;
      case "thinking": return <Brain className="w-3.5 h-3.5 text-[#a855f7]" />;
      case "speaking": return <Volume2 className="w-3.5 h-3.5 text-[#38bdf8]" />;
      default: return <Activity className="w-3.5 h-3.5 text-gray-400" />;
    }
  };

  return (
    <>
      {/* 0. Sichtbarer Aufklapp-Button ganz oben mittig (erscheint nur, wenn eingeklappt) */}
      {isHudCollapsed && (
        <button
          onClick={() => setIsHudCollapsed(false)}
          className="absolute top-0 left-1/2 transform -translate-x-1/2 z-20 flex items-center gap-1.5 px-3 py-1 rounded-b-xl glass-panel-glow border-x border-b border-[#00ff88]/40 bg-[#0a0d14]/90 text-[#00ff88] hover:bg-[#00ff88]/20 hover:scale-105 transition-all shadow-[0_0_15px_rgba(0,255,136,0.2)] text-[10px] font-mono font-bold"
          title="Progress-HUD aufklappen"
        >
          <span>HUD // {mainProgress}%</span>
          <ChevronDown className="w-3 h-3 animate-pulse" />
        </button>
      )}

      <div className={`absolute top-16 left-1/2 transform -translate-x-1/2 z-20 w-full max-w-lg pointer-events-none px-4 transition-transform duration-300 ease-in-out ${
        isHudCollapsed ? "-translate-y-[calc(100%+5rem)] pointer-events-none" : "translate-y-0"
      }`}>
        <div className={`pointer-events-auto rounded-2xl glass-panel-glow border backdrop-blur-xl shadow-2xl transition-all duration-300 ${
          isDisconnected
            ? "bg-red-950/70 border-red-500/50 shadow-[0_0_15px_rgba(239,68,68,0.2)]"
            : isIdle
            ? "bg-[#0a0e14]/85 border-[#00d4ff]/30 shadow-[0_0_15px_rgba(0,212,255,0.1)]"
            : "bg-[#0b1522]/95 border-[#00ff88]/50 shadow-[0_0_20px_rgba(0,255,136,0.18)]"
        } p-3`}>
          
          {/* Oberste Zeile: Status-Header & Aufklapp-Button */}
          <div className="flex items-center justify-between gap-2 mb-1.5">
            <div className="flex items-center gap-2 min-w-0">
              {isDisconnected ? (
                <AlertTriangle className="w-4 h-4 text-red-400 animate-pulse" />
              ) : isIdle ? (
                <ShieldCheck className="w-4 h-4 text-[#00ff88]" />
              ) : (
                <Loader2 className="w-4 h-4 text-[#00d4ff] animate-spin" />
              )}
              <span className="text-[11px] font-black tracking-wider uppercase text-white truncate">
                {mainTitle}
              </span>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <span className="text-[10px] font-mono font-bold text-gray-300">
                {mainProgress}%
              </span>

              {/* Einklapp-Button nach oben */}
              <button
                onClick={() => setIsHudCollapsed(true)}
                className="p-1 rounded-md text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
                title="Progress-HUD nach oben einklappen"
              >
                <ChevronUp className="w-3.5 h-3.5 text-[#00d4ff]" />
              </button>

              {/* Badge für Anzahl paralleler Tasks (bis zu 3) */}
              {tasks.length > 1 && (
                <button
                  onClick={() => setIsExpanded((prev) => !prev)}
                  className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-[#00d4ff]/20 text-[#00d4ff] hover:bg-[#00d4ff]/30 border border-[#00d4ff]/40 text-[9px] font-bold transition-colors"
                  title="Parallele Aufgaben aufklappen"
                >
                <span>{tasks.length} AKTIV</span>
                {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              </button>
            )}

            <div className={`w-2 h-2 rounded-full ${
              isDisconnected
                ? "bg-red-500 animate-ping"
                : isIdle
                ? "bg-[#00ff88]"
                : "bg-[#00d4ff] animate-pulse"
            }`} />
          </div>
        </div>

        {/* Dynamischer Haupt-Fortschrittsbalken */}
        <div className="w-full h-1.5 rounded-full bg-black/60 overflow-hidden p-0.5 border border-white/5">
          <div
            className={`h-full rounded-full transition-all duration-300 ease-out shadow-[0_0_8px_currentColor] ${
              isDisconnected
                ? "bg-red-500"
                : isIdle
                ? "bg-[#00ff88]"
                : "bg-gradient-to-r from-[#00d4ff] to-[#00ff88]"
            }`}
            style={{ width: `${mainProgress}%` }}
          />
        </div>

        {/* Detail-Statuszeile */}
        <div className="mt-1.5 flex items-center justify-between text-[10px] text-gray-400 font-mono">
          <span className="truncate pr-2">{mainDetails}</span>
          <span className="text-[9px] text-gray-500 shrink-0 uppercase tracking-widest">
            {isIdle ? "STANDBY" : "RUNNING"}
          </span>
        </div>

        {/* Aufgeklappte Liste bei parallelen Aufgaben (bis zu 3 gleichzeitig) */}
        {isExpanded && tasks.length > 0 && (
          <div className="mt-2.5 pt-2 border-t border-[#1f242d] space-y-2 animate-in fade-in duration-150">
            <div className="text-[9px] font-bold uppercase tracking-wider text-gray-400 flex items-center justify-between">
              <span>Aktive Sub-Prozesse ({tasks.length}/3)</span>
              <button
                onClick={() => setIsExpanded(false)}
                className="text-gray-500 hover:text-white"
              >
                Einklappen ▲
              </button>
            </div>

            {tasks.map((task) => (
              <div
                key={task.id}
                className="p-2 rounded-xl bg-black/40 border border-white/5 flex flex-col gap-1 text-[10px]"
              >
                <div className="flex items-center justify-between text-gray-200 font-bold">
                  <div className="flex items-center gap-1.5 truncate">
                    {getTaskIcon(task.type)}
                    <span className="truncate">{task.title}</span>
                  </div>
                  <span className="font-mono text-[#00d4ff]">{task.progress}%</span>
                </div>
                <div className="w-full h-1 bg-black/80 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-[#00d4ff] transition-all duration-300"
                    style={{ width: `${task.progress}%` }}
                  />
                </div>
                <div className="text-[9px] text-gray-400 font-mono truncate">
                  {task.details}
                </div>
              </div>
            ))}
          </div>
        )}

      </div>
    </div>
    </>
  );
};
