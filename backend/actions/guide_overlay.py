"""
backend/actions/guide_overlay.py — Visuelle Anleitungs- & Overlay-Engine für WebJarvis.
Generiert interaktive Schritt-für-Schritt-Anleitungen mit Callout-Pfeilen, Markierungen
und Erklärungen, die im Next.js HUD als blätterbare Slideshow aufpoppen.
"""

from __future__ import annotations
import io
import time
import base64
from typing import Optional, List, Dict, Any
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Optionaler Screenshot-Import
try:
    from actions.screen_processor import capture_screen_base64
except ImportError:
    try:
        from screen_processor import capture_screen_base64
    except Exception:
        capture_screen_base64 = None

# Globale Broadcast-Funktion für WebSocket-Push
_BROADCAST_FN = None

def bind_broadcast(fn):
    global _BROADCAST_FN
    _BROADCAST_FN = fn

def _draw_arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], color=(0, 255, 204), width=4):
    """Zeichnet einen leuchtenden Sci-Fi-Pfeil."""
    draw.line([start, end], fill=color, width=width)
    # Pfeilspitze berechnen
    import math
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    angle = math.atan2(dy, dx)
    arrow_len = 18
    p1 = (end[0] - arrow_len * math.cos(angle - math.pi / 6), end[1] - arrow_len * math.sin(angle - math.pi / 6))
    p2 = (end[0] - arrow_len * math.cos(angle + math.pi / 6), end[1] - arrow_len * math.sin(angle + math.pi / 6))
    draw.polygon([end, p1, p2], fill=color)

def create_guide_step_image(
    title: str,
    description: str,
    base_image_b64: Optional[str] = None,
    focus_box: Optional[list[int]] = None, # [x, y, w, h] in Prozent 0-100 oder Pixel
    arrow_from: Optional[list[int]] = None,
    arrow_to: Optional[list[int]] = None,
    theme_color: tuple[int, int, int] = (0, 255, 204) # Cyan default
) -> str:
    """
    Rendert einen annotierten Guide-Step als JPEG Base64.
    Falls kein Basis-Bild übergeben wird, wird ein dunkler HUD-Hintergrund erzeugt.
    """
    if base_image_b64:
        try:
            raw_bytes = base64.b64decode(base_image_b64)
            img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
        except Exception:
            img = Image.new("RGB", (1280, 720), color=(10, 14, 20))
    else:
        # Dunkler HUD-Mockup Background
        img = Image.new("RGB", (1280, 720), color=(10, 14, 20))

    width, height = img.size
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 1. Focus Box hervorheben (falls angegeben)
    if focus_box and len(focus_box) == 4:
        # Wenn Werte <= 100 sind, als Prozentwerte skalieren
        bx, by, bw, bh = focus_box
        if bx <= 100 and by <= 100 and bw <= 100 and bh <= 100:
            x1 = int(bx * width / 100.0)
            y1 = int(by * height / 100.0)
            x2 = int((bx + bw) * width / 100.0)
            y2 = int((by + bh) * height / 100.0)
        else:
            x1, y1, x2, y2 = bx, by, bx + bw, by + bh

        # Box abdunkeln außen, Box-Rahmen cyan
        draw.rectangle([x1, y1, x2, y2], outline=theme_color, width=4)
        # Glühende Ecken
        corner_len = 15
        draw.line([(x1, y1), (x1 + corner_len, y1)], fill=(255, 255, 255), width=3)
        draw.line([(x1, y1), (x1, y1 + corner_len)], fill=(255, 255, 255), width=3)
        draw.line([(x2, y2), (x2 - corner_len, y2)], fill=(255, 255, 255), width=3)
        draw.line([(x2, y2), (x2, y2 - corner_len)], fill=(255, 255, 255), width=3)

    # 2. Pfeil zeichnen (falls angegeben)
    if arrow_from and arrow_to and len(arrow_from) == 2 and len(arrow_to) == 2:
        af_x = int(arrow_from[0] * width / 100.0) if arrow_from[0] <= 100 else arrow_from[0]
        af_y = int(arrow_from[1] * height / 100.0) if arrow_from[1] <= 100 else arrow_from[1]
        at_x = int(arrow_to[0] * width / 100.0) if arrow_to[0] <= 100 else arrow_to[0]
        at_y = int(arrow_to[1] * height / 100.0) if arrow_to[1] <= 100 else arrow_to[1]
        _draw_arrow(draw, (af_x, af_y), (at_x, at_y), color=theme_color, width=4)

    # 3. Text-Banner unten
    banner_height = 110
    draw.rectangle([0, height - banner_height, width, height], fill=(12, 16, 24, 230), outline=theme_color, width=2)
    # Titel & Beschreibung
    draw.text((30, height - banner_height + 15), f"▶ {title.upper()}", fill=theme_color)
    draw.text((30, height - banner_height + 45), description, fill=(240, 240, 240))

    # Kombinieren
    img.paste(overlay, (0, 0), overlay)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def show_interactive_guide(
    guide_id: str,
    title: str,
    steps: list[dict],
    capture_current_screen: bool = False
) -> dict:
    """
    Erstellt ein interaktives Guide-Paket und pusht es via WebSocket an das HUD.
    """
    screen_b64 = None
    if capture_current_screen and capture_screen_base64:
        try:
            b64, _ = capture_screen_base64()
            if b64:
                screen_b64 = b64
        except Exception:
            pass

    processed_steps = []
    for idx, s in enumerate(steps, start=1):
        s_title = s.get("title", f"Schritt {idx}")
        s_desc = s.get("description", "")
        s_box = s.get("focus_box")
        s_arrow_from = s.get("arrow_from")
        s_arrow_to = s.get("arrow_to")
        s_image = s.get("image_base64") or screen_b64

        annotated_b64 = create_guide_step_image(
            title=f"Schritt {idx}: {s_title}",
            description=s_desc,
            base_image_b64=s_image,
            focus_box=s_box,
            arrow_from=s_arrow_from,
            arrow_to=s_arrow_to
        )

        processed_steps.append({
            "step_number": idx,
            "title": s_title,
            "description": s_desc,
            "image_base64": annotated_b64,
            "highlight_action": s.get("highlight_action", "")
        })

    payload = {
        "type": "guide_overlay_show",
        "guide": {
            "id": guide_id or f"guide_{int(time.time())}",
            "title": title,
            "total_steps": len(processed_steps),
            "steps": processed_steps
        }
    }

    if _BROADCAST_FN:
        _BROADCAST_FN(payload)

    return {
        "success": True,
        "guide_id": guide_id,
        "title": title,
        "steps_count": len(processed_steps),
        "message": f"Guide '{title}' mit {len(processed_steps)} Schritten wurde im HUD geöffnet."
    }

def guide_action_handler(parameters: dict | None = None, **kwargs) -> str:
    params = parameters or kwargs
    action = str(params.get("action", "show")).strip().lower()
    
    if action == "show":
        title = str(params.get("title", "Interaktive Anleitung")).strip()
        guide_id = str(params.get("guide_id", "interactive_tutorial")).strip()
        steps = params.get("steps", [])
        use_screen = bool(params.get("capture_screen", False))

        if not steps:
            # Standard Quickstart-Guide falls keine Steps übergeben
            steps = [
                {
                    "title": "3D-Wissensgraph",
                    "description": "Klicke auf Knoten, um Beziehungen zu inspizieren. Doppelklick öffnet den Wiki-Inspektor.",
                    "focus_box": [30, 20, 40, 50],
                    "arrow_from": [15, 45],
                    "arrow_to": [30, 45]
                },
                {
                    "title": "Task Backlog Drawer (Alt+T)",
                    "description": "Aufgaben verwalten, per Pfeil-Tasten sortieren und mit Checkboxen als erledigt markieren.",
                    "focus_box": [80, 10, 18, 80],
                    "arrow_from": [65, 30],
                    "arrow_to": [80, 30]
                },
                {
                    "title": "Sprachsteuerung & Paranoia-Mute",
                    "description": "Sprich mit Jarvis über Gemini Live oder aktiviere den roten Paranoia-Mute zur Mikrofon-Freigabe.",
                    "focus_box": [35, 75, 30, 20],
                    "arrow_from": [50, 60],
                    "arrow_to": [50, 75]
                }
            ]

        res = show_interactive_guide(guide_id, title, steps, capture_current_screen=use_screen)
        return f"[GUIDE_LAUNCHED] {res.get('message')}"

    elif action == "close":
        if _BROADCAST_FN:
            _BROADCAST_FN({"type": "guide_overlay_close"})
        return "[GUIDE_CLOSED] Anleitung im HUD geschlossen."

    return f"Unbekannte Guide-Aktion '{action}'."

TOOL = {
    "name": "show_guide",
    "description": "Blendet eine interaktive, bebilderte Schritt-für-Schritt-Anleitung mit Pfeilen und Erklärungen im HUD ein, durch die der User blättern kann.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "Aktion: 'show' (Anleitung öffnen) oder 'close' (Anleitung schließen)."
            },
            "title": {
                "type": "STRING",
                "description": "Titel der Anleitung (z. B. 'Task-Backlog Anleitung' oder 'Erste Schritte')."
            },
            "capture_screen": {
                "type": "BOOLEAN",
                "description": "True, um den aktuellen Bildschirm zu fotografieren und als Hintergrund für die Pfeile zu nutzen."
            },
            "steps": {
                "type": "ARRAY",
                "description": "Liste der Anleitungs-Schritte mit title, description, focus_box [x,y,w,h in %] und arrow_from [x,y], arrow_to [x,y].",
                "items": {
                    "type": "OBJECT"
                }
            }
        }
    },
    "handler": guide_action_handler
}
