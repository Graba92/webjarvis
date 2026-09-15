"""
backend/core/confirm.py — Hardware Confirmation Gate.
Verhindert die willkürliche Ausführung irreversibler Aktionen (Reboot, Shutdown, WiFi Aus).
Erfordert eine echte physische Bestätigung über das HUD.
"""

from __future__ import annotations
import threading
import time
import asyncio
from dataclasses import dataclass
from typing import Callable, Optional

TIMEOUT_SECONDS = 90.0

@dataclass
class _Pending:
    action: str
    label: str
    detail: str
    run: Callable[[], str]
    at: float
    timeout: float = TIMEOUT_SECONDS
    future: Optional[asyncio.Future] = None
    event: Optional[threading.Event] = None

_pending: Optional[_Pending] = None
_lock = threading.Lock()
_main_loop: Optional[asyncio.AbstractEventLoop] = None

_show_cb: Optional[Callable] = None
_hide_cb: Optional[Callable[[], None]] = None
_log_cb: Optional[Callable[[str], None]] = None

def set_event_loop(loop: asyncio.AbstractEventLoop) -> None:
    global _main_loop
    _main_loop = loop

def bind(show, hide, log=None, loop=None) -> None:
    global _show_cb, _hide_cb, _log_cb, _main_loop
    _show_cb, _hide_cb, _log_cb = show, hide, log
    if loop:
        _main_loop = loop

def _log(msg: str) -> None:
    if _log_cb:
        try:
            _log_cb(msg)
        except Exception:
            pass

def request(
    action: str = "",
    label: str = "",
    detail: str = "",
    run: Optional[Callable[[], str]] = None,
    timeout: float = TIMEOUT_SECONDS,
    **kwargs
) -> str:
    """Registriert eine Bestätigungsanforderung und triggert den HUD-Dialog."""
    global _pending

    act = action or kwargs.get("key", "system_action")
    lbl = label or kwargs.get("title", "Bestätigung erforderlich")
    det = detail or kwargs.get("detail", f"Möchten Sie '{lbl}' wirklich ausführen?")
    fn = run or kwargs.get("run") or (lambda: "Keine Aktion hinterlegt.")
    to = float(timeout or kwargs.get("timeout", TIMEOUT_SECONDS))

    event = threading.Event()
    future = None
    if _main_loop and _main_loop.is_running():
        try:
            future = _main_loop.create_future()
        except Exception:
            future = None

    with _lock:
        _pending = _Pending(
            action=act,
            label=lbl,
            detail=det,
            run=fn,
            at=time.monotonic(),
            timeout=to,
            future=future,
            event=event
        )

    _log(f"SYS: [SAFETY GATE] Anforderung registriert: action='{act}', label='{lbl}' ({int(to)}s Timeout)")

    if _show_cb:
        try:
            import inspect
            sig = inspect.signature(_show_cb)
            if len(sig.parameters) >= 4:
                _show_cb(act, lbl, det, int(to))
            else:
                _show_cb(act, lbl, det)
        except Exception as e:
            with _lock:
                _pending = None
            return f"Bestätigungsdialog konnte nicht geöffnet werden: {e}."

    return (
        f"[HARDWARE_CONFIRMATION_GATE_TRIGGERED] Ein bernsteinfarbenes Sicherheits-Banner wurde auf dem HUD geöffnet für: '{lbl}'. "
        f"Informiere den Benutzer in einem kurzen Satz auf Deutsch, dass das Bestätigungs-Banner auf dem HUD aktiviert wurde und auf seine Freigabe wartet."
    )

def resolve(accepted: bool) -> bool:
    """Löst die anhängige Bestätigung auf (Freigabe erteilt oder abgelehnt)."""
    global _pending

    with _lock:
        p, _pending = _pending, None

    if _hide_cb:
        try:
            _hide_cb()
        except Exception:
            pass

    if p is None:
        _log("SYS: [SAFETY GATE] Keine anhängige Bestätigung vorhanden.")
        return False

    elapsed = time.monotonic() - p.at
    if elapsed > p.timeout:
        _log(f"SYS: [SAFETY GATE] Freigabe abgelaufen ({elapsed:.1f}s > {p.timeout}s) — '{p.label}'")
        if p.future and not p.future.done() and _main_loop and _main_loop.is_running():
            _main_loop.call_soon_threadsafe(p.future.set_result, False)
        if p.event:
            p.event.set()
        return False

    # Async Future & Threading Event auflösen
    if p.future and not p.future.done() and _main_loop and _main_loop.is_running():
        _main_loop.call_soon_threadsafe(p.future.set_result, accepted)
    if p.event:
        p.event.set()

    if not accepted:
        _log(f"SYS: [SAFETY GATE] Freigabe ABGELEHNT vom Benutzer — '{p.label}'")
        return False

    _log(f"SYS: [SAFETY GATE] Freigabe ERTEILT für: '{p.label}'. Starte Ausführung...")

    def _worker():
        try:
            result = p.run() or "Erfolgreich ausgeführt."
            _log(f"SYS: [SAFETY GATE] Bestätigt & Ausgeführt — '{p.label}': {result}")
        except Exception as e:
            _log(f"ERR: [SAFETY GATE] Fehler bei Ausführung von '{p.label}': {e}")

    threading.Thread(target=_worker, daemon=True, name=f"confirm-{p.action}").start()
    return True

def pending_info() -> Optional[dict]:
    with _lock:
        if _pending is None or (time.monotonic() - _pending.at > _pending.timeout):
            return None
        rem = int(_pending.timeout - (time.monotonic() - _pending.at))
        return {
            "action": _pending.action,
            "key": _pending.action,
            "label": _pending.label,
            "title": _pending.label,
            "detail": _pending.detail,
            "timeout": max(0, rem)
        }
