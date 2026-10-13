"""
backend/core/cron_engine.py — Proaktive Cron- & Heartbeat-Engine für J.A.R.V.I.S. AI OS.
Macht HEARTBEAT.md durch einen echten Cron-Scheduler zeitgesteuert und autonom nutzbar.
Führt geplante System-Checks, Hardware-Prüfungen und Statusberichte zu festgelegten
Uhrzeiten oder Intervallen vollautomatisch im Hintergrund aus.
"""

from __future__ import annotations
import asyncio
import json
import os
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import psutil

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "config" / "cron_jobs.json"
HEARTBEAT_FILE = BASE_DIR / "HEARTBEAT.md"

def _matches_cron_field(val: int, field_expr: str) -> bool:
    """Prüft, ob ein Integer-Wert zu einem Cron-Feld (*, */N, 1,2,3, 1-5) passt."""
    expr = field_expr.strip()
    if expr == "*":
        return True
    if "/" in expr:
        parts = expr.split("/")
        step = int(parts[1]) if parts[1].isdigit() else 1
        return (val % step) == 0
    if "," in expr:
        allowed = [int(x) for x in expr.split(",") if x.isdigit()]
        return val in allowed
    if "-" in expr:
        start, end = [int(x) for x in expr.split("-") if x.isdigit()]
        return start <= val <= end
    if expr.isdigit():
        return val == int(expr)
    return False

def matches_cron(dt: datetime, cron_expr: str) -> bool:
    """Prüft eine standardmäßige 5-Teil-Cron-Expression: (Minute Stunde Tag Monat Wochentag)."""
    parts = cron_expr.strip().split()
    if len(parts) != 5:
        return False
    min_exp, hour_exp, dom_exp, mon_exp, dow_exp = parts
    # Python weekday(): Montag=0, Sonntag=6 -> Cron: Sonntag=0 oder 7, Montag=1
    cron_dow = (dt.weekday() + 1) % 7
    return (
        _matches_cron_field(dt.minute, min_exp) and
        _matches_cron_field(dt.hour, hour_exp) and
        _matches_cron_field(dt.day, dom_exp) and
        _matches_cron_field(dt.month, mon_exp) and
        (_matches_cron_field(cron_dow, dow_exp) or _matches_cron_field(dt.weekday(), dow_exp))
    )

SETTINGS_FILE = BASE_DIR / "config" / "cron_settings.json"

class CronJob:
    def __init__(self, name: str, schedule: str, action: str, enabled: bool = True, description: str = ""):
        self.name = name
        self.schedule = schedule
        self.action = action
        self.enabled = enabled
        self.description = description
        self.last_run_minute: Optional[str] = None

    def should_run(self, dt: datetime) -> bool:
        if not self.enabled:
            return False
        current_minute_key = dt.strftime("%Y-%m-%d %H:%M")
        if self.last_run_minute == current_minute_key:
            return False
        if matches_cron(dt, self.schedule):
            self.last_run_minute = current_minute_key
            return True
        return False

class CronEngine:
    """Zentrale Engine für zeitgesteuerte Hintergrund-Prüfungen & autonome Alerts."""
    def __init__(self, broadcast_fn: Optional[Callable[[dict], None]] = None, logger: Callable[[str], None] = print):
        self.broadcast = broadcast_fn or (lambda msg: None)
        self.logger = logger
        self.jobs: List[CronJob] = []
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self.controller = None
        self.focus_mode = False
        self.settings_file = SETTINGS_FILE
        self.auto_briefing = self._load_auto_briefing()

    def _load_auto_briefing(self) -> bool:
        try:
            if self.settings_file.exists():
                cfg = json.loads(self.settings_file.read_text(encoding="utf-8"))
                return bool(cfg.get("auto_briefing", True))
        except Exception:
            pass
        return True

    def set_auto_briefing(self, enabled: bool) -> None:
        """Aktiviert oder deaktiviert das automatische Morning-Briefing beim Systemstart."""
        self.auto_briefing = bool(enabled)
        try:
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            self.settings_file.write_text(
                json.dumps({"auto_briefing": self.auto_briefing}, indent=2),
                encoding="utf-8"
            )
        except Exception as e:
            self.logger(f"[CronEngine] Fehler beim Speichern von cron_settings.json: {e}")
        state_str = "AKTIVIERT" if self.auto_briefing else "DEAKTIVIERT"
        self.logger(f"[CronEngine] Auto-Briefing bei Start {state_str}.")
        self.broadcast({"type": "auto_briefing_state", "enabled": self.auto_briefing})

    def set_focus_mode(self, enabled: bool) -> None:
        """Aktiviert oder pausiert den Performance-Fokusmodus (friert Hintergrund-Jobs ein)."""
        self.focus_mode = bool(enabled)
        state_str = "AKTIVIERT (Hintergrund-Checks pausiert)" if self.focus_mode else "DEAKTIVIERT (Normalbetrieb)"
        self.logger(f"[CronEngine] Focus Mode {state_str}.")

    def ensure_default_config(self) -> None:
        """Legt standardmäßig geplante Jobs an, die sich an HEARTBEAT.md orientieren."""
        if not CONFIG_FILE.exists():
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            default_jobs = {
                "jobs": [
                    {
                        "name": "heartbeat_health_check",
                        "schedule": "*/15 * * * *",
                        "action": "heartbeat_check",
                        "enabled": True,
                        "description": "Periodische Hardware- & PipeWire-Prüfung nach HEARTBEAT.md alle 15 Minuten."
                    },
                    {
                        "name": "daily_morning_briefing",
                        "schedule": "0 8 * * *",
                        "action": "morning_briefing",
                        "enabled": True,
                        "description": "Autonomes Morgen-Briefing um 08:00 Uhr mit System- & Aufgabenübersicht."
                    },
                    {
                        "name": "hourly_system_telemetry",
                        "schedule": "0 * * * *",
                        "action": "system_check",
                        "enabled": True,
                        "description": "Stündliche System-Telemetrie und RAM/CPU Protokollierung."
                    }
                ]
            }
            CONFIG_FILE.write_text(json.dumps(default_jobs, indent=2, ensure_ascii=False), encoding="utf-8")

    def load_jobs(self) -> None:
        self.ensure_default_config()
        self.jobs = []
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            for j in data.get("jobs", []):
                self.jobs.append(CronJob(
                    name=j.get("name", "unnamed"),
                    schedule=j.get("schedule", "*/30 * * * *"),
                    action=j.get("action", "heartbeat_check"),
                    enabled=j.get("enabled", True),
                    description=j.get("description", "")
                ))
            self.logger(f"[CronEngine] {len(self.jobs)} zeitgesteuerte Aufgaben geladen.")
        except Exception as e:
            self.logger(f"[CronEngine] Fehler beim Laden von cron_jobs.json: {e}")

    async def execute_job(self, job: CronJob) -> None:
        """Führt eine geplante Aktion autonom aus."""
        now_str = datetime.now().strftime("%H:%M:%S")
        self.logger(f"[CronEngine / {now_str}] Starte geplante Aktion: '{job.name}' ({job.action})")

        result_text = ""
        is_critical = False

        if job.action == "heartbeat_check":
            result_text, is_critical = self._run_heartbeat_check()
        elif job.action == "system_check":
            result_text, is_critical = self._run_system_check()
        elif job.action == "morning_briefing":
            result_text, is_critical = self._run_morning_briefing()
        else:
            result_text = f"Benutzerdefinierte Aktion '{job.action}' ausgeführt."

        # Broadcast ans HUD
        self.broadcast({
            "type": "cron_event",
            "job": job.name,
            "action": job.action,
            "result": result_text,
            "is_critical": is_critical,
            "timestamp": now_str
        })

        # Falls kritisch (z.B. CPU > 80°C oder RAM > 90%): Proaktive Sprach- oder Textwarnung
        if is_critical and self.controller:
            try:
                alert_prompt = f"[AUTONOMER HEARTBEAT ALERT]: {result_text}"
                await self.controller.send_text_prompt(alert_prompt)
            except Exception as e:
                self.logger(f"[CronEngine] Warnung konnte nicht an Controller übermittelt werden: {e}")

    def _run_heartbeat_check(self) -> tuple[str, bool]:
        """Prüft die Kriterien aus HEARTBEAT.md."""
        mem = psutil.virtual_memory()
        cpu_usage = psutil.cpu_percent(interval=0.5)

        # PipeWire Audio-Status prüfen
        pipewire_ok = True
        try:
            res = subprocess.run(["pactl", "info"], capture_output=True, text=True, timeout=2)
            pipewire_ok = (res.returncode == 0)
        except Exception:
            pipewire_ok = False

        # Schwellenwerte nach HEARTBEAT.md
        warnings = []
        is_critical = False

        if mem.percent > 90.0:
            warnings.append(f"RAM-Auslastung kritisch hoch: {mem.percent}%")
            is_critical = True

        if cpu_usage > 85.0:
            warnings.append(f"CPU-Last extrem hoch: {cpu_usage}%")
            is_critical = True

        if not pipewire_ok:
            warnings.append("PipeWire Audio-Daemon antwortet nicht.")
            is_critical = True

        if warnings:
            msg = "ACHTUNG: " + " | ".join(warnings)
            self.logger(f"[HEARTBEAT WARNUNG] {msg}")
            return msg, is_critical

        # Alles grün: HEARTBEAT_OK (keine Störung nach Direktive 1)
        ok_msg = f"HEARTBEAT_OK — CPU: {cpu_usage}%, RAM: {mem.percent}%, PipeWire: Aktiv."
        self.logger(f"[HEARTBEAT] {ok_msg}")
        return ok_msg, False

    def _run_system_check(self) -> tuple[str, bool]:
        mem = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=0.2)
        disk = psutil.disk_usage("/")
        status = f"System-Telemetrie: CPU {cpu}%, RAM {mem.percent}% ({round(mem.used/(1024**3), 1)}GB), Disk {disk.percent}%"
        self.logger(f"[TELEMETRIE] {status}")
        return status, False

    def _run_morning_briefing(self) -> tuple[str, bool]:
        date_str = datetime.now().strftime("%A, %d. %B %Y — %H:%M Uhr")

        # 1. Termine abrufen
        events_str = "Keine anstehenden Termine für heute."
        try:
            from actions.calendar_manager import get_upcoming_events
            upcoming = get_upcoming_events(days=1)
            if upcoming:
                events_str = f"{len(upcoming)} anstehende Termine: " + ", ".join([f"{e['title']} ({e['start_time'].split()[-1]})" for e in upcoming[:3]])
        except Exception:
            pass

        # 2. Paket-Updates abrufen
        updates_str = "Systempakete sind auf dem aktuellen Stand."
        try:
            from actions.update_agent import get_pending_updates
            upd = get_pending_updates()
            if upd["total_count"] > 0:
                crit_note = f", davon {upd['critical_count']} sicherheitskritisch" if upd["critical_count"] > 0 else ""
                updates_str = f"{upd['total_count']} Paket-Updates verfügbar{crit_note}."
        except Exception:
            pass

        # 3. Systemmetriken
        mem = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=0.2)

        briefing = (
            f"Guten Morgen, Operator. Status-Report für {date_str}:\n"
            f"• Hardware: CPU {cpu}%, RAM {mem.percent}% belegt.\n"
            f"• Kalender: {events_str}\n"
            f"• System-Updates: {updates_str}\n"
            f"Subsysteme und PipeWire-Audio sind nominal einsatzbereit."
        )
        self.logger(f"[BRIEFING] {briefing}")
        return briefing, False

    async def run_loop(self) -> None:
        """Hintergrund-Schleife: Prüft jede Minute fällige Cron-Jobs."""
        self._running = True
        self.logger("[CronEngine] Scheduler-Schleife aktiv gestartet.")
        while self._running:
            try:
                if self.focus_mode:
                    await asyncio.sleep(15)
                    continue

                now = datetime.now()
                for job in self.jobs:
                    if job.should_run(now):
                        asyncio.create_task(self.execute_job(job))
                await asyncio.sleep(15)  # Alle 15 Sekunden auf Minutensprung prüfen
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger(f"[CronEngine] Schleifenfehler: {e}")
                await asyncio.sleep(30)

    async def _startup_briefing(self) -> None:
        """Führt nach Systemstart ein automatisches kurzes Morning/Startup-Briefing durch (falls aktiviert)."""
        await asyncio.sleep(5)
        if self.auto_briefing and not self.focus_mode:
            text, _ = self._run_morning_briefing()
            if self.controller and hasattr(self.controller, "send_text_prompt"):
                try:
                    await self.controller.send_text_prompt(
                        f"[SYSTEM STARTUP BRIEFING]: Das System ist hochgefahren. Fasse das folgende Morgen-Briefing kurz und prägnant für den Operator zusammen und lies es vor:\n{text}"
                    )
                except Exception:
                    pass

    async def trigger_briefing_now(self) -> str:
        """Manuell ausgelöstes Morning Briefing über das HUD."""
        text, _ = self._run_morning_briefing()
        self.broadcast({
            "type": "cron_event",
            "job": "manual_morning_briefing",
            "action": "morning_briefing",
            "result": text,
            "is_critical": False,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
        if self.controller and hasattr(self.controller, "send_text_prompt"):
            try:
                await self.controller.send_text_prompt(
                    f"[MANUELLES BRIEFING]: Der Operator hat das Morgen-Briefing angefordert. Lies es vor:\n{text}"
                )
            except Exception:
                pass
        return text

    def start(self, controller: Any = None) -> asyncio.Task:
        self.controller = controller
        self.load_jobs()
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self.run_loop())
        if self.auto_briefing:
            asyncio.create_task(self._startup_briefing())
        return self._task

    def stop(self) -> None:
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
        self.logger("[CronEngine] Scheduler gestoppt.")
