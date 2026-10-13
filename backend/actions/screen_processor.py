"""
backend/actions/screen_processor.py — Bildschirmaufnahme & Kamera-Vision.
Erstellt hochoptimierte JPEG-Frames (1280x720, 82% Qualität) für multimodale Analysen.
"""

from __future__ import annotations
import io
import base64
from PIL import Image

def capture_screen_base64() -> tuple[str, str]:
    try:
        import mss
        with mss.mss() as sct:
            monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
            sct_img = sct.grab(monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            img.thumbnail((1280, 720))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=82)
            b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")
            return b64_str, f"Screenshot aufgenommen ({img.width}x{img.height})."
    except Exception as e:
        return "", f"Screenshot-Fehler: {e}"

def screen_process(parameters: dict | None = None, **kwargs) -> str:
    b64_str, msg = capture_screen_base64()
    if not b64_str:
        return msg
    return f"[MULTIMODAL_SCREENSHOT_READY] {msg} Das Bild wurde an die Session übergeben."

TOOL = {
    "name": "screen_process",
    "description": "Nimmt den aktuellen Bildschirminhalt auf, um Fenster, Fehlermeldungen oder Code visuell zu analysieren.",
    "parameters": {
        "type": "OBJECT",
        "properties": {}
    },
    "handler": screen_process
}
