"use client";

import React, { useState, useEffect } from "react";
import { socketManager } from "@/lib/websocket";
import { CalendarEvent } from "@/lib/types";
import { 
  Calendar, 
  Clock, 
  Plus, 
  Trash2, 
  Sunrise, 
  Volume2, 
  X, 
  Bell, 
  CalendarDays,
  CheckCircle2,
  Repeat
} from "lucide-react";

interface CalendarModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const CalendarModal: React.FC<CalendarModalProps> = ({ isOpen, onClose }) => {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [autoBriefing, setAutoBriefing] = useState<boolean>(true);
  const [title, setTitle] = useState("");
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [category, setCategory] = useState("Termin");
  const [recurrence, setRecurrence] = useState<"NONE" | "DAILY" | "WEEKLY" | "MONTHLY">("NONE");
  const [reminder, setReminder] = useState("15m");
  const [description, setDescription] = useState("");
  const [feedbackMsg, setFeedbackMsg] = useState<string | null>(null);
  const [briefingTriggered, setBriefingTriggered] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const unsubEvents = socketManager.onCalendarEvents((evList) => {
      setEvents(evList || []);
    });

    const unsubBriefing = socketManager.onAutoBriefing((enabled) => {
      setAutoBriefing(enabled);
    });

    if (isOpen) {
      socketManager.requestCalendarEvents();
      const now = new Date();
      now.setHours(now.getHours() + 1, 0, 0, 0);
      const tzOffset = now.getTimezoneOffset() * 60000;
      const localISOTime = new Date(now.getTime() - tzOffset).toISOString().slice(0, 16);
      setStartTime(localISOTime);
    }

    return () => {
      unsubEvents();
      unsubBriefing();
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || isSubmitting) return;

    setIsSubmitting(true);
    let reminderRules = [{ trigger: "-15m", frequency: "once" }];
    if (reminder === "1h") {
      reminderRules = [{ trigger: "-1h", frequency: "once" }];
    } else if (reminder === "1d") {
      reminderRules = [{ trigger: "-1d", frequency: "daily" }];
    } else if (reminder === "staged_week_hour") {
      reminderRules = [
        { trigger: "-7d", frequency: "daily" },
        { trigger: "-1h", frequency: "once" }
      ];
    } else if (reminder === "none") {
      reminderRules = [];
    }

    const payload = {
      title: title.trim(),
      start_time: startTime || new Date().toISOString(),
      end_time: endTime || undefined,
      description: description.trim(),
      category: category.trim(),
      recurrence_rule: recurrence,
      reminder_strategy: { rules: reminderRules },
      reminder: reminderRules.length > 0 ? `${reminderRules[0].trigger} (${reminderRules[0].frequency})` : "Keine"
    };

    const success = await socketManager.dispatchAuditedAction("CALENDAR_MANUAL_CREATE", payload);
    setIsSubmitting(false);

    if (success) {
      setTitle("");
      setDescription("");
      setEndTime("");
      setRecurrence("NONE");
      setFeedbackMsg("Termin erfolgreich gespeichert & in Echtzeit synchronisiert!");
      setTimeout(() => setFeedbackMsg(null), 2500);
    } else {
      setFeedbackMsg("Warnung: Backend-Quittierung ausstehend. Termin wird synchronisiert.");
      setTimeout(() => setFeedbackMsg(null), 3000);
    }
  };

  const handleDelete = async (id: string | number) => {
    const previousEvents = [...events];
    // Optimistisches Entfernen aus der UI
    setEvents((prev) => prev.filter((ev) => ev.id !== id));

    const success = await socketManager.dispatchAuditedAction("CALENDAR_DELETE", { event_id: id });
    if (!success) {
      // Rollback bei fehlender Bestätigung
      setEvents(previousEvents);
      setFeedbackMsg("Fehler: Termin konnte auf dem Server nicht gelöscht werden. Wiederhergestellt.");
      setTimeout(() => setFeedbackMsg(null), 3000);
    }
  };

  const handleToggleAutoBriefing = () => {
    const nextState = !autoBriefing;
    setAutoBriefing(nextState);
    socketManager.setAutoBriefing(nextState);
  };

  const handleTriggerBriefing = () => {
    socketManager.triggerBriefingNow();
    setBriefingTriggered(true);
    setTimeout(() => setBriefingTriggered(false), 3000);
  };

  const formatEventDate = (dateStr: string) => {
    try {
      const d = new Date(dateStr);
      if (isNaN(d.getTime())) return dateStr;
      return d.toLocaleString("de-DE", {
        weekday: "short",
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit"
      });
    } catch {
      return dateStr;
    }
  };

  const getCategoryColor = (cat: string) => {
    switch (cat.toLowerCase()) {
      case "arbeit":
      case "work":
        return "border-blue-500/40 bg-blue-500/10 text-blue-400";
      case "meeting":
        return "border-purple-500/40 bg-purple-500/10 text-purple-400";
      case "privat":
        return "border-emerald-500/40 bg-emerald-500/10 text-emerald-400";
      case "system":
        return "border-amber-500/40 bg-amber-500/10 text-amber-400";
      default:
        return "border-[#00d4ff]/40 bg-[#00d4ff]/10 text-[#00d4ff]";
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 animate-in fade-in duration-200">
      <div className="relative w-full max-w-5xl rounded-2xl glass-panel border border-[#00d4ff]/40 bg-[#0d1117]/95 shadow-2xl p-6 overflow-hidden flex flex-col max-h-[92vh]">
        
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#1f242d] pb-4 mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-[#00d4ff]/10 text-[#00d4ff] border border-[#00d4ff]/30 shadow-[0_0_15px_rgba(0,212,255,0.2)]">
              <CalendarDays className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-white uppercase tracking-wider">
                  Terminkalender & Tagesbriefing
                </h2>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#00d4ff]/20 text-[#00d4ff] font-mono border border-[#00d4ff]/30">
                  SQLite Core
                </span>
              </div>
              <p className="text-xs text-gray-400">
                Verwalte Termine & steuere das autonome Sprach-Briefing beim Systemstart.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Briefing Control Bar */}
        <div className="mb-5 p-3.5 rounded-xl bg-gradient-to-r from-[#00d4ff]/5 via-purple-500/5 to-transparent border border-white/10 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <Sunrise className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs font-semibold text-gray-200">
                Morgen-/Startup-Briefing (Sprachausgabe)
              </div>
              <div className="text-[11px] text-gray-400">
                Liest beim Start Wetter, Systemstatus und heutige Termine vor.
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Manual Briefing Trigger Button */}
            <button
              onClick={handleTriggerBriefing}
              disabled={briefingTriggered}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                briefingTriggered
                  ? "bg-emerald-500/20 border-emerald-500 text-emerald-300"
                  : "bg-white/5 border-white/15 text-gray-300 hover:text-white hover:border-[#00d4ff]/50 hover:bg-[#00d4ff]/10"
              }`}
            >
              <Volume2 className="w-3.5 h-3.5 text-[#00d4ff]" />
              <span>{briefingTriggered ? "Briefing gestartet..." : "Jetzt vorlesen"}</span>
            </button>

            {/* Auto-Briefing Switch */}
            <button
              onClick={handleToggleAutoBriefing}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-mono font-medium border transition-all ${
                autoBriefing
                  ? "bg-emerald-500/20 border-emerald-500/50 text-emerald-400"
                  : "bg-red-500/10 border-red-500/30 text-red-400"
              }`}
            >
              <span className={`w-2 h-2 rounded-full ${autoBriefing ? "bg-emerald-400 shadow-[0_0_8px_#34d399]" : "bg-red-500"}`} />
              <span>Autostart: {autoBriefing ? "AKTIV (AN)" : "INAKTIV (AUS)"}</span>
            </button>
          </div>
        </div>

        {/* Feedback Alert */}
        {feedbackMsg && (
          <div className="mb-4 p-2.5 rounded-lg bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-xs flex items-center gap-2 animate-in fade-in">
            <CheckCircle2 className="w-4 h-4" />
            <span>{feedbackMsg}</span>
          </div>
        )}

        {/* Two-Column Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 flex-1 overflow-y-auto pr-1">
          
          {/* Left: Events List (7 Cols) */}
          <div className="lg:col-span-7 flex flex-col">
            <div className="flex items-center justify-between mb-2.5">
              <span className="text-xs font-bold text-gray-300 uppercase tracking-wider flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5 text-[#00d4ff]" />
                Kommende Termine ({events.length})
              </span>
              <button
                onClick={() => socketManager.requestCalendarEvents()}
                className="text-[11px] text-gray-400 hover:text-[#00d4ff] font-mono"
              >
                [Aktualisieren]
              </button>
            </div>

            <div className="flex-1 space-y-2.5 overflow-y-auto pr-1 max-h-[480px]">
              {events.length === 0 ? (
                <div className="p-8 text-center border border-dashed border-white/10 rounded-xl bg-white/[0.02]">
                  <Calendar className="w-8 h-8 text-gray-600 mx-auto mb-2" />
                  <p className="text-xs text-gray-400">Keine Termine im Kalender hinterlegt.</p>
                  <p className="text-[11px] text-gray-500 mt-1">
                    Trage rechts einen Termin ein oder sage J.A.R.V.I.S. per Sprache: „Erstelle einen Termin für...“
                  </p>
                </div>
              ) : (
                events.map((ev) => (
                  <div
                    key={ev.id}
                    className="p-3 rounded-xl border border-white/10 bg-white/[0.03] hover:border-[#00d4ff]/40 hover:bg-white/[0.05] transition-all flex items-start justify-between gap-3 group"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <span className="text-sm font-semibold text-white truncate">
                          {ev.title}
                        </span>
                        <span className={`text-[10px] px-2 py-0.5 rounded-md border font-mono ${getCategoryColor(ev.category || "Termin")}`}>
                          {ev.category || "Termin"}
                        </span>
                        {ev.recurrence_rule && ev.recurrence_rule !== "NONE" && (
                          <span className="text-[10px] px-2 py-0.5 rounded-md border border-cyan-500/40 bg-cyan-500/10 text-cyan-300 font-mono flex items-center gap-1">
                            <Repeat className="w-2.5 h-2.5" />
                            {ev.recurrence_rule}
                          </span>
                        )}
                      </div>

                      <div className="flex items-center gap-3 text-xs text-gray-400 mb-1 flex-wrap">
                        <span className="flex items-center gap-1 text-[#00d4ff] font-mono">
                          <Clock className="w-3 h-3" />
                          {formatEventDate(ev.start_time)}
                          {ev.end_time ? ` → ${formatEventDate(ev.end_time)}` : ""}
                        </span>
                        {ev.reminder_strategy_parsed?.rules && ev.reminder_strategy_parsed.rules.length > 0 ? (
                          <div className="flex items-center gap-1.5 flex-wrap">
                            {ev.reminder_strategy_parsed.rules.map((r, idx) => (
                              <span key={idx} className="flex items-center gap-1 text-amber-300/90 bg-amber-500/10 border border-amber-500/20 px-1.5 py-0.5 rounded font-mono text-[10px]">
                                <Bell className="w-2.5 h-2.5 text-amber-400" />
                                {r.trigger} ({r.frequency || "once"})
                              </span>
                            ))}
                          </div>
                        ) : ev.reminder_offset_minutes && ev.reminder_offset_minutes > 0 ? (
                          <span className="flex items-center gap-1 text-gray-400 font-mono text-[11px]">
                            <Bell className="w-3 h-3 text-amber-400" />
                            {ev.reminder_offset_minutes}m vorher
                          </span>
                        ) : null}
                      </div>

                      {ev.description && (
                        <p className="text-xs text-gray-400 line-clamp-2 mt-1 bg-black/20 p-1.5 rounded-lg border border-white/5">
                          {ev.description}
                        </p>
                      )}
                    </div>

                    <button
                      onClick={() => handleDelete(ev.id)}
                      title="Termin löschen"
                      className="p-2 rounded-lg text-gray-500 hover:text-red-400 hover:bg-red-500/10 border border-transparent hover:border-red-500/30 transition-colors opacity-80 group-hover:opacity-100"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Right: Add Event Form (5 Cols) */}
          <div className="lg:col-span-5 border-t lg:border-t-0 lg:border-l border-[#1f242d] pt-4 lg:pt-0 lg:pl-5 flex flex-col">
            <span className="text-xs font-bold text-gray-300 uppercase tracking-wider flex items-center gap-1.5 mb-3">
              <Plus className="w-3.5 h-3.5 text-[#00d4ff]" />
              Neuen Termin eintragen
            </span>

            <form onSubmit={handleCreate} className="space-y-3 flex-1 flex flex-col justify-between">
              <div className="space-y-3">
                <div>
                  <label className="block text-[11px] font-mono text-gray-400 mb-1">
                    TITEL / EREIGNIS *
                  </label>
                  <input
                    type="text"
                    required
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="z. B. Team-Meeting, Zahnarzt, Server-Wartung..."
                    className="w-full px-3 py-2 text-xs bg-black/40 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-[#00d4ff] transition-colors"
                  />
                </div>

                <div className="grid grid-cols-2 gap-2.5">
                  <div>
                    <label className="block text-[11px] font-mono text-gray-400 mb-1">
                      STARTZEITPUNKT *
                    </label>
                    <input
                      type="datetime-local"
                      required
                      value={startTime}
                      onChange={(e) => setStartTime(e.target.value)}
                      className="w-full px-2.5 py-2 text-xs bg-black/40 border border-white/10 rounded-lg text-white font-mono focus:outline-none focus:border-[#00d4ff] transition-colors"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-mono text-gray-400 mb-1">
                      ENDE (OPTIONAL)
                    </label>
                    <input
                      type="datetime-local"
                      value={endTime}
                      onChange={(e) => setEndTime(e.target.value)}
                      className="w-full px-2.5 py-2 text-xs bg-black/40 border border-white/10 rounded-lg text-white font-mono focus:outline-none focus:border-[#00d4ff] transition-colors"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2.5">
                  <div>
                    <label className="block text-[11px] font-mono text-gray-400 mb-1">
                      WIEDERHOLUNG
                    </label>
                    <select
                      value={recurrence}
                      onChange={(e) => setRecurrence(e.target.value as any)}
                      className="w-full px-2.5 py-2 text-xs bg-black/40 border border-white/10 rounded-lg text-white focus:outline-none focus:border-[#00d4ff] transition-colors"
                    >
                      <option value="NONE">Einmalig (NONE)</option>
                      <option value="DAILY">Täglich (DAILY)</option>
                      <option value="WEEKLY">Wöchentlich (WEEKLY)</option>
                      <option value="MONTHLY">Monatlich (MONTHLY)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-[11px] font-mono text-gray-400 mb-1">
                      ERINNERUNGS-STRATEGIE
                    </label>
                    <select
                      value={reminder}
                      onChange={(e) => setReminder(e.target.value)}
                      className="w-full px-2.5 py-2 text-xs bg-black/40 border border-white/10 rounded-lg text-white focus:outline-none focus:border-[#00d4ff] transition-colors"
                    >
                      <option value="15m">15 Min vorher (einmalig)</option>
                      <option value="1h">1 Stunde vorher (einmalig)</option>
                      <option value="1d">1 Tag vorher (täglich)</option>
                      <option value="staged_week_hour">Gestaffelt: -7d (tägl.) + -1h (einm.)</option>
                      <option value="none">Keine Erinnerung</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-[11px] font-mono text-gray-400 mb-1">
                    KATEGORIE
                  </label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full px-2.5 py-2 text-xs bg-black/40 border border-white/10 rounded-lg text-white focus:outline-none focus:border-[#00d4ff] transition-colors"
                  >
                    <option value="Termin">Termin</option>
                    <option value="Arbeit">Arbeit</option>
                    <option value="Meeting">Meeting</option>
                    <option value="Privat">Privat</option>
                    <option value="System">System</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[11px] font-mono text-gray-400 mb-1">
                    BESCHREIBUNG / NOTIZEN (OPTIONAL)
                  </label>
                  <textarea
                    rows={2}
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Details, Vorbereitung oder Notizen..."
                    className="w-full px-3 py-2 text-xs bg-black/40 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-[#00d4ff] transition-colors resize-none"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full mt-3 py-2.5 px-4 rounded-xl bg-[#00d4ff]/20 hover:bg-[#00d4ff]/30 text-[#00d4ff] border border-[#00d4ff]/50 hover:border-[#00d4ff] font-semibold text-xs transition-all shadow-[0_0_15px_rgba(0,212,255,0.2)] flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Plus className={`w-4 h-4 ${isSubmitting ? "animate-spin" : ""}`} />
                <span>{isSubmitting ? "Wird übertragen & verifiziert..." : "Termin im Kalender speichern"}</span>
              </button>
            </form>
          </div>

        </div>

        {/* Footer info */}
        <div className="mt-4 pt-3 border-t border-[#1f242d] flex items-center justify-between text-[11px] text-gray-500 font-mono">
          <span>Gespeichert in: <code className="text-gray-400">backend/memory/calendar.db</code></span>
          <span>Cron-Settings: <code className="text-gray-400">backend/config/cron_settings.json</code></span>
        </div>

      </div>
    </div>
  );
};
