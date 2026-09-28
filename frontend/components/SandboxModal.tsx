"use client";

import React, { useState, useEffect } from "react";
import { socketManager } from "@/lib/websocket";
import { SandboxConfig } from "@/lib/types";
import { 
  Shield, ShieldAlert, ShieldCheck, FolderPlus, Trash2, Folder, 
  X, CheckCircle2, AlertTriangle, Lock, Unlock, HardDrive, Terminal
} from "lucide-react";

interface SandboxModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SandboxModal: React.FC<SandboxModalProps> = ({ isOpen, onClose }) => {
  const [config, setConfig] = useState<SandboxConfig>({
    allowed_paths: [],
    full_os_access: false
  });
  const [newPath, setNewPath] = useState("");
  const [feedback, setFeedback] = useState<string | null>(null);

  useEffect(() => {
    const unsub = socketManager.onSandboxConfig((cfg) => {
      if (cfg) setConfig(cfg);
    });
    return () => unsub();
  }, []);

  useEffect(() => {
    if (isOpen) {
      socketManager.requestSandboxConfig();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleToggleFullOs = () => {
    const nextState = !config.full_os_access;
    setConfig((prev) => ({ ...prev, full_os_access: nextState }));
    socketManager.setFullOsAccess(nextState);
    setFeedback(
      nextState
        ? "⚠️ Uneingeschränkter OS-Vollzugriff aktiviert!"
        : "🛡️ Sandbox-Schutz wiederhergestellt. Jarvis arbeitet wieder isoliert."
    );
    setTimeout(() => setFeedback(null), 4000);
  };

  const handleAddPath = (e: React.FormEvent) => {
    e.preventDefault();
    const clean = newPath.trim();
    if (!clean) return;
    socketManager.addSandboxPath(clean);
    setNewPath("");
    setFeedback(`Pfad '${clean}' hinzugefügt.`);
    setTimeout(() => setFeedback(null), 3000);
  };

  const handleQuickAdd = (pathStr: string) => {
    socketManager.addSandboxPath(pathStr);
    setFeedback(`Pfad '${pathStr}' freigegeben.`);
    setTimeout(() => setFeedback(null), 3000);
  };

  const handleRemovePath = (pathStr: string) => {
    socketManager.removeSandboxPath(pathStr);
    setFeedback(`Pfad '${pathStr}' aus Sandbox entfernt.`);
    setTimeout(() => setFeedback(null), 3000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-md p-4 animate-in fade-in duration-150">
      <div className="w-full max-w-2xl rounded-2xl glass-panel-glow bg-[#0a0d14]/95 border border-[#00d4ff]/30 shadow-2xl p-6 flex flex-col gap-5 text-gray-200">
        
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#1f242d] pb-3">
          <div className="flex items-center gap-3">
            <div className={`p-2.5 rounded-xl border ${
              config.full_os_access 
                ? "bg-red-500/20 border-red-500/50 text-red-400 shadow-[0_0_15px_rgba(239,68,68,0.4)]" 
                : "bg-[#00d4ff]/15 border-[#00d4ff]/40 text-[#00d4ff]"
            }`}>
              {config.full_os_access ? <ShieldAlert className="w-6 h-6 animate-pulse" /> : <ShieldCheck className="w-6 h-6" />}
            </div>
            <div>
              <h2 className="text-base font-black tracking-wider uppercase text-white flex items-center gap-2">
                <span>Sandbox- & OS-Sicherheitsmatrix</span>
                <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono font-bold uppercase ${
                  config.full_os_access 
                    ? "bg-red-500/20 text-red-400 border border-red-500/40" 
                    : "bg-[#22c55e]/20 text-[#22c55e] border border-[#22c55e]/40"
                }`}>
                  {config.full_os_access ? "UNRESTRICTED OS" : "SANDBOX PROTECTED"}
                </span>
              </h2>
              <p className="text-xs text-gray-400">
                Isolierung, erlaubte Arbeitsverzeichnisse & uneingeschränkter Systemzugriff
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-white/10 text-gray-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Feedback Banner */}
        {feedback && (
          <div className={`px-4 py-2 rounded-xl text-xs font-mono font-bold flex items-center gap-2 border animate-in fade-in ${
            feedback.includes("⚠️") 
              ? "bg-red-500/20 border-red-500/50 text-red-300" 
              : "bg-[#22c55e]/20 border-[#22c55e]/50 text-[#22c55e]"
          }`}>
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{feedback}</span>
          </div>
        )}

        {/* 1. Große Steuerkarte: Voller OS-Zugriff Switch */}
        <div className={`p-4 rounded-xl border transition-all ${
          config.full_os_access
            ? "bg-red-950/30 border-red-500/50 shadow-[0_0_20px_rgba(239,68,68,0.25)]"
            : "bg-[#080a0f]/80 border-[#1f242d] hover:border-white/10"
        }`}>
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-start gap-3">
              <div className={`p-2 rounded-lg mt-0.5 ${
                config.full_os_access ? "bg-red-500/20 text-red-400" : "bg-white/5 text-gray-400"
              }`}>
                {config.full_os_access ? <Unlock className="w-5 h-5" /> : <Lock className="w-5 h-5" />}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-bold text-white">
                    Uneingeschränkter OS-Vollzugriff
                  </h3>
                  <span className="text-[10px] text-gray-400 font-mono">
                    (Temporär für diese Sitzung)
                  </span>
                </div>
                <p className="text-xs text-gray-400 mt-1 leading-relaxed">
                  {config.full_os_access ? (
                    <span className="text-red-300 font-medium">
                      ⚠️ Jarvis besitzt derzeit vollen Zugriff auf dein Host-Betriebssystem. Dateien können überall gelesen, geschrieben, erstellt und gelöscht werden.
                    </span>
                  ) : (
                    <span>
                      Standardmäßig isoliert: Jarvis darf Shell-Befehle und Dateimanipulationen nur in den unten explizit freigegebenen Sandbox-Verzeichnissen ausführen.
                    </span>
                  )}
                </p>
                <div className="text-[11px] text-gray-500 font-mono mt-1">
                  Direktive: Bleibt exakt solange aktiv, bis du erneut klickst oder Jarvis neu gestartet wird.
                </div>
              </div>
            </div>

            <button
              onClick={handleToggleFullOs}
              className={`px-4 py-2.5 rounded-xl font-mono text-xs font-bold shrink-0 flex items-center gap-2 transition-all cursor-pointer ${
                config.full_os_access
                  ? "bg-red-600 hover:bg-red-700 text-white shadow-lg shadow-red-600/40 animate-pulse"
                  : "bg-white/10 hover:bg-white/20 text-white border border-white/20"
              }`}
            >
              {config.full_os_access ? (
                <>
                  <Lock className="w-4 h-4" />
                  <span>OS-VOLLZUGRIFF BEENDEN</span>
                </>
              ) : (
                <>
                  <Unlock className="w-4 h-4 text-amber-400" />
                  <span>VOLLZUGRIFF AKTIVIEREN</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* 2. Erlaubte Sandbox-Arbeitsverzeichnisse */}
        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase tracking-wider text-gray-300 flex items-center gap-2">
              <Folder className="w-4 h-4 text-[#00d4ff]" />
              <span>Freigegebene Arbeitsverzeichnisse (Lesen, Schreiben & Unterordner)</span>
            </h3>
            <span className="text-[10px] font-mono text-[#00d4ff]">
              {config.allowed_paths?.length || 0} Pfade aktiv
            </span>
          </div>

          {/* Formular zum Hinzufügen */}
          <form onSubmit={handleAddPath} className="flex gap-2">
            <div className="relative flex-1">
              <input
                type="text"
                value={newPath}
                onChange={(e) => setNewPath(e.target.value)}
                placeholder="z. B. ~/workspace oder ~/projekte"
                className="w-full bg-[#080a0f] border border-[#1f242d] rounded-xl px-3.5 py-2 text-xs font-mono text-white placeholder-gray-600 focus:outline-none focus:border-[#00d4ff]/60"
              />
            </div>
            <button
              type="submit"
              disabled={!newPath.trim()}
              className="px-4 py-2 rounded-xl bg-[#00d4ff]/20 hover:bg-[#00d4ff]/30 text-[#00d4ff] border border-[#00d4ff]/40 text-xs font-bold font-mono flex items-center gap-1.5 disabled:opacity-40 transition-all cursor-pointer"
            >
              <FolderPlus className="w-4 h-4" />
              <span>Hinzufügen</span>
            </button>
          </form>

          {/* Quick Suggestions Chips */}
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-[10px] text-gray-500 font-mono">Schnellwahl:</span>
            {[
              "~/workspace",
              "~/Schreibtisch",
              "~/Downloads"
            ].map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => handleQuickAdd(s)}
                className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-white/5 hover:bg-white/10 text-gray-300 border border-[#1f242d] transition-colors cursor-pointer"
              >
                + {s}
              </button>
            ))}
          </div>

          {/* Liste der Pfade */}
          <div className="max-h-52 overflow-y-auto flex flex-col gap-2 mt-1 pr-1">
            {config.allowed_paths && config.allowed_paths.length > 0 ? (
              config.allowed_paths.map((p, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-2.5 rounded-xl bg-[#080a0f] border border-[#1f242d] hover:border-[#1f242d]/80 text-xs font-mono group transition-colors"
                >
                  <div className="flex items-center gap-2.5 truncate pr-2">
                    <HardDrive className="w-4 h-4 text-[#00d4ff] shrink-0" />
                    <span className="text-gray-200 truncate">{p}</span>
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-[#22c55e]/15 text-[#22c55e] border border-[#22c55e]/30 shrink-0">
                      R/W + Subdirs
                    </span>
                  </div>
                  <button
                    onClick={() => handleRemovePath(p)}
                    className="p-1.5 rounded-lg text-gray-500 hover:text-red-400 hover:bg-red-500/10 transition-colors cursor-pointer"
                    title={`Pfad '${p}' aus Sandbox entfernen`}
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))
            ) : (
              <div className="p-4 rounded-xl bg-[#080a0f] border border-dashed border-[#1f242d] text-center text-xs text-gray-500 font-mono">
                Keine benutzerdefinierten Pfade hinterlegt. Jarvis nutzt das Standard-Workspace-Verzeichnis.
              </div>
            )}
          </div>
        </div>

        {/* Footer Info */}
        <div className="pt-2 border-t border-[#1f242d] flex items-center justify-between text-[11px] text-gray-500 font-mono">
          <span className="flex items-center gap-1.5">
            <Terminal className="w-3.5 h-3.5 text-[#00d4ff]" />
            Bubblewrap bwrap & direct host fallback bereit
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-white font-sans text-xs font-semibold transition-colors cursor-pointer"
          >
            Schließen
          </button>
        </div>

      </div>
    </div>
  );
};
