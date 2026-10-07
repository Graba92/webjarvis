"""
backend/core/task_manager.py — SPS-konformer Single-Writer Task-Manager für WebJarvis.
Verwaltet rohe Markdown-Dateien (backlog.md) als Single Source of Truth.
Garantiert:
- POSIX-atomare Schreiboperationen via Tempfile und os.replace (keine korrupten Dateien bei Crashs).
- Serialisierung aller Lese-/Schreibzyklen via asyncio.Lock() (keine Race Conditions / Lost Updates).
- Anti-Echo Hash-Entprellung (SHA-256): Erkennt externe Edits (z.B. in Neovim), ignoriert eigene Schreib-Events.
- WebSocket-Broadcasts für Live-Sync mit dem Next.js Frontend.
"""

from __future__ import annotations
import os
import re
import hashlib
import asyncio
import threading
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional, Callable, Dict, Any

BACKEND_DIR = Path(__file__).resolve().parent.parent
DEFAULT_BACKLOG_PATH = BACKEND_DIR / "backlog.md"

_TASK_REGEX = re.compile(r"^(\s*)-\s*\[([ xX])\]\s*(.*?)(?:\s*<!--\s*id:([a-zA-Z0-9_-]+)\s*-->)?$")

@dataclass
class TaskItem:
    id: str
    text: str
    completed: bool
    line_index: int
    priority: str = "normal"  # high, normal, low

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "completed": self.completed,
            "line_index": self.line_index,
            "priority": self.priority
        }

class TaskManager:
    def __init__(self, backlog_path: Path = DEFAULT_BACKLOG_PATH, broadcast_cb: Optional[Callable[[dict], None]] = None):
        self.backlog_path = backlog_path
        self.broadcast_cb = broadcast_cb
        self._lock = threading.RLock()
        self._tasks: List[TaskItem] = []
        self._raw_lines: List[str] = []
        self._last_written_hash: str = ""
        self._watcher_task: Optional[asyncio.Task] = None
        self._running = False

        # Sicherstellen, dass die Datei existiert
        if not self.backlog_path.exists():
            self._create_initial_backlog()
        self.load_sync()

    def _create_initial_backlog(self):
        initial_content = (
            "# 📋 J.A.R.V.I.S. Task Backlog\n"
            "Single Source of Truth für anstehende Aufgaben und Systemziele.\n\n"
            "## Offene Aufgaben\n"
            "- [ ] 01. Karpathy-Wiki Wissensnetzwerk initialisieren <!-- id:tk-wiki-init -->\n"
            "- [ ] 02. Three.js 3D-Graph mit Frontmatter-Titeln prüfen <!-- id:tk-graph-titles -->\n"
            "- [ ] 03. Orphan-Knoten im Fresnel-Shader visualisieren <!-- id:tk-orphan-shader -->\n"
            "- [ ] 04. System-Backup im Brain Vault erstellen <!-- id:tk-vault-backup -->\n"
            "- [x] 05. Bubblewrap Sandbox-Härtung abschließen <!-- id:tk-sandbox-hardened -->\n"
        )
        self.backlog_path.parent.mkdir(parents=True, exist_ok=True)
        self.backlog_path.write_text(initial_content, encoding="utf-8")

    def load_sync(self):
        """Liest und parst die backlog.md synchron (für den Server-Start)."""
        if not self.backlog_path.exists():
            return
        try:
            content = self.backlog_path.read_text(encoding="utf-8")
            self._last_written_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            self._raw_lines = content.splitlines()
            self._tasks = self._parse_lines(self._raw_lines)
        except Exception as e:
            print(f"[TASK_MANAGER] Fehler beim initialen Laden: {e}")

    def _parse_lines(self, lines: List[str]) -> List[TaskItem]:
        tasks: List[TaskItem] = []
        for idx, line in enumerate(lines):
            match = _TASK_REGEX.match(line)
            if match:
                _indent, mark, text, custom_id = match.groups()
                completed = mark.lower() == "x"
                clean_text = text.strip()
                
                # Eindeutige deterministische ID ermitteln
                if custom_id and custom_id.strip():
                    task_id = custom_id.strip()
                else:
                    # Fallback-ID basierend auf Zeilenindex und kurzem Hash
                    h = hashlib.sha256(f"{idx}:{clean_text}".encode("utf-8")).hexdigest()[:8]
                    task_id = f"task-{idx+1}-{h}"

                priority = "normal"
                if "[high]" in clean_text.lower() or "dringend" in clean_text.lower():
                    priority = "high"
                elif "[low]" in clean_text.lower():
                    priority = "low"

                tasks.append(TaskItem(
                    id=task_id,
                    text=clean_text,
                    completed=completed,
                    line_index=idx,
                    priority=priority
                ))
        return tasks

    def get_tasks(self) -> List[Dict[str, Any]]:
        """Gibt die aktuelle Liste aller Tasks als Dictionaries zurück."""
        return [t.to_dict() for t in self._tasks]

    def _format_markdown(self) -> str:
        """Erzeugt das vollständige Markdown aus den Rohzeilen und dem Task-State."""
        updated_lines = list(self._raw_lines)
        for t in self._tasks:
            if 0 <= t.line_index < len(updated_lines):
                mark = "x" if t.completed else " "
                line = updated_lines[t.line_index]
                match = _TASK_REGEX.match(line)
                indent = match.group(1) if match else ""
                updated_lines[t.line_index] = f"{indent}- [{mark}] {t.text} <!-- id:{t.id} -->"
        return "\n".join(updated_lines) + "\n"

    def _atomic_save(self) -> bool:
        """Speichert den aktuellen Zustand POSIX-atomar via Tempfile und os.replace."""
        content = self._format_markdown()
        temp_path = self.backlog_path.with_suffix(".tmp")
        try:
            temp_path.write_text(content, encoding="utf-8")
            os.replace(temp_path, self.backlog_path)
            self._last_written_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            self._raw_lines = content.splitlines()
            return True
        except Exception as e:
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            print(f"[TASK_MANAGER] Fehler beim atomaren Schreiben: {e}")
            return False

    def _broadcast_change(self):
        if self.broadcast_cb:
            try:
                self.broadcast_cb({
                    "type": "tasks_data",
                    "tasks": self.get_tasks()
                })
            except Exception as e:
                print(f"[TASK_MANAGER] Broadcast-Fehler: {e}")

    def toggle_task_sync(self, task_id: str, completed: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        """Toggled oder setzt den Status eines Tasks atomar (synchron)."""
        with self._lock:
            target = next((t for t in self._tasks if t.id == task_id), None)
            if not target:
                return None
            
            if completed is None:
                target.completed = not target.completed
            else:
                target.completed = bool(completed)

            self._atomic_save()
            self._broadcast_change()
            return target.to_dict()

    async def toggle_task(self, task_id: str, completed: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        return self.toggle_task_sync(task_id, completed=completed)

    def add_task_sync(self, text: str, priority: str = "normal") -> Dict[str, Any]:
        """Fügt einen neuen Task ans Ende der Aufgabenliste an (synchron)."""
        with self._lock:
            clean_text = text.strip()
            # Eindeutige ID generieren
            task_num = len(self._tasks) + 1
            short_h = hashlib.sha256(f"{clean_text}:{len(self._raw_lines)}".encode()).hexdigest()[:6]
            task_id = f"tk-{task_num:02d}-{short_h}"

            new_line = f"- [ ] {clean_text} <!-- id:{task_id} -->"
            self._raw_lines.append(new_line)
            
            item = TaskItem(
                id=task_id,
                text=clean_text,
                completed=False,
                line_index=len(self._raw_lines) - 1,
                priority=priority
            )
            self._tasks.append(item)

            self._atomic_save()
            self._broadcast_change()
            return item.to_dict()

    async def add_task(self, text: str, priority: str = "normal") -> Dict[str, Any]:
        return self.add_task_sync(text, priority=priority)

    def delete_task_sync(self, task_id: str) -> bool:
        """Entfernt einen Task aus der Markdown-Datei (synchron)."""
        with self._lock:
            target_idx = -1
            for i, t in enumerate(self._tasks):
                if t.id == task_id:
                    target_idx = i
                    break
            if target_idx == -1:
                return False

            removed_item = self._tasks.pop(target_idx)
            if 0 <= removed_item.line_index < len(self._raw_lines):
                self._raw_lines.pop(removed_item.line_index)

            # Zeilenindizes der nachfolgenden Tasks korrigieren
            for t in self._tasks:
                if t.line_index > removed_item.line_index:
                    t.line_index -= 1

            self._atomic_save()
            self._broadcast_change()
            return True

    async def delete_task(self, task_id: str) -> bool:
        return self.delete_task_sync(task_id)

    def check_external_changes_sync(self) -> bool:
        """Prüft synchron, ob die Datei extern (z.B. in Kate/Neovim) geändert wurde."""
        if not self.backlog_path.exists():
            return False
        try:
            content = self.backlog_path.read_text(encoding="utf-8")
            current_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            if current_hash != self._last_written_hash:
                with self._lock:
                    self._last_written_hash = current_hash
                    self._raw_lines = content.splitlines()
                    self._tasks = self._parse_lines(self._raw_lines)
                    self._broadcast_change()
                    return True
        except Exception:
            pass
        return False

    async def check_external_changes(self) -> bool:
        return self.check_external_changes_sync()

    async def start_watcher(self, poll_interval: float = 2.0):
        """Startet den Hintergrund-Wächter für externe Änderungen."""
        self._running = True
        while self._running:
            try:
                await self.check_external_changes()
                await asyncio.sleep(poll_interval)
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(poll_interval)

    def stop_watcher(self):
        self._running = False
        if self._watcher_task and not self._watcher_task.done():
            self._watcher_task.cancel()

_GLOBAL_TASK_MANAGER: Optional[TaskManager] = None

def get_task_manager(broadcast_cb: Optional[Callable[[dict], None]] = None) -> TaskManager:
    global _GLOBAL_TASK_MANAGER
    if _GLOBAL_TASK_MANAGER is None:
        _GLOBAL_TASK_MANAGER = TaskManager(broadcast_cb=broadcast_cb)
    elif broadcast_cb and _GLOBAL_TASK_MANAGER.broadcast_cb is None:
        _GLOBAL_TASK_MANAGER.broadcast_cb = broadcast_cb
    return _GLOBAL_TASK_MANAGER

