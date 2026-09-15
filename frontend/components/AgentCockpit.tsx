"use client";

import React, { useState, useEffect } from "react";
import { AssistantState, NodeCategory } from "@/lib/types";
import { CATEGORY_COLORS } from "@/lib/graphData";
import { socketManager } from "@/lib/websocket";
import { Eye, Radio, Grid, Crosshair, KeyRound, Mic, MicOff, ShieldAlert } from "lucide-react";

interface AgentCockpitProps {
  state: AssistantState;
  audioLevel: number;
  activeFilter: Set<NodeCategory>;
  onToggleFilter: (cat: NodeCategory) => void;
  categoryCounts: Record<NodeCategory, number>;
  onOpenApiKeyModal: () => void;
}

export const AgentCockpit: React.FC<AgentCockpitProps> = ({
  state,
  audioLevel,
  activeFilter,
  onToggleFilter,
  categoryCounts,
  onOpenApiKeyModal,
}) => {
  const [sensorEyes, setSensorEyes] = useState(false);
  const [sensorWatch, setSensorWatch] = useState(false);
  const [sensorHolo, setSensorHolo] = useState(true);
  const [focusMode, setFocusMode] = useState(false);
  const [paranoiaMuted, setParanoiaMuted] = useState(false);
  const [angle, setAngle] = useState(0);

  useEffect(() => {
    let animId: number;
    const updateRotation = () => {
      const speed = state === "SPEAKING" ? 0.05 : state === "THINKING" ? 0.08 : 0.015;
      setAngle((prev) => (prev + speed) % (Math.PI * 2));
      animId = requestAnimationFrame(updateRotation);
    };
    animId = requestAnimationFrame(updateRotation);
    return () => cancelAnimationFrame(animId);
  }, [state]);

  useEffect(() => {
    const unsubParanoia = socketManager.onParanoiaMute((muted) => {
      setParanoiaMuted(muted);
    });
    const unsubFocus = socketManager.onFocusMode((enabled) => {
      setFocusMode(enabled);
    });
    return () => {
      unsubParanoia();
      unsubFocus();
    };
  }, []);

  const handleInterrupt = () => {
    socketManager.interrupt();
  };

  const handleToggleParanoia = () => {
    const nextState = !paranoiaMuted;
    setParanoiaMuted(nextState);
    socketManager.setParanoiaMute(nextState);
  };

  const handleToggleFocusMode = () => {
    const nextState = !focusMode;
    setFocusMode(nextState);
    socketManager.setFocusMode(nextState);
  };

  const pulseScale = 1 + (audioLevel || 0) * 0.25;

  return (
    <div className="absolute top-4 right-4 z-30 w-72 flex flex-col gap-3">
      {/* 1. Filter-Legende */}
      <div className="rounded-xl glass-panel p-3">
        <div className="flex items-center justify-between text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-2 border-b border-[#1f242d] pb-1.5">
          <span>Kategorien Filter</span>
          <span className="text-[#00d4ff]">{activeFilter.size}/9</span>
        </div>
        <div className="grid grid-cols-3 gap-1.5">
          {(Object.keys(CATEGORY_COLORS) as NodeCategory[]).map((cat) => {
            const isActive = activeFilter.has(cat);
            return (
              <button
                key={cat}
                onClick={() => onToggleFilter(cat)}
                title={`Kategorie ${cat} im Wissensgraphen filtern (${categoryCounts[cat] || 0} Knoten)`}
                className={`flex items-center gap-1.5 px-2 py-1 rounded text-[10px] transition-all cursor-pointer ${
                  isActive
                    ? "bg-white/10 text-white border border-white/10"
                    : "opacity-40 text-gray-500 hover:opacity-75"
                }`}
              >
                <span
                  className="w-1.5 h-1.5 rounded-full shrink-0"
                  style={{ backgroundColor: CATEGORY_COLORS[cat] }}
                />
                <span className="truncate">{cat}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* 2. J.A.R.V.I.S. Arc Reactor */}
      <div className="rounded-xl glass-panel p-4 flex flex-col items-center">
        <div className="relative w-44 h-44 flex items-center justify-center my-1">
          <svg
            className="w-full h-full transition-transform duration-75"
            viewBox="0 0 200 200"
            style={{ transform: `scale(${pulseScale})` }}
          >
            <circle cx="100" cy="100" r="90" fill="none" stroke="#1f242d" strokeWidth="1.5" />
            <circle
              cx="100" cy="100" r="82" fill="none" stroke="#00d4ff" strokeWidth="1"
              strokeDasharray="4 4" strokeOpacity="0.6"
              transform={`rotate(${(angle * 180) / Math.PI} 100 100)`}
            />
            <circle
              cx="100" cy="100" r="68" fill="none" stroke="#a855f7" strokeWidth="2.5"
              strokeDasharray="25 12" strokeOpacity="0.8"
              transform={`rotate(${(-angle * 180) / Math.PI * 1.5} 100 100)`}
            />
            <circle
              cx="100" cy="100" r="52" fill="none" stroke="#00d4ff" strokeWidth="2"
              strokeOpacity="0.9" style={{ filter: "drop-shadow(0 0 8px #00d4ff)" }}
            />
            <circle cx="100" cy="100" r="38" fill="rgba(10, 15, 25, 0.85)" stroke="#1f242d" strokeWidth="1" />
            <circle
              cx="100" cy="100" r={16 + audioLevel * 14}
              fill="rgba(0, 212, 255, 0.25)"
              style={{ filter: "drop-shadow(0 0 10px #00d4ff)" }}
            />
            <text x="100" y="104" textAnchor="middle" fill="#ffffff" fontSize="10" fontWeight="900" letterSpacing="2" fontFamily="monospace">
              CYPHER
            </text>
          </svg>

          {state === "SPEAKING" && (
            <button
              onClick={handleInterrupt}
              title="Sprachausgabe sofort unterbrechen"
              className="absolute bottom-1 px-3 py-1 rounded-full bg-red-500/20 text-red-400 border border-red-500/40 text-[10px] font-bold tracking-wider hover:bg-red-500/30 transition-all animate-pulse cursor-pointer"
            >
              INTERRUPT
            </button>
          )}
        </div>

        {/* Paranoia Killswitch Status Badge */}
        <div className="w-full mt-2 mb-1">
          <button
            onClick={handleToggleParanoia}
            title={paranoiaMuted ? "Mikrofon-Hardware-Stream reaktivieren" : "Paranoia Killswitch: Mikrofon-Stream auf Treiberebene killen"}
            className={`w-full py-1.5 px-3 rounded-lg border text-xs font-mono font-bold flex items-center justify-center gap-2 transition-all cursor-pointer ${
              paranoiaMuted
                ? "bg-red-500/20 border-red-500 text-red-400 shadow-[0_0_12px_rgba(239,68,68,0.5)] animate-pulse"
                : "bg-[#22c55e]/15 border-[#22c55e]/50 text-[#22c55e] hover:bg-[#22c55e]/25"
            }`}
          >
            {paranoiaMuted ? (
              <>
                <ShieldAlert className="w-3.5 h-3.5 text-red-400" />
                <span>PARANOIA MUTED (HARDWARE-OFF)</span>
              </>
            ) : (
              <>
                <span className="w-2 h-2 rounded-full bg-[#22c55e] animate-ping" />
                <span>MIC LIVE (PIPEWIRE ACTIVE)</span>
              </>
            )}
          </button>
        </div>

        {/* Status Badges */}
        <div className="flex items-center gap-2 w-full mt-2">
          <div 
            className="flex-1 flex items-center justify-center gap-1.5 py-1 rounded-lg bg-[#080a0f]/80 border border-[#1f242d] text-[11px] font-bold"
            title={`Aktueller Assistenten-Status: ${state}`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                state === "ONLINE"
                  ? "bg-[#22c55e] shadow-[0_0_8px_#22c55e]"
                  : state === "SPEAKING"
                  ? "bg-[#00d4ff] animate-ping"
                  : state === "LISTENING"
                  ? "bg-[#eab308] animate-pulse"
                  : "bg-red-500"
              }`}
            />
            <span className="text-gray-200">{state}</span>
          </div>

          <button
            onClick={onOpenApiKeyModal}
            className="flex-1 flex items-center justify-center gap-1.5 py-1 px-2 rounded-lg bg-[#a855f7]/15 hover:bg-[#a855f7]/30 border border-[#a855f7]/40 hover:border-[#a855f7]/70 text-[10px] font-bold text-[#a855f7] transition-all cursor-pointer shadow-sm shadow-[#a855f7]/10"
            title="Gemini API Key einsehen oder ändern"
          >
            <KeyRound className="w-3 h-3 text-[#a855f7]" />
            <span>GEMINI 2.5 LIVE</span>
          </button>
        </div>

        {/* Live Status Zeile */}
        <div className="w-full text-center mt-2.5 text-[11px] font-mono text-gray-400 truncate">
          {state === "LISTENING" && "● listening to you, sir..."}
          {state === "SPEAKING" && "● vocalizing response..."}
          {state === "THINKING" && "● orchestrating neural tools..."}
          {state === "ONLINE" && "● standby, awaiting command"}
          {state === "OFFLINE" && "● offline, connecting backend..."}
        </div>
      </div>

      {/* 3. Sensor-Matrix */}
      <div className="rounded-xl glass-panel p-3">
        <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-2">
          Sensor / Mode Matrix
        </div>
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => {
              const next = !sensorEyes;
              setSensorEyes(next);
              if (next) {
                socketManager.triggerTool("analyze_screen", { prompt: "Prüfe den Bildschirm auf Anomalien oder aktive Fenster." });
              }
            }}
            className={`flex items-center justify-between px-2.5 py-1.5 rounded-lg border text-xs transition-colors cursor-pointer ${
              sensorEyes ? "bg-[#00d4ff]/15 border-[#00d4ff]/40 text-white shadow-sm shadow-[#00d4ff]/20" : "bg-[#080a0f]/60 border-[#1f242d] text-gray-400 hover:text-white"
            }`}
            title="Screen-Vision & Screenshot-Analyse ausführen"
          >
            <span className="flex items-center gap-1.5"><Eye className="w-3.5 h-3.5" /> EYES</span>
            <span className={`text-[10px] ${sensorEyes ? "text-[#00d4ff]" : "text-gray-500"}`}>{sensorEyes ? "on" : "off"}</span>
          </button>

          <button
            onClick={() => {
              const next = !sensorWatch;
              setSensorWatch(next);
              socketManager.sendText(next ? "System-Hinweis: Proaktiver WATCH-Überwachungsmodus aktiviert." : "System-Hinweis: WATCH-Modus deaktiviert.");
            }}
            className={`flex items-center justify-between px-2.5 py-1.5 rounded-lg border text-xs transition-colors cursor-pointer ${
              sensorWatch ? "bg-[#22c55e]/15 border-[#22c55e]/40 text-white shadow-sm shadow-[#22c55e]/20" : "bg-[#080a0f]/60 border-[#1f242d] text-gray-400 hover:text-white"
            }`}
            title="Proaktiven Überwachungsmodus umschalten"
          >
            <span className="flex items-center gap-1.5"><Radio className="w-3.5 h-3.5" /> WATCH</span>
            <span className={`text-[10px] ${sensorWatch ? "text-[#22c55e]" : "text-gray-500"}`}>{sensorWatch ? "on" : "off"}</span>
          </button>

          <button
            onClick={() => {
              const next = !sensorHolo;
              setSensorHolo(next);
            }}
            className={`flex items-center justify-between px-2.5 py-1.5 rounded-lg border text-xs transition-colors cursor-pointer ${
              sensorHolo ? "bg-[#a855f7]/15 border-[#a855f7]/40 text-white shadow-sm shadow-[#a855f7]/20" : "bg-[#080a0f]/60 border-[#1f242d] text-gray-400 hover:text-white"
            }`}
            title="Holo-Visualisierungsmodus umschalten"
          >
            <span className="flex items-center gap-1.5"><Grid className="w-3.5 h-3.5" /> HOLO</span>
            <span className={`text-[10px] ${sensorHolo ? "text-[#a855f7]" : "text-gray-500"}`}>{sensorHolo ? "on" : "off"}</span>
          </button>

          <button
            onClick={handleToggleFocusMode}
            className={`flex items-center justify-between px-2.5 py-1.5 rounded-lg border text-xs transition-colors cursor-pointer ${
              focusMode ? "bg-[#eab308]/20 border-[#eab308]/60 text-white shadow-[0_0_10px_rgba(234,179,8,0.4)]" : "bg-[#080a0f]/60 border-[#1f242d] text-gray-400 hover:text-white"
            }`}
            title="Focus Mode: Friert Heartbeat & Cronjobs ein (100% CPU für Gaming & Compiles)"
          >
            <span className="flex items-center gap-1.5"><Crosshair className="w-3.5 h-3.5" /> FOCUS</span>
            <span className={`text-[10px] font-bold ${focusMode ? "text-[#eab308]" : "text-gray-500"}`}>{focusMode ? "on" : "off"}</span>
          </button>
        </div>

        {/* Paranoia Quick Action */}
        <div className="mt-2.5 pt-2 border-t border-[#1f242d] flex justify-between items-center text-xs text-gray-300">
          <span title="Treiberebene-Mikrofonstatus">Hardware Mic-Stream</span>
          <button
            onClick={handleToggleParanoia}
            title={paranoiaMuted ? "Hardware-Stream reaktivieren" : "Hardware-Stream sofort kappen"}
            className={`p-1.5 rounded-md border text-xs flex items-center gap-1.5 transition-colors cursor-pointer ${
              paranoiaMuted ? "bg-red-500/20 text-red-400 border-red-500/40" : "bg-[#22c55e]/20 text-[#22c55e] border-[#22c55e]/40"
            }`}
          >
            {paranoiaMuted ? <MicOff className="w-3.5 h-3.5" /> : <Mic className="w-3.5 h-3.5" />}
            <span>{paranoiaMuted ? "Gesperrt" : "Verbunden"}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
