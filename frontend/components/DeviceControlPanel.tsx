"use client";

import React, { useState, useEffect } from "react";
import { socketManager } from "@/lib/websocket";
import { TelemetryData } from "@/lib/types";
import { 
  Laptop, Volume2, Sun, Wifi, RotateCcw, FolderCheck, 
  Terminal, AppWindow, Cpu, HardDrive, Thermometer, ShieldAlert, X, KeyRound,
  Mic, Sparkles
} from "lucide-react";

interface DeviceControlPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onOpenApiKeyModal?: () => void;
}

export const DeviceControlPanel: React.FC<DeviceControlPanelProps> = ({ 
  isOpen, 
  onClose, 
  onOpenApiKeyModal
}) => {
  const [telemetry, setTelemetry] = useState<TelemetryData | null>(null);
  const [volume, setVolume] = useState(50);
  const [brightness, setBrightness] = useState(80);
  const [voice, setVoice] = useState<string>("Puck");

  useEffect(() => {
    const unsub = socketManager.onTelemetry(setTelemetry);
    const unsubVoice = socketManager.onVoiceChange(setVoice);
    return () => {
      unsub();
      unsubVoice();
    };
  }, []);

  if (!isOpen) return null;

  const handleVolumeChange = (val: number) => {
    setVolume(val);
    socketManager.triggerTool("computer_settings", { action: "volume", value: String(val) });
  };

  const handleBrightnessChange = (val: number) => {
    setBrightness(val);
    socketManager.triggerTool("computer_settings", { action: "brightness", value: String(val) });
  };

  const handleLaunchApp = (appName: string) => {
    socketManager.triggerTool("open_app", { app_name: appName });
  };

  const handleOrganizeDesktop = () => {
    socketManager.triggerTool("file_controller", { action: "organize_desktop" });
  };

  const handleUndo = () => {
    socketManager.triggerUndo();
  };

  const handleReboot = () => {
    socketManager.triggerTool("computer_settings", { action: "reboot" });
  };

  const handleShutdown = () => {
    socketManager.triggerTool("computer_settings", { action: "shutdown" });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="w-full max-w-xl rounded-2xl glass-panel-glow bg-[#0a0d14]/95 p-5 shadow-2xl border border-[#00d4ff]/30 animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#1f242d] pb-3 mb-4">
          <div className="flex items-center gap-2">
            <Laptop className="w-5 h-5 text-[#00d4ff]" />
            <div>
              <h2 className="text-sm font-black tracking-wider uppercase text-white">
                CachyOS Linux Hardware Bridge
              </h2>
              <p className="text-[10px] text-gray-400">
                PipeWire · Brightnessctl · NetworkManager · Systemd
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-white/10 text-gray-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Telemetrie Schnellübersicht */}
        {telemetry && (
          <div className="grid grid-cols-4 gap-2 mb-4">
            <div className="rounded-lg bg-[#080a0f] border border-[#1f242d] p-2 text-center">
              <Cpu className="w-4 h-4 mx-auto text-[#00d4ff] mb-1" />
              <div className="text-[10px] text-gray-400">CPU Load</div>
              <div className="text-xs font-bold text-white">{telemetry.cpu_percent}%</div>
            </div>
            <div className="rounded-lg bg-[#080a0f] border border-[#1f242d] p-2 text-center">
              <HardDrive className="w-4 h-4 mx-auto text-[#22c55e] mb-1" />
              <div className="text-[10px] text-gray-400">RAM Belegt</div>
              <div className="text-xs font-bold text-white">{telemetry.ram_used_gb} GB</div>
            </div>
            <div className="rounded-lg bg-[#080a0f] border border-[#1f242d] p-2 text-center">
              <Thermometer className="w-4 h-4 mx-auto text-[#ff6b00] mb-1" />
              <div className="text-[10px] text-gray-400">Disk Frei</div>
              <div className="text-xs font-bold text-white">{telemetry.disk_free_gb} GB</div>
            </div>
            <div className="rounded-lg bg-[#080a0f] border border-[#1f242d] p-2 text-center">
              <Wifi className="w-4 h-4 mx-auto text-[#a855f7] mb-1" />
              <div className="text-[10px] text-gray-400">Swap</div>
              <div className="text-xs font-bold text-white">{telemetry.swap_percent}%</div>
            </div>
          </div>
        )}

        {/* Hardware Regler */}
        <div className="flex flex-col gap-3 rounded-xl bg-[#080a0f]/60 border border-[#1f242d] p-3 mb-4">
          <div>
            <div className="flex justify-between text-xs text-gray-300 mb-1">
              <span className="flex items-center gap-1.5"><Volume2 className="w-3.5 h-3.5 text-[#00d4ff]" /> PipeWire Lautstärke</span>
              <span className="font-mono text-[#00d4ff]">{volume}%</span>
            </div>
            <input
              type="range" min="0" max="100" value={volume}
              onChange={(e) => handleVolumeChange(Number(e.target.value))}
              className="w-full accent-[#00d4ff] bg-gray-800 h-1.5 rounded"
            />
          </div>

          <div>
            <div className="flex justify-between text-xs text-gray-300 mb-1">
              <span className="flex items-center gap-1.5"><Sun className="w-3.5 h-3.5 text-[#eab308]" /> Display Helligkeit</span>
              <span className="font-mono text-[#eab308]">{brightness}%</span>
            </div>
            <input
              type="range" min="5" max="100" value={brightness}
              onChange={(e) => handleBrightnessChange(Number(e.target.value))}
              className="w-full accent-[#eab308] bg-gray-800 h-1.5 rounded"
            />
          </div>
        </div>

        {/* Jarvis KI-Stimme & Companion Steuerungsmatrix */}
        <div className="flex flex-col gap-2 rounded-xl bg-[#080a0f]/80 border border-[#1f242d] p-3 mb-4">
          <div className="flex items-center justify-between text-[11px] font-bold text-gray-300">
            <span className="flex items-center gap-1.5 text-[#00d4ff]">
              <Mic className="w-3.5 h-3.5" />
              <span>Jarvis KI-Stimme (TTS Engine)</span>
            </span>
            <span className="font-mono text-[10px] text-gray-400">
              Aktiv: <strong className="text-white">{voice === "Aoede" ? "Weiblich (Aoede)" : "Männlich (Puck)"}</strong>
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => socketManager.setVoice("Puck")}
              className={`flex items-center justify-center gap-2 py-2 px-3 rounded-lg border text-xs font-semibold transition-all cursor-pointer ${
                voice !== "Aoede"
                  ? "bg-[#00d4ff]/20 border-[#00d4ff] text-cyan-300 shadow-[0_0_12px_rgba(0,212,255,0.35)]"
                  : "bg-white/5 border-white/10 text-gray-400 hover:bg-white/10 hover:text-white"
              }`}
            >
              <span>👨</span>
              <span>Männlich (Puck / Standard)</span>
            </button>

            <button
              type="button"
              onClick={() => socketManager.setVoice("Aoede")}
              className={`flex items-center justify-center gap-2 py-2 px-3 rounded-lg border text-xs font-semibold transition-all cursor-pointer ${
                voice === "Aoede"
                  ? "bg-pink-500/20 border-pink-500 text-pink-300 shadow-[0_0_12px_rgba(244,114,182,0.35)]"
                  : "bg-white/5 border-white/10 text-gray-400 hover:bg-white/10 hover:text-white"
              }`}
            >
              <span>👩</span>
              <span>Weiblich (Aoede / Sanft)</span>
            </button>
          </div>
        </div>

        {/* Anwendungsstarter & System-Aktionen */}
        <div className="flex flex-col gap-2">
          <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">
            Quick Launch & System Tools
          </div>
          <div className="grid grid-cols-4 gap-2">
            {[
              { name: "Brave", cmd: "brave" },
              { name: "Dolphin", cmd: "dolphin" },
              { name: "Konsole", cmd: "konsole" },
              { name: "VS Code", cmd: "code" }
            ].map(app => (
              <button
                key={app.name}
                onClick={() => handleLaunchApp(app.cmd)}
                className="flex items-center justify-center gap-1.5 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-[#1f242d] text-xs text-gray-200 transition-colors"
              >
                <AppWindow className="w-3.5 h-3.5 text-[#00d4ff]" />
                <span>{app.name}</span>
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2 mt-2">
            <button
              onClick={handleOrganizeDesktop}
              className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg bg-[#22c55e]/15 hover:bg-[#22c55e]/25 border border-[#22c55e]/40 text-xs font-semibold text-[#22c55e] transition-colors"
            >
              <FolderCheck className="w-3.5 h-3.5" />
              <span>Schreibtisch Aufräumen</span>
            </button>

            <button
              onClick={handleUndo}
              className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg bg-white/10 hover:bg-white/15 border border-[#1f242d] text-xs font-semibold text-gray-200 transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5 text-gray-400" />
              <span>Undo Last Operation</span>
            </button>
          </div>

          <button
            onClick={() => {
              onClose();
              if (onOpenApiKeyModal) onOpenApiKeyModal();
            }}
            className="w-full flex items-center justify-center gap-1.5 py-2 rounded-lg bg-[#00d4ff]/10 hover:bg-[#00d4ff]/20 border border-[#00d4ff]/30 text-xs font-semibold text-[#00d4ff] transition-colors"
          >
            <KeyRound className="w-3.5 h-3.5" />
            <span>Gemini Live API Key verwalten</span>
          </button>

          {/* Dangerous Zone (Protected by Confirmation Gate) */}
          <div className="flex items-center gap-2 mt-1">
            <button
              onClick={handleReboot}
              className="flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg bg-yellow-600/20 hover:bg-yellow-600/30 border border-yellow-500/40 text-xs text-yellow-400 transition-colors"
            >
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>Neustart anfordern</span>
            </button>
            <button
              onClick={handleShutdown}
              className="flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg bg-red-600/20 hover:bg-red-600/30 border border-red-500/40 text-xs text-red-400 transition-colors"
            >
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>Herunterfahren anfordern</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
