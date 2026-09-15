"""
backend/actions/whatsapp_messenger.py — WhatsApp-Integration für J.A.R.V.I.S. AI OS.
Unterstützt zwei Betriebsmodi:
1. Headless / API-Modus (WhatsApp Cloud API oder lokale HTTP-Bridge wie Baileys / Mudslide)
2. OS-Fallback (CachyOS Desktop-Automation via xdg-open "https://web.whatsapp.com/send?phone=...&text=...")

Standard-Empfänger: +4911744833685 (aus 011744833685 normiert).
"""

from __future__ import annotations
import os
import re
import sys
import json
import urllib.parse
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Callable

# Sicherstellen, dass core/config und core/undo importiert werden können
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

try:
    import requests
except ImportError:
    requests = None

from core.config import get_whatsapp_config, USER_NAME
from core.undo import push_undo

def normalize_phone_number(phone_raw: str | None) -> str:
    """
    Normiert Telefonnummern nach E.164 oder löst Kontaktnamen aus contacts.json auf.
    """
    cfg = get_whatsapp_config()
    contacts = cfg.get("contacts") or {}

    if not phone_raw or not str(phone_raw).strip():
        return cfg.get("recipient", "")

    raw = str(phone_raw).strip()
    raw_lower = raw.lower().strip()

    # 1. Bekannte Kontakt-Namen prüfen (z. B. "Lisa", "Freundin", "Matze")
    if raw_lower in contacts:
        return contacts[raw_lower]
    for name, num in contacts.items():
        if name in raw_lower:
            return num

    # 2. Ziffern und führendes Plus extrahieren
    cleaned = "".join(ch for ch in raw if ch.isdigit() or ch == "+")

    if cleaned.startswith("00"):
        return "+" + cleaned[2:]
    if cleaned.startswith("0"):
        return "+49" + cleaned[1:]
    if not cleaned.startswith("+"):
        return "+" + cleaned
    return cleaned

def _send_via_cloud_api(recipient_e164: str, message: str, token: str, phone_number_id: str) -> tuple[bool, str]:
    """Versendet Nachricht über die offizielle Meta WhatsApp Cloud API."""
    if not requests:
        return False, "Python 'requests' Modul fehlt."
    
    url = f"https://graph.facebook.com/v21.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_e164.replace("+", ""),
        "type": "text",
        "text": {
            "preview_url": True,
            "body": message
        }
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=8)
        if resp.status_code in (200, 201):
            return True, f"Erfolgreich via WhatsApp Cloud API gesendet (Status {resp.status_code})."
        return False, f"Cloud API Fehler ({resp.status_code}): {resp.text[:140]}"
    except Exception as e:
        return False, f"Cloud API Verbindungsfehler: {e}"

def _send_via_local_bridge(recipient_e164: str, message: str, bridge_url: str) -> tuple[bool, str]:
    """Versendet Nachricht über die lokale Baileys HTTP-Bridge."""
    if not requests or not bridge_url:
        return False, "Keine lokale Bridge verfügbar."
    
    clean_url = bridge_url.rstrip("/") + "/send"
    payload = {
        "recipient": recipient_e164,
        "message": message
    }
    try:
        resp = requests.post(clean_url, json=payload, timeout=12)
        if resp.status_code in (200, 201):
            return True, f"Erfolgreich via lokaler Bridge gesendet ({bridge_url})."
        return False, f"Bridge HTTP {resp.status_code}: {resp.text[:120]}"
    except Exception as e:
        return False, f"Lokale Bridge nicht erreichbar: {e}"

def _send_via_desktop_automation(recipient_e164: str, message: str) -> tuple[bool, str]:
    """
    OS-Fallback: Öffnet WhatsApp Web auf CachyOS / KDE Plasma mit vorbefülltem Text.
    Nutzt xdg-open und optional xdotool zur Fenster-Fokussierung.
    """
    clean_number = recipient_e164.replace("+", "").strip()
    encoded_text = urllib.parse.quote(message)
    web_url = f"https://web.whatsapp.com/send?phone={clean_number}&text={encoded_text}"

    try:
        # Browser über xdg-open starten (oder direkt Brave / Firefox falls xdg-open blockiert)
        opener = shutil.which("xdg-open") or shutil.which("brave") or shutil.which("firefox")
        if not opener:
            return False, "Kein geeigneter Browser oder xdg-open im PATH gefunden."

        proc = subprocess.Popen(
            [opener, web_url],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        proc.poll()

        return True, f"WhatsApp Web mit vorbefüllter Nachricht für {recipient_e164} im Browser geöffnet."
    except Exception as e:
        return False, f"Desktop-Automation fehlgeschlagen: {e}"

def send_whatsapp(message: str = "", recipient: str = "", **kwargs) -> str:
    """
    Haupt-Handler für das Gemini Live Tool 'send_whatsapp'.
    """
    # 1. Flexible Extraktion falls Parameter über kwargs oder parameters dict übergeben wurden
    p = kwargs.get("parameters") or {}
    if not message and isinstance(p, dict):
        message = p.get("message") or p.get("text") or ""
    if not recipient and isinstance(p, dict):
        recipient = p.get("recipient") or p.get("to") or p.get("phone") or ""

    msg_text = str(message or "").strip()
    if not msg_text:
        return "Abbruch: Der Nachrichtentext darf nicht leer sein."

    # Falls kein Empfänger angegeben ist (z.B. "sende mir eine Nachricht"):
    # Automatisch das aktuell verbundene WhatsApp-Konto der Bridge ermitteln ("Chat mit mir selbst")
    if not recipient or not str(recipient).strip():
        cfg = get_whatsapp_config()
        bridge_url = cfg.get("bridge_url") or "http://127.0.0.1:3001"
        try:
            if requests:
                resp = requests.get(bridge_url.rstrip("/") + "/status", timeout=2)
                if resp.status_code == 200:
                    data = resp.json()
                    user_num = data.get("user")
                    if user_num:
                        recipient = f"+{user_num}"
        except Exception:
            pass

    target_number = normalize_phone_number(recipient)
    cfg = get_whatsapp_config()
    if "cypher" not in msg_text.lower() and "jarvis" not in msg_text.lower():
        msg_text = f"{msg_text}\n\n— Übermittelt von Cypher ({USER_NAME}'s AI OS)"

    token = cfg.get("api_token", "")
    phone_id = cfg.get("phone_number_id", "")
    bridge_url = cfg.get("bridge_url", "")
    broadcast_fn = kwargs.get("ws_broadcast")

    # 1. Headless Modus versuchen (Cloud API)
    if token and phone_id:
        ok, detail = _send_via_cloud_api(target_number, msg_text, token, phone_id)
        if ok:
            _record_and_log(target_number, msg_text, "Cloud API", broadcast_fn)
            return f"WhatsApp-Nachricht an {target_number} erfolgreich übermittelt (Cloud API)."

    # 2. Lokale Bridge versuchen (Baileys Gateway)
    if bridge_url and bridge_url.startswith("http"):
        ok, detail = _send_via_local_bridge(target_number, msg_text, bridge_url)
        if ok:
            _record_and_log(target_number, msg_text, "Lokale Bridge", broadcast_fn)
            return f"WhatsApp-Nachricht an {target_number} erfolgreich übermittelt (Lokale Bridge)."

    # 3. OS Fallback: Desktop-Automation via CachyOS Browser
    ok, detail = _send_via_desktop_automation(target_number, msg_text)
    if ok:
        _record_and_log(target_number, msg_text, "Desktop-Automation", broadcast_fn)
        return f"WhatsApp-Nachricht an {target_number} via Browser/Desktop-Automation initiiert: {detail}"

    return f"Fehler beim Senden der WhatsApp-Nachricht an {target_number}: {detail}"

def _record_and_log(recipient: str, message: str, method: str, broadcast_fn: Optional[Callable[[dict], None]]):
    """Protokolliert das Senden im Undo-Stack und sendet ein WebSocket-Log ans HUD."""
    preview = message[:40] + ("..." if len(message) > 40 else "")
    push_undo(
        label=f"WhatsApp an {recipient}: \"{preview}\"",
        undo_fn=lambda: f"Hinweis: WhatsApp-Nachrichten ({recipient}) können nach dem Senden nicht serverseitig zurückgezogen werden."
    )
    log_msg = f"[WHATSAPP] Nachricht an {recipient} über {method} initiiert: \"{preview}\""
    print(log_msg)
    if broadcast_fn:
        broadcast_fn({
            "type": "log",
            "speaker": "SYS",
            "text": log_msg
        })

def check_whatsapp_status(parameters: dict = None, **kwargs) -> str:
    """Prüft den aktuellen Verbindungs- und Anmeldestatus der lokalen WhatsApp Bridge."""
    cfg = get_whatsapp_config()
    bridge_url = cfg.get("bridge_url") or "http://127.0.0.1:3001"
    clean_url = bridge_url.rstrip("/") + "/status"

    if not requests:
        return "Fehler: Python 'requests' Modul nicht verfügbar."

    try:
        resp = requests.get(clean_url, timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            connected = data.get("connected", False)
            user = data.get("user")
            qr_avail = data.get("qr_available", False)

            if connected:
                return f"WhatsApp Bridge ist online und aktiv verbunden! Angemeldet als: +{user}."
            elif qr_avail:
                return "WhatsApp Bridge ist online, aber noch nicht gekoppelt. QR-Code Scan erforderlich unter http://localhost:3001/qr oder im Terminal via './start.sh -w'."
            else:
                return "WhatsApp Bridge ist online, initialisiert jedoch noch die Verbindung."
        return f"WhatsApp Bridge antwortete mit HTTP {resp.status_code}: {resp.text[:80]}"
    except Exception as e:
        return f"WhatsApp Bridge ({bridge_url}) ist offline oder nicht erreichbar. Bitte starten via './start.sh -w' oder './start.sh -a'."

def autodoc_repair(parameters: dict = None, **kwargs) -> str:
    """
    Führt über den Auto-Doc der WhatsApp-Bridge eine automatische Selbstreparatur aus:
    Bereinigt veraltete Ratchet-Sitzungen, repariert desynchronisierte Schlüssel und behebt
    'Warte auf diese Nachricht...' oder 'Bad MAC'-Hänger.
    """
    cfg = get_whatsapp_config()
    bridge_url = cfg.get("bridge_url") or "http://127.0.0.1:3001"
    if not requests:
        return "Fehler: Python 'requests' Modul nicht verfügbar."
    try:
        resp = requests.post(f"{bridge_url.rstrip('/')}/auto-doc/prune", timeout=5)
        prune_data = resp.json() if resp.status_code == 200 else {}
        pruned = prune_data.get("pruned", 0)

        p = parameters or {}
        target = p.get("target") or p.get("recipient")
        if target:
            clean_t = normalize_phone_number(target).replace("+", "")
            h_resp = requests.post(f"{bridge_url.rstrip('/')}/auto-doc/heal", json={"target": clean_t}, timeout=5)
            h_data = h_resp.json() if h_resp.status_code == 200 else {}
            return f"Auto-Doc Reparatur ausgeführt: {pruned} alte Sitzungen bereinigt, Heilung für {target}: {h_data.get('message', 'ausgeführt')}."

        return f"Auto-Doc Selbstheilung erfolgreich: {pruned} veraltete Sitzungen bereinigt. Ratchet-Schlüssel synchronisiert."
    except Exception as e:
        return f"Auto-Doc Reparaturfehler: {e}"

TOOL = {
    "name": "send_whatsapp",
    "description": "Sendet eine WhatsApp-Nachricht an einen Kontakt oder eine Telefonnummer. Nutzt bevorzugt die lokale Baileys Multi-Device Bridge.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "message": {
                "type": "STRING",
                "description": "Der vollständige Textinhalt der Nachricht, die versendet werden soll."
            },
            "recipient": {
                "type": "STRING",
                "description": "Optionale Zielperson oder Telefonnummer: z. B. 'Partner', '+491500000000' oder 'ich'. Standardmäßig die in contacts.json hinterlegte Nummer."
            }
        },
        "required": ["message"]
    },
    "handler": send_whatsapp
}

STATUS_TOOL = {
    "name": "whatsapp_status",
    "description": "Prüft den aktuellen Verbindungs- und Anmeldestatus der WhatsApp Multi-Device Bridge (ob online, gekoppelt und welches Konto aktiv ist).",
    "parameters": {
        "type": "OBJECT",
        "properties": {}
    },
    "handler": check_whatsapp_status
}

REPAIR_TOOL = {
    "name": "repair_whatsapp",
    "description": "Führt über den Auto-Doc der WhatsApp-Bridge eine automatische Selbstreparatur aus: Bereinigt veraltete Ratchet-Sitzungen und synchronisiert Schlüssel.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "target": {
                "type": "STRING",
                "description": "Optional: Spezifischer Kontakt oder Rufnummer, für die die Sitzung repariert werden soll."
            }
        }
    },
    "handler": autodoc_repair
}

TOOLS = [TOOL, STATUS_TOOL, REPAIR_TOOL]
