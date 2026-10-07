"use client";

import React, { useState, useEffect } from "react";
import { socketManager } from "@/lib/websocket";
import { TaskItem } from "@/lib/types";
import { 
  CheckSquare, Square, Trash2, Plus, X, ListTodo, 
  AlertCircle, Sparkles, Filter, CheckCircle2,
  ChevronUp, ChevronDown
} from "lucide-react";

interface BacklogDrawerProps {
  onClose: () => void;
}

export const BacklogDrawer: React.FC<BacklogDrawerProps> = ({ onClose }) => {
  const [tasks, setTasks] = useState<TaskItem[]>(socketManager.currentTasks);
  const [filter, setFilter] = useState<"all" | "pending" | "done">("all");
  const [newText, setNewText] = useState("");
  const [newPriority, setNewPriority] = useState<"high" | "normal" | "low">("normal");

  const handleMove = (taskId: string, direction: -1 | 1) => {
    const currentIdx = tasks.findIndex((t) => t.id === taskId);
    if (currentIdx === -1) return;
    const targetIdx = currentIdx + direction;
    if (targetIdx < 0 || targetIdx >= tasks.length) return;
    const newOrder = [...tasks];
    const temp = newOrder[currentIdx];
    newOrder[currentIdx] = newOrder[targetIdx];
    newOrder[targetIdx] = temp;
    setTasks(newOrder);
    socketManager.reorderTasks(newOrder.map((t) => t.id));
  };

  useEffect(() => {
    const unsub = socketManager.onTasks((updated) => {
      setTasks([...updated]);
    });
    return () => unsub();
  }, []);

  const handleToggle = (taskId: string, currentCompleted: boolean) => {
    socketManager.toggleTask(taskId, !currentCompleted);
  };

  const handleAdd = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!newText.trim()) return;
    socketManager.addTask(newText.trim(), newPriority);
    setNewText("");
  };

  const handleDelete = (taskId: string) => {
    socketManager.deleteTask(taskId);
  };

  const completedCount = tasks.filter((t) => t.completed).length;
  const pendingCount = tasks.length - completedCount;

  const filteredTasks = tasks.filter((t) => {
    if (filter === "pending") return !t.completed;
    if (filter === "done") return t.completed;
    return true;
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="flex flex-col w-full max-w-2xl max-h-[85vh] bg-gray-950/95 border border-cyan-500/40 rounded-xl shadow-[0_0_50px_rgba(0,240,255,0.15)] overflow-hidden font-mono">
        
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-cyan-500/20 bg-gray-900/60">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-cyan-500/10 border border-cyan-500/30 rounded-lg text-cyan-400">
              <ListTodo className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold tracking-wider text-white uppercase">
                  Task-Matrix // Single Source of Truth
                </h2>
                <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-950 border border-cyan-500/40 text-cyan-400 font-bold">
                  backlog.md
                </span>
              </div>
              <p className="text-xs text-gray-400 mt-0.5">
                Atomarer POSIX-Sync mit Next.js, Gemini Live und lokalen Editoren.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800/80 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Status- & Filter-Bar */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-gray-800 bg-gray-900/30 text-xs">
          <div className="flex items-center gap-2">
            <span className="text-gray-400">Status:</span>
            <span className="text-emerald-400 font-bold">{completedCount} erledigt</span>
            <span className="text-gray-600">|</span>
            <span className="text-amber-400 font-bold">{pendingCount} offen</span>
          </div>

          <div className="flex items-center gap-1.5 bg-gray-900 p-1 rounded-lg border border-gray-800">
            <button
              onClick={() => setFilter("all")}
              className={`px-2.5 py-1 rounded text-xs transition-colors ${
                filter === "all" ? "bg-cyan-500/20 text-cyan-400 font-bold" : "text-gray-400 hover:text-gray-200"
              }`}
            >
              Alle ({tasks.length})
            </button>
            <button
              onClick={() => setFilter("pending")}
              className={`px-2.5 py-1 rounded text-xs transition-colors ${
                filter === "pending" ? "bg-amber-500/20 text-amber-400 font-bold" : "text-gray-400 hover:text-gray-200"
              }`}
            >
              Offen ({pendingCount})
            </button>
            <button
              onClick={() => setFilter("done")}
              className={`px-2.5 py-1 rounded text-xs transition-colors ${
                filter === "done" ? "bg-emerald-500/20 text-emerald-400 font-bold" : "text-gray-400 hover:text-gray-200"
              }`}
            >
              Fertig ({completedCount})
            </button>
          </div>
        </div>

        {/* Task-Liste */}
        <div className="flex-1 overflow-y-auto p-5 space-y-2.5 min-h-[220px]">
          {filteredTasks.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center text-gray-500">
              <CheckCircle2 className="w-10 h-10 mb-2 stroke-1 text-gray-600" />
              <p className="text-sm font-semibold text-gray-400">Keine Aufgaben in dieser Ansicht.</p>
              <p className="text-xs text-gray-600 mt-1">Füge unten eine neue Aufgabe zu backlog.md hinzu.</p>
            </div>
          ) : (
            filteredTasks.map((t) => (
              <div
                key={t.id}
                className={`flex items-center justify-between p-3 rounded-lg border transition-all ${
                  t.completed
                    ? "bg-gray-900/30 border-gray-800/60 opacity-60"
                    : "bg-gray-900/70 border-cyan-500/20 hover:border-cyan-500/40"
                }`}
              >
                <div className="flex items-center gap-3 flex-1 min-w-0 pr-3">
                  <button
                    onClick={() => handleToggle(t.id, t.completed)}
                    className="flex-shrink-0 text-cyan-400 hover:text-cyan-300 transition-colors"
                  >
                    {t.completed ? (
                      <CheckSquare className="w-5 h-5 text-emerald-400" />
                    ) : (
                      <Square className="w-5 h-5 text-gray-400 hover:text-cyan-400" />
                    )}
                  </button>

                  <div className="flex flex-col min-w-0 flex-1">
                    <span
                      className={`text-sm break-words ${
                        t.completed ? "line-through text-gray-500" : "text-gray-100 font-medium"
                      }`}
                    >
                      {t.text}
                    </span>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-[10px] text-gray-500 font-mono">
                        ID: {t.id}
                      </span>
                      {t.status === "running" && (
                        <span className="text-[10px] text-cyan-400 font-bold animate-pulse flex items-center gap-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />
                          Läuft: {t.status_message || `${t.progress || 0}%`}
                        </span>
                      )}
                    </div>
                    {/* Fortschrittsbalken bei Ausführung */}
                    {typeof t.progress === "number" && t.status === "running" && (
                      <div className="w-full bg-gray-800 h-1 rounded-full mt-1.5 overflow-hidden border border-cyan-500/30">
                        <div
                          className="bg-gradient-to-r from-cyan-500 to-emerald-400 h-full transition-all duration-300"
                          style={{ width: `${Math.min(100, Math.max(0, t.progress))}%` }}
                        />
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2 flex-shrink-0">
                  {/* Task Ausführen Button */}
                  {!t.completed && (
                    <button
                      onClick={() => socketManager.runTask(t.id)}
                      disabled={t.status === "running"}
                      className={`flex items-center gap-1 px-2.5 py-1 rounded text-[11px] font-bold transition-all ${
                        t.status === "running"
                          ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/40 opacity-70"
                          : "bg-cyan-500/15 hover:bg-cyan-500/30 border border-cyan-500/30 text-cyan-300 hover:text-white"
                      }`}
                      title="Aufgabe autonom analysieren, updaten & ausführen"
                    >
                      <Sparkles className="w-3 h-3 text-cyan-400" />
                      <span>{t.status === "running" ? `${t.progress || 0}%` : "Ausführen"}</span>
                    </button>
                  )}
                  {t.priority === "high" && (
                    <span className="text-[10px] px-2 py-0.5 rounded bg-red-950/80 border border-red-500/50 text-red-400 font-bold uppercase">
                      High
                    </span>
                  )}
                  {t.priority === "low" && (
                    <span className="text-[10px] px-2 py-0.5 rounded bg-gray-800 border border-gray-700 text-gray-400 uppercase">
                      Low
                    </span>
                  )}

                  <div className="flex items-center gap-0.5">
                    <button
                      onClick={() => handleMove(t.id, -1)}
                      className="p-1 text-gray-500 hover:text-cyan-400 rounded hover:bg-gray-800 transition-colors"
                      title="Nach oben verschieben"
                    >
                      <ChevronUp className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => handleMove(t.id, 1)}
                      className="p-1 text-gray-500 hover:text-cyan-400 rounded hover:bg-gray-800 transition-colors"
                      title="Nach unten verschieben"
                    >
                      <ChevronDown className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  <button
                    onClick={() => handleDelete(t.id)}
                    className="p-1.5 text-gray-500 hover:text-red-400 rounded hover:bg-gray-800 transition-colors"
                    title="Aufgabe löschen"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Input Footer */}
        <form onSubmit={handleAdd} className="p-4 border-t border-gray-800 bg-gray-900/60">
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={newText}
              onChange={(e) => setNewText(e.target.value)}
              placeholder="Neue Aufgabe für backlog.md..."
              className="flex-1 bg-gray-950 border border-gray-700 rounded-lg px-3.5 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 transition-colors"
            />

            <select
              value={newPriority}
              onChange={(e) => setNewPriority(e.target.value as any)}
              className="bg-gray-950 border border-gray-700 rounded-lg px-2.5 py-2 text-xs text-gray-300 focus:outline-none focus:border-cyan-500"
            >
              <option value="normal">Normal</option>
              <option value="high">Dringend</option>
              <option value="low">Niedrig</option>
            </select>

            <button
              type="submit"
              disabled={!newText.trim()}
              className="flex items-center gap-1.5 px-4 py-2 bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 disabled:hover:bg-cyan-500 text-black font-bold text-xs rounded-lg transition-colors shadow-[0_0_15px_rgba(0,240,255,0.3)]"
            >
              <Plus className="w-4 h-4" />
              <span>Hinzufügen</span>
            </button>
          </div>
        </form>

      </div>
    </div>
  );
};
