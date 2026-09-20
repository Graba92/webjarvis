"use client";

import React, { useState, useEffect, useMemo } from "react";
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
  Repeat,
  CalendarRange,
  ChevronLeft,
  ChevronRight,
  Cake,
  Sparkles,
  Layers,
  LayoutGrid,
  Filter
} from "lucide-react";

interface CalendarModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type ZoomHorizon = "1w" | "2w" | "1m" | "3m" | "6m" | "9m" | "12m";

export const CalendarModal: React.FC<CalendarModalProps> = ({ isOpen, onClose }) => {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [autoBriefing, setAutoBriefing] = useState<boolean>(true);
  
  // View Modes: "manager" (Eintragen & Liste) vs "matrix" (Vollwertige Kalender-Matrix)
  const [viewMode, setViewMode] = useState<"manager" | "matrix">("manager");
  const [zoomHorizon, setZoomHorizon] = useState<ZoomHorizon>("1m");
  
  // Navigation
  const [referenceDate, setReferenceDate] = useState<Date>(new Date());
  const [selectedDay, setSelectedDay] = useState<Date>(new Date());
  
  // Form fields
  const [title, setTitle] = useState("");
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [category, setCategory] = useState("Termin");
  const [recurrence, setRecurrence] = useState<"NONE" | "DAILY" | "WEEKLY" | "MONTHLY" | "YEARLY">("NONE");
  const [reminder, setReminder] = useState("15m");
  const [description, setDescription] = useState("");
  const [feedbackMsg, setFeedbackMsg] = useState<string | null>(null);
  const [briefingTriggered, setBriefingTriggered] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [categoryFilter, setCategoryFilter] = useState<string>("ALL");

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
      setReferenceDate(new Date());
      setSelectedDay(new Date());
    }

    return () => {
      unsubEvents();
      unsubBriefing();
    };
  }, [isOpen]);

  if (!isOpen) return null;

  // Form submission
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
    setEvents((prev) => prev.filter((ev) => ev.id !== id));

    const success = await socketManager.dispatchAuditedAction("CALENDAR_DELETE", { event_id: id });
    if (!success) {
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

  // Check if an event is persistent / recurring or a birthday
  const isPersistentEvent = (ev: CalendarEvent) => {
    const cat = (ev.category || "").toLowerCase();
    const rule = (ev.recurrence_rule || "").toUpperCase();
    return (
      rule === "DAILY" || 
      rule === "WEEKLY" || 
      rule === "MONTHLY" || 
      rule === "YEARLY" || 
      cat.includes("geburtstag") ||
      cat.includes("birthday") ||
      Boolean(ev.is_recurring)
    );
  };

  // Recurrence Matching Logic for a given calendar day
  const doesEventOccurOnDay = (ev: CalendarEvent, targetDay: Date) => {
    try {
      const evDate = new Date(ev.start_time);
      if (isNaN(evDate.getTime())) return false;

      const rule = (ev.recurrence_rule || "NONE").toUpperCase();
      const cat = (ev.category || "").toLowerCase();
      const isBirthday = cat.includes("geburtstag") || cat.includes("birthday");

      // Normalize dates to YYYY-MM-DD
      const targetYear = targetDay.getFullYear();
      const targetMonth = targetDay.getMonth();
      const targetDate = targetDay.getDate();
      const targetDayOfWeek = targetDay.getDay(); // 0 = Sunday, 1 = Monday...

      const evYear = evDate.getFullYear();
      const evMonth = evDate.getMonth();
      const evDateNum = evDate.getDate();
      const evDayOfWeek = evDate.getDay();

      // Check if event starts after targetDay
      const targetMidnight = new Date(targetYear, targetMonth, targetDate).getTime();
      const evMidnight = new Date(evYear, evMonth, evDateNum).getTime();

      if (rule === "NONE" && !isBirthday && !ev.is_recurring) {
        return targetYear === evYear && targetMonth === evMonth && targetDate === evDateNum;
      }

      // If target day is before the initial creation date, it doesn't occur yet
      if (targetMidnight < evMidnight) {
        return false;
      }

      if (rule === "DAILY") {
        return true;
      }

      if (rule === "WEEKLY") {
        return targetDayOfWeek === evDayOfWeek;
      }

      if (rule === "MONTHLY") {
        return targetDate === evDateNum;
      }

      if (rule === "YEARLY" || isBirthday) {
        return targetMonth === evMonth && targetDate === evDateNum;
      }

      return targetYear === evYear && targetMonth === evMonth && targetDate === evDateNum;
    } catch {
      return false;
    }
  };

  // Get all events occurring on a specific date
  const getEventsForDay = (targetDay: Date) => {
    return events.filter((ev) => {
      if (categoryFilter !== "ALL") {
        if (categoryFilter === "RECURRING" && !isPersistentEvent(ev)) return false;
        if (categoryFilter === "NORMAL" && isPersistentEvent(ev)) return false;
        if (categoryFilter !== "RECURRING" && categoryFilter !== "NORMAL" && (ev.category || "Termin") !== categoryFilter) return false;
      }
      return doesEventOccurOnDay(ev, targetDay);
    });
  };

  // Navigation handlers
  const handleNavigate = (delta: number) => {
    const next = new Date(referenceDate);
    if (zoomHorizon === "1w") {
      next.setDate(next.getDate() + delta * 7);
    } else if (zoomHorizon === "2w") {
      next.setDate(next.getDate() + delta * 14);
    } else if (zoomHorizon === "1m") {
      next.setMonth(next.getMonth() + delta);
    } else if (zoomHorizon === "3m") {
      next.setMonth(next.getMonth() + delta * 3);
    } else if (zoomHorizon === "6m") {
      next.setMonth(next.getMonth() + delta * 6);
    } else if (zoomHorizon === "9m") {
      next.setMonth(next.getMonth() + delta * 9);
    } else if (zoomHorizon === "12m") {
      next.setFullYear(next.getFullYear() + delta);
    }
    setReferenceDate(next);
  };

  const handleJumpToToday = () => {
    const now = new Date();
    setReferenceDate(now);
    setSelectedDay(now);
  };

  // Helper formatting
  const formatHeaderTitle = () => {
    const deMonth = referenceDate.toLocaleString("de-DE", { month: "long", year: "numeric" });
    if (zoomHorizon === "1w" || zoomHorizon === "2w") {
      return `Kalenderwoche • ${deMonth}`;
    }
    if (zoomHorizon === "1m") {
      return deMonth;
    }
    if (zoomHorizon === "3m") {
      const end = new Date(referenceDate);
      end.setMonth(end.getMonth() + 2);
      return `${referenceDate.toLocaleString("de-DE", { month: "short" })} – ${end.toLocaleString("de-DE", { month: "short", year: "numeric" })} (3 Monate)`;
    }
    if (zoomHorizon === "6m") {
      const end = new Date(referenceDate);
      end.setMonth(end.getMonth() + 5);
      return `${referenceDate.toLocaleString("de-DE", { month: "short" })} – ${end.toLocaleString("de-DE", { month: "short", year: "numeric" })} (Halbjahr)`;
    }
    if (zoomHorizon === "9m") {
      const end = new Date(referenceDate);
      end.setMonth(end.getMonth() + 8);
      return `${referenceDate.toLocaleString("de-DE", { month: "short" })} – ${end.toLocaleString("de-DE", { month: "short", year: "numeric" })} (9 Monate)`;
    }
    if (zoomHorizon === "12m") {
      return `Jahresübersicht ${referenceDate.getFullYear()} / ${referenceDate.getFullYear() + 1}`;
    }
    return deMonth;
  };

  const formatEventTime = (dateStr: string) => {
    try {
      const d = new Date(dateStr);
      if (isNaN(d.getTime())) return "";
      return d.toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit" });
    } catch {
      return "";
    }
  };

  // Day inspector events
  const selectedDayEvents = useMemo(() => {
    return getEventsForDay(selectedDay);
  }, [selectedDay, events, categoryFilter]);

  // Generate Days for 1 Week / 2 Weeks
  const weekDaysList = useMemo(() => {
    const totalDays = zoomHorizon === "1w" ? 7 : 14;
    const start = new Date(referenceDate);
    // Find Monday of the reference week
    const dayOfWeek = start.getDay();
    const distanceToMonday = (dayOfWeek + 6) % 7;
    start.setDate(start.getDate() - distanceToMonday);
    start.setHours(0, 0, 0, 0);

    const days: Date[] = [];
    for (let i = 0; i < totalDays; i++) {
      const d = new Date(start);
      d.setDate(d.getDate() + i);
      days.push(d);
    }
    return days;
  }, [referenceDate, zoomHorizon]);

  // Generate Month Grid (42 cells: 6 weeks x 7 days starting with Monday)
  const getMonthDaysGrid = (baseDate: Date) => {
    const year = baseDate.getFullYear();
    const month = baseDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const dayOfWeek = firstDay.getDay();
    const distanceToMonday = (dayOfWeek + 6) % 7;

    const start = new Date(firstDay);
    start.setDate(start.getDate() - distanceToMonday);

    const grid: Date[] = [];
    for (let i = 0; i < 42; i++) {
      const d = new Date(start);
      d.setDate(d.getDate() + i);
      grid.push(d);
    }
    return { grid, activeMonth: month };
  };

  // Multi-Month Generator (for 3m, 6m, 9m, 12m)
  const multiMonthsList = useMemo(() => {
    let count = 3;
    if (zoomHorizon === "6m") count = 6;
    if (zoomHorizon === "9m") count = 9;
    if (zoomHorizon === "12m") count = 12;

    const list: Date[] = [];
    for (let i = 0; i < count; i++) {
      const d = new Date(referenceDate.getFullYear(), referenceDate.getMonth() + i, 1);
      list.push(d);
    }
    return list;
  }, [referenceDate, zoomHorizon]);

  const isSameCalendarDay = (d1: Date, d2: Date) => {
    return (
      d1.getFullYear() === d2.getFullYear() &&
      d1.getMonth() === d2.getMonth() &&
      d1.getDate() === d2.getDate()
    );
  };

  const isToday = (d: Date) => {
    return isSameCalendarDay(d, new Date());
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-3 sm:p-5 animate-in fade-in duration-200">
      
      {/* Outer Wrapper for Modal + Protruding Dock Button */}
      <div className={`relative w-full ${viewMode === "matrix" ? "max-w-7xl" : "max-w-5xl"} transition-all duration-300 flex flex-col`}>
        
        {/* RECHTER DOCK-BUTTON (Wie im User-Screenshot markiert) */}
        <button
          onClick={() => setViewMode(viewMode === "manager" ? "matrix" : "manager")}
          title={viewMode === "manager" ? "Vollwertige Kalender-Matrix öffnen" : "Zurück zur Terminverwaltung & Schnelleingabe"}
          className="absolute -right-12 top-28 z-40 hidden md:flex flex-col items-center justify-center gap-2.5 py-4 px-2.5 rounded-r-2xl bg-[#0d1117]/95 border-t border-r border-b border-[#00d4ff]/50 text-[#00d4ff] hover:bg-[#00d4ff]/20 hover:text-white hover:border-[#00d4ff] shadow-[5px_0_20px_rgba(0,212,255,0.3)] transition-all cursor-pointer group"
        >
          <CalendarRange className="w-5 h-5 text-[#00d4ff] group-hover:scale-125 transition-transform" />
          <span className="[writing-mode:vertical-rl] rotate-180 text-[10px] font-mono font-bold tracking-widest uppercase text-gray-300 group-hover:text-white">
            {viewMode === "manager" ? "Kalender-Matrix ▶" : "◀ Termin-Manager"}
          </span>
        </button>

        {/* Modal Window */}
        <div className={`relative w-full rounded-2xl glass-panel border border-[#00d4ff]/40 bg-[#0d1117]/95 shadow-2xl p-5 overflow-hidden flex flex-col ${viewMode === "matrix" ? "max-h-[94vh] min-h-[85vh]" : "max-h-[90vh]"}`}>
          
          {/* Header */}
          <div className="flex items-center justify-between border-b border-[#1f242d] pb-3.5 mb-3.5 flex-wrap gap-3">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-[#00d4ff]/10 text-[#00d4ff] border border-[#00d4ff]/30 shadow-[0_0_15px_rgba(0,212,255,0.2)]">
                {viewMode === "matrix" ? <CalendarRange className="w-6 h-6" /> : <CalendarDays className="w-6 h-6" />}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-base font-bold text-white uppercase tracking-wider">
                    {viewMode === "matrix" ? "Interaktive Kalender-Matrix" : "Terminkalender & Tagesbriefing"}
                  </h2>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#00d4ff]/20 text-[#00d4ff] font-mono border border-[#00d4ff]/30">
                    SQLite + Live-Sync
                  </span>
                </div>
                <p className="text-xs text-gray-400">
                  {viewMode === "matrix" 
                    ? "Überlappungsfreier Zeithorizont von 1 Woche bis 12 Monate mit Hervorhebung von Dauerterminen & Geburtstagen."
                    : "Verwalte Termine & steuere das autonome Sprach-Briefing beim Systemstart."}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2.5">
              {/* Dual View Switcher im Header */}
              <div className="flex items-center p-1 rounded-xl bg-black/40 border border-white/10 text-xs font-mono">
                <button
                  onClick={() => setViewMode("manager")}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
                    viewMode === "manager"
                      ? "bg-[#00d4ff]/20 text-[#00d4ff] border border-[#00d4ff]/40 font-bold shadow-[0_0_10px_rgba(0,212,255,0.2)]"
                      : "text-gray-400 hover:text-white"
                  }`}
                >
                  <LayoutGrid className="w-3.5 h-3.5" />
                  <span>Verwaltung</span>
                </button>
                <button
                  onClick={() => setViewMode("matrix")}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
                    viewMode === "matrix"
                      ? "bg-[#00d4ff]/20 text-[#00d4ff] border border-[#00d4ff]/40 font-bold shadow-[0_0_10px_rgba(0,212,255,0.2)]"
                      : "text-gray-400 hover:text-white"
                  }`}
                >
                  <CalendarRange className="w-3.5 h-3.5" />
                  <span>Kalender-Ansicht</span>
                </button>
              </div>

              {/* Close Button */}
              <button
                onClick={onClose}
                className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-colors cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* ═════════════════════════════════════════════════════════════════════ */}
          {/* ANSICHT 1: VOLLWERTIGE KALENDER-MATRIX (Woche bis 12 Monate)           */}
          {/* ═════════════════════════════════════════════════════════════════════ */}
          {viewMode === "matrix" && (
            <div className="flex-1 flex flex-col overflow-hidden gap-3">
              
              {/* Matrix Control Bar: Zeithorizont + Navigation + Legende */}
              <div className="flex flex-wrap items-center justify-between gap-2.5 p-2.5 rounded-xl bg-white/[0.02] border border-white/10">
                
                {/* Navigation (Zurück, Heute, Weiter, Titel) */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleNavigate(-1)}
                    title="Vorheriger Zeitraum"
                    className="p-1.5 rounded-lg bg-black/40 hover:bg-[#00d4ff]/20 text-gray-300 hover:text-[#00d4ff] border border-white/10 hover:border-[#00d4ff]/40 transition-colors cursor-pointer"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>

                  <button
                    onClick={handleJumpToToday}
                    className="px-2.5 py-1 text-xs font-mono font-bold rounded-lg bg-[#00d4ff]/10 hover:bg-[#00d4ff]/20 text-[#00d4ff] border border-[#00d4ff]/30 transition-colors cursor-pointer"
                  >
                    Heute
                  </button>

                  <button
                    onClick={() => handleNavigate(1)}
                    title="Nächster Zeitraum"
                    className="p-1.5 rounded-lg bg-black/40 hover:bg-[#00d4ff]/20 text-gray-300 hover:text-[#00d4ff] border border-white/10 hover:border-[#00d4ff]/40 transition-colors cursor-pointer"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>

                  <span className="text-sm font-bold text-white font-mono ml-2">
                    {formatHeaderTitle()}
                  </span>
                </div>

                {/* Zeithorizont-Wahltasten (1W, 2W, 1M, 3M, 6M, 9M, 12M) */}
                <div className="flex items-center gap-1 p-1 rounded-lg bg-black/50 border border-white/10 text-xs font-mono flex-wrap">
                  {(["1w", "2w", "1m", "3m", "6m", "9m", "12m"] as ZoomHorizon[]).map((hz) => {
                    const labels: Record<ZoomHorizon, string> = {
                      "1w": "1 Woche",
                      "2w": "2 Wochen",
                      "1m": "1 Monat",
                      "3m": "3 Monate",
                      "6m": "6 Monate",
                      "9m": "9 Monate",
                      "12m": "12 Monate"
                    };
                    const isActive = zoomHorizon === hz;
                    return (
                      <button
                        key={hz}
                        onClick={() => setZoomHorizon(hz)}
                        className={`px-2.5 py-1 rounded-md transition-all cursor-pointer ${
                          isActive
                            ? "bg-[#00d4ff] text-black font-bold shadow-[0_0_12px_rgba(0,212,255,0.4)]"
                            : "text-gray-400 hover:text-white hover:bg-white/5"
                        }`}
                      >
                        {labels[hz]}
                      </button>
                    );
                  })}
                </div>

                {/* Farblegende & Filter */}
                <div className="flex items-center gap-3 text-xs font-mono flex-wrap">
                  <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-amber-500/10 border border-amber-500/30 text-amber-300">
                    <Cake className="w-3.5 h-3.5 text-amber-400" />
                    <span>Dauerhaft / Geburtstag</span>
                  </div>

                  <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-[#00d4ff]/10 border border-[#00d4ff]/30 text-[#00d4ff]">
                    <Clock className="w-3.5 h-3.5 text-[#00d4ff]" />
                    <span>Normaler Termin</span>
                  </div>

                  <select
                    value={categoryFilter}
                    onChange={(e) => setCategoryFilter(e.target.value)}
                    className="px-2 py-1 text-xs bg-black/40 border border-white/10 rounded-lg text-white font-mono focus:outline-none focus:border-[#00d4ff]"
                  >
                    <option value="ALL">Alle Kategorien</option>
                    <option value="RECURRING">Nur Dauerhafte & Geburtstage</option>
                    <option value="NORMAL">Nur Einmaltermine</option>
                    <option value="Termin">Kategorie: Termin</option>
                    <option value="Geburtstag">Kategorie: Geburtstag</option>
                    <option value="Arbeit">Kategorie: Arbeit</option>
                    <option value="Meeting">Kategorie: Meeting</option>
                    <option value="Privat">Kategorie: Privat</option>
                  </select>
                </div>

              </div>

              {/* Kalender-Hauptbereich (Raster links, Tages-Inspektor rechts) */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-3 flex-1 overflow-hidden">
                
                {/* Kalender-Gitter (8 Spalten auf Desktop) */}
                <div className="lg:col-span-8 overflow-y-auto pr-1 flex flex-col">
                  
                  {/* Fall 1 & 2: Wochenansichten (1 Woche oder 2 Wochen) */}
                  {(zoomHorizon === "1w" || zoomHorizon === "2w") && (
                    <div className={`grid grid-cols-1 md:grid-cols-7 gap-2 flex-1`}>
                      {weekDaysList.map((day, idx) => {
                        const dayEvents = getEventsForDay(day);
                        const isCurrentDay = isToday(day);
                        const isSelected = isSameCalendarDay(day, selectedDay);

                        return (
                          <div
                            key={idx}
                            onClick={() => setSelectedDay(day)}
                            className={`p-2.5 rounded-xl border transition-all flex flex-col min-h-[220px] cursor-pointer ${
                              isSelected
                                ? "border-[#00d4ff] bg-[#00d4ff]/10 shadow-[0_0_15px_rgba(0,212,255,0.15)]"
                                : isCurrentDay
                                ? "border-amber-400/50 bg-amber-500/5"
                                : "border-white/10 bg-white/[0.02] hover:border-white/20 hover:bg-white/[0.04]"
                            }`}
                          >
                            <div className="flex items-center justify-between border-b border-white/10 pb-1.5 mb-2">
                              <span className="text-[11px] font-mono font-bold uppercase text-gray-400">
                                {day.toLocaleString("de-DE", { weekday: "short" })}
                              </span>
                              <span className={`text-xs font-mono font-bold px-1.5 py-0.5 rounded-md ${
                                isCurrentDay ? "bg-amber-400 text-black font-bold" : "text-white"
                              }`}>
                                {day.getDate()}.{day.getMonth() + 1}.
                              </span>
                            </div>

                            {/* Termine an diesem Wochentag */}
                            <div className="flex-1 space-y-1.5 overflow-y-auto">
                              {dayEvents.length === 0 ? (
                                <span className="text-[10px] text-gray-600 font-mono italic">Keine Termine</span>
                              ) : (
                                dayEvents.map((ev) => {
                                  const persistent = isPersistentEvent(ev);
                                  return (
                                    <div
                                      key={ev.id}
                                      className={`p-1.5 rounded-lg border text-[11px] leading-snug transition-all ${
                                        persistent
                                          ? "border-amber-400/60 bg-amber-500/20 text-amber-200 shadow-[0_0_8px_rgba(245,158,11,0.2)]"
                                          : "border-[#00d4ff]/40 bg-[#00d4ff]/15 text-[#00d4ff]"
                                      }`}
                                    >
                                      <div className="flex items-center gap-1 font-semibold truncate">
                                        {persistent ? <Cake className="w-3 h-3 shrink-0 text-amber-400" /> : <Clock className="w-3 h-3 shrink-0" />}
                                        <span className="truncate">{ev.title}</span>
                                      </div>
                                      <div className="text-[10px] opacity-80 font-mono mt-0.5">
                                        {formatEventTime(ev.start_time) || "Ganztägig"}
                                      </div>
                                    </div>
                                  );
                                })
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}

                  {/* Fall 3: 1 Monat Vollansicht */}
                  {zoomHorizon === "1m" && (() => {
                    const { grid, activeMonth } = getMonthDaysGrid(referenceDate);
                    const weekDaysHeader = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"];

                    return (
                      <div className="flex-1 flex flex-col">
                        {/* Wochentags-Kopfzeile */}
                        <div className="grid grid-cols-7 gap-1.5 mb-1.5 text-center text-xs font-mono font-bold text-gray-400">
                          {weekDaysHeader.map((w) => (
                            <div key={w} className="py-1 bg-white/[0.03] rounded-lg border border-white/5">
                              {w}
                            </div>
                          ))}
                        </div>

                        {/* 42-Tage-Monatsraster */}
                        <div className="grid grid-cols-7 gap-1.5 flex-1">
                          {grid.map((day, idx) => {
                            const dayEvents = getEventsForDay(day);
                            const isCurrentMonth = day.getMonth() === activeMonth;
                            const isCurrentDay = isToday(day);
                            const isSelected = isSameCalendarDay(day, selectedDay);

                            return (
                              <div
                                key={idx}
                                onClick={() => setSelectedDay(day)}
                                className={`p-1.5 rounded-xl border transition-all flex flex-col min-h-[75px] max-h-[105px] cursor-pointer ${
                                  isSelected
                                    ? "border-[#00d4ff] bg-[#00d4ff]/15 shadow-[0_0_15px_rgba(0,212,255,0.2)]"
                                    : isCurrentDay
                                    ? "border-amber-400/60 bg-amber-500/10"
                                    : isCurrentMonth
                                    ? "border-white/10 bg-white/[0.02] hover:border-white/20 hover:bg-white/[0.04]"
                                    : "border-white/5 bg-transparent opacity-40 hover:opacity-70"
                                }`}
                              >
                                <div className="flex items-center justify-between mb-1">
                                  <span className={`text-[11px] font-mono font-bold px-1 rounded ${
                                    isCurrentDay ? "bg-amber-400 text-black font-bold" : "text-white"
                                  }`}>
                                    {day.getDate()}
                                  </span>
                                  {dayEvents.length > 0 && (
                                    <span className="text-[9px] px-1 rounded-full bg-white/10 text-gray-300 font-mono">
                                      {dayEvents.length}
                                    </span>
                                  )}
                                </div>

                                {/* Events im Tag-Feld */}
                                <div className="space-y-1 overflow-hidden flex-1">
                                  {dayEvents.slice(0, 2).map((ev) => {
                                    const persistent = isPersistentEvent(ev);
                                    return (
                                      <div
                                        key={ev.id}
                                        className={`px-1 py-0.5 rounded text-[10px] truncate font-medium flex items-center gap-1 ${
                                          persistent
                                            ? "bg-amber-500/25 text-amber-200 border border-amber-500/40"
                                            : "bg-[#00d4ff]/20 text-[#00d4ff] border border-[#00d4ff]/40"
                                        }`}
                                      >
                                        {persistent ? <Cake className="w-2.5 h-2.5 shrink-0 text-amber-400" /> : <span className="w-1.5 h-1.5 rounded-full bg-[#00d4ff] shrink-0" />}
                                        <span className="truncate">{ev.title}</span>
                                      </div>
                                    );
                                  })}
                                  {dayEvents.length > 2 && (
                                    <div className="text-[9px] text-[#00d4ff] font-mono font-semibold pl-1">
                                      +{dayEvents.length - 2} weitere
                                    </div>
                                  )}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    );
                  })()}

                  {/* Fall 4: Multi-Monate (3, 6, 9 oder 12 Monate) */}
                  {(zoomHorizon === "3m" || zoomHorizon === "6m" || zoomHorizon === "9m" || zoomHorizon === "12m") && (
                    <div className={`grid gap-3 flex-1 ${
                      zoomHorizon === "3m" 
                        ? "grid-cols-1 md:grid-cols-3"
                        : zoomHorizon === "6m"
                        ? "grid-cols-1 md:grid-cols-3"
                        : zoomHorizon === "9m"
                        ? "grid-cols-1 md:grid-cols-3"
                        : "grid-cols-2 md:grid-cols-4"
                    }`}>
                      {multiMonthsList.map((mDate, mIdx) => {
                        const { grid, activeMonth } = getMonthDaysGrid(mDate);
                        const mTitle = mDate.toLocaleString("de-DE", { month: "long", year: "numeric" });
                        const miniWeekDays = ["M", "D", "M", "D", "F", "S", "S"];

                        return (
                          <div
                            key={mIdx}
                            className="p-2.5 rounded-xl border border-white/10 bg-white/[0.02] flex flex-col"
                          >
                            <div className="text-xs font-bold text-[#00d4ff] font-mono border-b border-white/10 pb-1 mb-2 text-center">
                              {mTitle}
                            </div>

                            {/* Wochentags-Header */}
                            <div className="grid grid-cols-7 gap-0.5 mb-1 text-center text-[9px] font-mono text-gray-500">
                              {miniWeekDays.map((d, i) => (
                                <span key={i}>{d}</span>
                              ))}
                            </div>

                            {/* Mini-Gitter */}
                            <div className="grid grid-cols-7 gap-0.5 flex-1">
                              {grid.map((day, dIdx) => {
                                const isCurrentMonth = day.getMonth() === activeMonth;
                                if (!isCurrentMonth) {
                                  return <div key={dIdx} className="h-5" />;
                                }

                                const dayEvents = getEventsForDay(day);
                                const hasPersistent = dayEvents.some((e) => isPersistentEvent(e));
                                const hasNormal = dayEvents.some((e) => !isPersistentEvent(e));
                                const isSelected = isSameCalendarDay(day, selectedDay);
                                const isCurrentDay = isToday(day);

                                return (
                                  <button
                                    key={dIdx}
                                    onClick={() => setSelectedDay(day)}
                                    className={`h-5 w-full rounded flex items-center justify-center text-[10px] font-mono relative transition-all cursor-pointer ${
                                      isSelected
                                        ? "bg-[#00d4ff] text-black font-bold shadow-[0_0_8px_#00d4ff]"
                                        : isCurrentDay
                                        ? "border border-amber-400 text-amber-300 font-bold"
                                        : dayEvents.length > 0
                                        ? hasPersistent
                                          ? "bg-amber-500/25 text-amber-200 border border-amber-500/40 font-bold"
                                          : "bg-[#00d4ff]/20 text-[#00d4ff] border border-[#00d4ff]/40 font-bold"
                                        : "text-gray-400 hover:bg-white/10 hover:text-white"
                                    }`}
                                  >
                                    <span>{day.getDate()}</span>
                                    {dayEvents.length > 0 && !isSelected && (
                                      <span className={`absolute bottom-0.5 w-1 h-1 rounded-full ${
                                        hasPersistent ? "bg-amber-400 shadow-[0_0_4px_#f59e0b]" : "bg-[#00d4ff]"
                                      }`} />
                                    )}
                                  </button>
                                );
                              })}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}

                </div>

                {/* Rechte Spalte: Tages-Detail-Inspektor (Überlappungsfrei & Klar) */}
                <div className="lg:col-span-4 border-t lg:border-t-0 lg:border-l border-[#1f242d] pt-3 lg:pt-0 lg:pl-3 flex flex-col justify-between overflow-hidden">
                  
                  <div className="flex-1 flex flex-col overflow-hidden">
                    <div className="flex items-center justify-between border-b border-white/10 pb-2 mb-3">
                      <div>
                        <span className="text-[10px] font-mono uppercase tracking-wider text-gray-400 block">
                          Tages-Inspektor
                        </span>
                        <span className="text-sm font-bold text-white font-mono">
                          {selectedDay.toLocaleString("de-DE", {
                            weekday: "long",
                            day: "2-digit",
                            month: "long",
                            year: "numeric"
                          })}
                        </span>
                      </div>
                      {isToday(selectedDay) && (
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-400/20 text-amber-300 border border-amber-400/30 font-mono font-bold">
                          HEUTE
                        </span>
                      )}
                    </div>

                    {/* Liste aller Termine des ausgewählten Tages */}
                    <div className="flex-1 space-y-2 overflow-y-auto pr-1">
                      {selectedDayEvents.length === 0 ? (
                        <div className="p-6 text-center border border-dashed border-white/10 rounded-xl bg-white/[0.02]">
                          <Calendar className="w-7 h-7 text-gray-600 mx-auto mb-2" />
                          <p className="text-xs text-gray-400">Keine Termine für diesen Tag hinterlegt.</p>
                          <button
                            onClick={() => {
                              const selISO = new Date(selectedDay);
                              selISO.setHours(10, 0, 0, 0);
                              const tzOffset = selISO.getTimezoneOffset() * 60000;
                              setStartTime(new Date(selISO.getTime() - tzOffset).toISOString().slice(0, 16));
                              setViewMode("manager");
                            }}
                            className="mt-3 px-3 py-1.5 rounded-lg bg-[#00d4ff]/20 hover:bg-[#00d4ff]/30 text-[#00d4ff] text-xs font-mono border border-[#00d4ff]/40 transition-colors"
                          >
                            + Termin für diesen Tag eintragen
                          </button>
                        </div>
                      ) : (
                        selectedDayEvents.map((ev) => {
                          const persistent = isPersistentEvent(ev);
                          return (
                            <div
                              key={ev.id}
                              className={`p-3 rounded-xl border transition-all ${
                                persistent
                                  ? "border-amber-400/50 bg-amber-500/10 shadow-[0_0_12px_rgba(245,158,11,0.15)]"
                                  : "border-[#00d4ff]/40 bg-[#00d4ff]/10"
                              }`}
                            >
                              <div className="flex items-start justify-between gap-2 mb-1.5">
                                <div className="flex items-center gap-1.5 flex-wrap">
                                  {persistent && (
                                    <span className="p-1 rounded bg-amber-500/20 text-amber-400 border border-amber-500/30">
                                      <Cake className="w-3.5 h-3.5" />
                                    </span>
                                  )}
                                  <span className="text-xs font-bold text-white">
                                    {ev.title}
                                  </span>
                                </div>
                                <button
                                  onClick={() => handleDelete(ev.id)}
                                  title="Termin löschen"
                                  className="p-1 rounded text-gray-500 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                                >
                                  <Trash2 className="w-3.5 h-3.5" />
                                </button>
                              </div>

                              <div className="flex items-center gap-2 text-[11px] font-mono text-gray-300 mb-1 flex-wrap">
                                <span className="flex items-center gap-1 text-[#00d4ff]">
                                  <Clock className="w-3 h-3" />
                                  {formatEventTime(ev.start_time) || "Ganztägig"}
                                </span>
                                <span className="px-1.5 py-0.5 rounded bg-white/10 text-gray-300 text-[10px]">
                                  {ev.category || "Termin"}
                                </span>
                                {ev.recurrence_rule && ev.recurrence_rule !== "NONE" && (
                                  <span className="px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 text-[10px] flex items-center gap-1">
                                    <Repeat className="w-2.5 h-2.5" />
                                    {ev.recurrence_rule}
                                  </span>
                                )}
                              </div>

                              {ev.description && (
                                <p className="text-xs text-gray-400 bg-black/30 p-2 rounded-lg border border-white/5 mt-1 leading-relaxed">
                                  {ev.description}
                                </p>
                              )}
                            </div>
                          );
                        })
                      )}
                    </div>
                  </div>

                  {/* Schnellaktion: Neuer Termin */}
                  <div className="pt-2 border-t border-[#1f242d] mt-2">
                    <button
                      onClick={() => {
                        const selISO = new Date(selectedDay);
                        selISO.setHours(10, 0, 0, 0);
                        const tzOffset = selISO.getTimezoneOffset() * 60000;
                        setStartTime(new Date(selISO.getTime() - tzOffset).toISOString().slice(0, 16));
                        setViewMode("manager");
                      }}
                      className="w-full py-2 px-3 rounded-xl bg-white/5 hover:bg-[#00d4ff]/20 text-gray-300 hover:text-[#00d4ff] border border-white/10 hover:border-[#00d4ff]/40 text-xs font-mono font-semibold transition-all flex items-center justify-center gap-2 cursor-pointer"
                    >
                      <Plus className="w-3.5 h-3.5 text-[#00d4ff]" />
                      <span>Termin für diesen Tag anlegen</span>
                    </button>
                  </div>

                </div>

              </div>

            </div>
          )}

          {/* ═════════════════════════════════════════════════════════════════════ */}
          {/* ANSICHT 2: TERMIN-VERWALTUNG (Liste & Neuer Eintrag)                  */}
          {/* ═════════════════════════════════════════════════════════════════════ */}
          {viewMode === "manager" && (
            <div className="flex-1 flex flex-col overflow-hidden">
              
              {/* Briefing Control Bar */}
              <div className="mb-4 p-3 rounded-xl bg-gradient-to-r from-[#00d4ff]/5 via-purple-500/5 to-transparent border border-white/10 flex flex-wrap items-center justify-between gap-3">
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
                  <button
                    onClick={handleTriggerBriefing}
                    disabled={briefingTriggered}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                      briefingTriggered
                        ? "bg-emerald-500/20 border-emerald-500 text-emerald-300"
                        : "bg-white/5 border-white/15 text-gray-300 hover:text-white hover:border-[#00d4ff]/50 hover:bg-[#00d4ff]/10 cursor-pointer"
                    }`}
                  >
                    <Volume2 className="w-3.5 h-3.5 text-[#00d4ff]" />
                    <span>{briefingTriggered ? "Briefing gestartet..." : "Jetzt vorlesen"}</span>
                  </button>

                  <button
                    onClick={handleToggleAutoBriefing}
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-mono font-medium border transition-all cursor-pointer ${
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
                      Hinterlegte Termine ({events.length})
                    </span>
                    <button
                      onClick={() => socketManager.requestCalendarEvents()}
                      className="text-[11px] text-gray-400 hover:text-[#00d4ff] font-mono cursor-pointer"
                    >
                      [Aktualisieren]
                    </button>
                  </div>

                  <div className="flex-1 space-y-2.5 overflow-y-auto pr-1 max-h-[440px]">
                    {events.length === 0 ? (
                      <div className="p-8 text-center border border-dashed border-white/10 rounded-xl bg-white/[0.02]">
                        <Calendar className="w-8 h-8 text-gray-600 mx-auto mb-2" />
                        <p className="text-xs text-gray-400">Keine Termine im Kalender hinterlegt.</p>
                        <p className="text-[11px] text-gray-500 mt-1">
                          Trage rechts einen Termin ein oder sage J.A.R.V.I.S. per Sprache: „Erstelle einen Termin für...“
                        </p>
                      </div>
                    ) : (
                      events.map((ev) => {
                        const persistent = isPersistentEvent(ev);
                        return (
                          <div
                            key={ev.id}
                            className={`p-3 rounded-xl border transition-all flex items-start justify-between gap-3 group ${
                              persistent
                                ? "border-amber-400/40 bg-amber-500/5 hover:border-amber-400/70 hover:bg-amber-500/10"
                                : "border-white/10 bg-white/[0.03] hover:border-[#00d4ff]/40 hover:bg-white/[0.05]"
                            }`}
                          >
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1 flex-wrap">
                                {persistent && <Cake className="w-3.5 h-3.5 text-amber-400 shrink-0" />}
                                <span className="text-sm font-semibold text-white truncate">
                                  {ev.title}
                                </span>
                                <span className={`text-[10px] px-2 py-0.5 rounded-md border font-mono ${
                                  persistent
                                    ? "border-amber-500/40 bg-amber-500/20 text-amber-300"
                                    : "border-[#00d4ff]/40 bg-[#00d4ff]/10 text-[#00d4ff]"
                                }`}>
                                  {ev.category || "Termin"}
                                </span>
                                {ev.recurrence_rule && ev.recurrence_rule !== "NONE" && (
                                  <span className="text-[10px] px-2 py-0.5 rounded-md border border-amber-500/40 bg-amber-500/15 text-amber-300 font-mono flex items-center gap-1">
                                    <Repeat className="w-2.5 h-2.5" />
                                    {ev.recurrence_rule}
                                  </span>
                                )}
                              </div>

                              <div className="flex items-center gap-3 text-xs text-gray-400 mb-1 flex-wrap">
                                <span className="flex items-center gap-1 text-[#00d4ff] font-mono">
                                  <Clock className="w-3 h-3" />
                                  {ev.start_time}
                                  {ev.end_time ? ` → ${ev.end_time}` : ""}
                                </span>
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
                              className="p-2 rounded-lg text-gray-500 hover:text-red-400 hover:bg-red-500/10 border border-transparent hover:border-red-500/30 transition-colors opacity-80 group-hover:opacity-100 cursor-pointer"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        );
                      })
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
                          placeholder="z. B. Florian Geburtstag, Team-Meeting, Zahnarzt..."
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
                            <option value="YEARLY">Jährlich / Geburtstag (YEARLY)</option>
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
                          <option value="Geburtstag">🎂 Geburtstag</option>
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
                          placeholder="Details, Geschenke, Vorbereitung oder Notizen..."
                          className="w-full px-3 py-2 text-xs bg-black/40 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-[#00d4ff] transition-colors resize-none"
                        />
                      </div>
                    </div>

                    <button
                      type="submit"
                      disabled={isSubmitting}
                      className="w-full mt-3 py-2.5 px-4 rounded-xl bg-[#00d4ff]/20 hover:bg-[#00d4ff]/30 text-[#00d4ff] border border-[#00d4ff]/50 hover:border-[#00d4ff] font-semibold text-xs transition-all shadow-[0_0_15px_rgba(0,212,255,0.2)] flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                    >
                      <Plus className={`w-4 h-4 ${isSubmitting ? "animate-spin" : ""}`} />
                      <span>{isSubmitting ? "Wird übertragen..." : "Termin im Kalender speichern"}</span>
                    </button>
                  </form>
                </div>

              </div>
            </div>
          )}

          {/* Footer info */}
          <div className="mt-3.5 pt-2.5 border-t border-[#1f242d] flex items-center justify-between text-[11px] text-gray-500 font-mono">
            <span>Datenbank: <code className="text-gray-400">backend/memory/calendar.db</code></span>
            <span>Ansicht: <code className="text-[#00d4ff]">{viewMode === "matrix" ? `Matrix-Modus (${zoomHorizon})` : "Manager-Modus"}</code></span>
          </div>

        </div>
      </div>
    </div>
  );
};
