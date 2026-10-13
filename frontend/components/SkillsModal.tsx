"use client";

import React, { useState, useEffect } from "react";
import { socketManager } from "@/lib/websocket";
import { MCPServerMap, MCPServerConfig } from "@/lib/types";
import { 
  Puzzle, 
  Plus, 
  Trash2, 
  X, 
  Terminal, 
  Search,
  Sparkles
} from "lucide-react";

interface SkillsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SkillsModal: React.FC<SkillsModalProps> = ({ isOpen, onClose }) => {
  const [servers, setServers] = useState<MCPServerMap>({});
  const [searchQuery, setSearchQuery] = useState("");
  const [isAddingNew, setIsAddingNew] = useState(false);
  
  const [newId, setNewId] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newCategory, setNewCategory] = useState("Custom");
  const [newCommand, setNewCommand] = useState("npx");
  const [newArgs, setNewArgs] = useState("-y, ");

  useEffect(() => {
    const unsub = socketManager.onMcpServers((data) => {
      setServers(data || {});
    });
    socketManager.requestMcpServers();
    return () => unsub();
  }, []);

  if (!isOpen) return null;

  const serverEntries = Object.entries(servers);
  const activeCount = serverEntries.filter(([_, s]) => s.enabled).length;

  const filteredServers = serverEntries.filter(([id, s]) => {
    const q = searchQuery.toLowerCase();
    return (
      id.toLowerCase().includes(q) ||
      (s.description && s.description.toLowerCase().includes(q)) ||
      (s.category && s.category.toLowerCase().includes(q))
    );
  });

  const handleToggle = (id: string, currentStatus: boolean) => {
    socketManager.toggleMcpServer(id, !currentStatus);
  };

  const handleDelete = (id: string) => {
    if (confirm(`MCP-Skill '${id}' wirklich entfernen?`)) {
      socketManager.deleteMcpServer(id);
    }
  };

  const handleAddSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newId.trim() || !newCommand.trim()) return;

    const parsedArgs = newArgs
      .split(",")
      .map((a) => a.trim())
      .filter(Boolean);

    const newConfig: MCPServerConfig = {
      command: newCommand.trim(),
      args: parsedArgs,
      description: newDesc.trim() || "Benutzerdefinierter MCP-Skill",
      category: newCategory.trim() || "Custom",
      enabled: false
    };

    socketManager.saveMcpServer(newId.trim(), newConfig);
    setIsAddingNew(false);
    setNewId("");
    setNewDesc("");
    setNewArgs("-y, ");
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-md p-4 animate-in fade-in duration-150">
      <div className="w-full max-w-2xl max-h-[85vh] flex flex-col rounded-2xl glass-panel-glow bg-[#0a0d14]/95 shadow-2xl border border-[#00d4ff]/40 overflow-hidden">
        
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#1f242d] p-5 bg-[#0e131d]/60">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-[#00d4ff]/10 border border-[#00d4ff]/30 text-[#00d4ff]">
              <Puzzle className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-black tracking-wider uppercase text-white">
                  MCP Skill Matrix
                </h2>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#00d4ff]/20 text-[#00d4ff] border border-[#00d4ff]/30">
                  {activeCount} / {serverEntries.length} Aktiv
                </span>
              </div>
              <p className="text-xs text-gray-400">
                Model Context Protocol · Modulare KI-Fähigkeiten & Stdio-Bridges
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

        {/* Toolbar */}
        <div className="p-4 border-b border-[#1f242d] flex flex-wrap items-center justify-between gap-3 bg-[#0a0d14]/40">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="w-4 h-4 text-gray-500 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Skills durchsuchen..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-[#141822] border border-[#2a3040] text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-[#00d4ff]"
            />
          </div>
          <button
            onClick={() => setIsAddingNew(!isAddingNew)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#00d4ff]/20 hover:bg-[#00d4ff]/30 border border-[#00d4ff]/40 text-[#00d4ff] text-xs font-semibold transition-all"
          >
            <Plus className="w-4 h-4" />
            Neuer MCP-Skill
          </button>
        </div>

        {/* Formular für neuen Skill */}
        {isAddingNew && (
          <form onSubmit={handleAddSubmit} className="p-4 border-b border-[#1f242d] bg-[#111726]/70 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-[#00d4ff]" /> Neuen MCP-Server registrieren
              </span>
              <button
                type="button"
                onClick={() => setIsAddingNew(false)}
                className="text-[11px] text-gray-400 hover:text-white"
              >
                Abbrechen
              </button>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <input
                type="text"
                placeholder="ID (z. B. postgres)"
                value={newId}
                onChange={(e) => setNewId(e.target.value)}
                className="px-2.5 py-1.5 rounded bg-[#141822] border border-[#2a3040] text-xs text-white placeholder-gray-500 focus:outline-none focus:border-[#00d4ff]"
                required
              />
              <input
                type="text"
                placeholder="Kategorie (z. B. Database)"
                value={newCategory}
                onChange={(e) => setNewCategory(e.target.value)}
                className="px-2.5 py-1.5 rounded bg-[#141822] border border-[#2a3040] text-xs text-white placeholder-gray-500 focus:outline-none focus:border-[#00d4ff]"
              />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              <input
                type="text"
                placeholder="Befehl (npx / uvx / python)"
                value={newCommand}
                onChange={(e) => setNewCommand(e.target.value)}
                className="px-2.5 py-1.5 rounded bg-[#141822] border border-[#2a3040] text-xs text-white placeholder-gray-500 focus:outline-none focus:border-[#00d4ff]"
                required
              />
              <input
                type="text"
                placeholder="Argumente (kommagetrennt: -y, @pkg/name)"
                value={newArgs}
                onChange={(e) => setNewArgs(e.target.value)}
                className="sm:col-span-2 px-2.5 py-1.5 rounded bg-[#141822] border border-[#2a3040] text-xs text-white placeholder-gray-500 focus:outline-none focus:border-[#00d4ff]"
              />
            </div>
            <input
              type="text"
              placeholder="Kurzbeschreibung der Fähigkeiten..."
              value={newDesc}
              onChange={(e) => setNewDesc(e.target.value)}
              className="w-full px-2.5 py-1.5 rounded bg-[#141822] border border-[#2a3040] text-xs text-white placeholder-gray-500 focus:outline-none focus:border-[#00d4ff]"
            />
            <button
              type="submit"
              className="w-full py-1.5 rounded bg-[#00d4ff] hover:bg-[#00b8dd] text-black font-bold text-xs transition-colors"
            >
              Skill speichern (Deaktiviert hinterlegen)
            </button>
          </form>
        )}

        {/* Server Cards Liste */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2.5">
          {filteredServers.length === 0 ? (
            <div className="py-12 text-center text-gray-500 text-xs">
              Keine MCP-Skills gefunden.
            </div>
          ) : (
            filteredServers.map(([id, server]) => {
              const isEnabled = !!server.enabled;
              return (
                <div
                  key={id}
                  className={`p-3.5 rounded-xl border transition-all ${
                    isEnabled
                      ? "bg-[#0b1b2b]/60 border-[#00d4ff]/50 shadow-[0_0_15px_rgba(0,212,255,0.15)]"
                      : "bg-[#0f141f]/40 border-[#1f242d] hover:border-[#2a3040]"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap mb-1">
                        <span className="text-xs font-bold text-white tracking-wide">
                          {id}
                        </span>
                        {server.category && (
                          <span className="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-[#1e2536] text-gray-300 border border-[#2b334a]">
                            {server.category}
                          </span>
                        )}
                        <span
                          className={`flex items-center gap-1 text-[10px] font-bold ${
                            isEnabled ? "text-[#00ff88]" : "text-gray-500"
                          }`}
                        >
                          <span
                            className={`w-1.5 h-1.5 rounded-full ${
                              isEnabled ? "bg-[#00ff88] animate-pulse" : "bg-gray-600"
                            }`}
                          />
                          {isEnabled ? "AKTIV" : "INAKTIV"}
                        </span>
                      </div>
                      <p className="text-[11px] text-gray-400 mb-2 leading-relaxed">
                        {server.description || "Keine Beschreibung verfügbar."}
                      </p>
                      <div className="flex items-center gap-1.5 text-[10px] text-gray-500 font-mono bg-black/40 px-2 py-1 rounded w-fit max-w-full overflow-hidden text-ellipsis">
                        <Terminal className="w-3 h-3 text-gray-400 shrink-0" />
                        <span className="truncate">
                          {server.command} {server.args?.join(" ")}
                        </span>
                      </div>
                    </div>

                    {/* Actions: Toggle Switch & Delete */}
                    <div className="flex items-center gap-2 pt-1 shrink-0">
                      <button
                        type="button"
                        onClick={() => handleToggle(id, isEnabled)}
                        className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                          isEnabled ? "bg-[#00d4ff]" : "bg-gray-700"
                        }`}
                        title={isEnabled ? "Skill deaktivieren" : "Skill aktivieren"}
                      >
                        <span
                          className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                            isEnabled ? "translate-x-5" : "translate-x-0"
                          }`}
                        />
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDelete(id)}
                        className="p-1.5 rounded text-gray-500 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                        title="Skill entfernen"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-[#1f242d] bg-[#0a0d14]/80 flex items-center justify-between text-[11px] text-gray-500">
          <span>
            Änderungen werden sofort in <code className="text-gray-400">backend/config/mcp_servers.json</code> gespeichert.
          </span>
          <button
            onClick={onClose}
            className="px-3 py-1 rounded-lg bg-white/10 hover:bg-white/20 text-white font-semibold transition-colors"
          >
            Schließen
          </button>
        </div>

      </div>
    </div>
  );
};
