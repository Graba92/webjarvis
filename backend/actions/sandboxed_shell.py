"""
backend/actions/sandboxed_shell.py — Bubblewrap Sandboxed Shell Action für J.A.R.V.I.S. AI OS.
Ermöglicht die sichere, isolierte Ausführung von Shell-Befehlen, Skripten und Tests in einer
gehärteten CachyOS Bubblewrap Sandbox (bwrap).
"""

from __future__ import annotations
from typing import Optional
from core.sandbox import execute_sandboxed, is_bubblewrap_available

def sandboxed_shell_handler(parameters: dict, **kwargs) -> str:
    command = str(parameters.get("command", "")).strip()
    if not command:
        return "Abbruch: Kein Shell-Befehl angegeben."

    allow_network = bool(parameters.get("allow_network", True))
    timeout = int(parameters.get("timeout", 30))
    cwd = parameters.get("working_dir")

    broadcast_fn = kwargs.get("ws_broadcast")
    if broadcast_fn:
        broadcast_fn({
            "type": "log",
            "speaker": "SYS",
            "text": f"[SANDBOX EXEC] Starte isolierten Befehl: {command[:60]}..."
        })

    exit_code, stdout, stderr, was_sandboxed = execute_sandboxed(
        command=command,
        cwd=cwd,
        allow_network=allow_network,
        timeout=timeout
    )

    status_tag = "✓ BWRAP SANDBOX" if was_sandboxed else "! UNGESANDBOXED (Fallback)"
    out_lines = []
    out_lines.append(f"[{status_tag}] Exit-Code: {exit_code}")

    clean_stdout = stdout.strip()
    if clean_stdout:
        out_lines.append(f"STDOUT:\n{clean_stdout}")

    clean_stderr = stderr.strip()
    if clean_stderr:
        out_lines.append(f"STDERR:\n{clean_stderr}")

    if not clean_stdout and not clean_stderr:
        out_lines.append("(Befehl ohne Textausgabe beendet)")

    return "\n".join(out_lines)

TOOL = {
    "name": "execute_sandboxed_shell",
    "description": "Führt potenziell riskante oder externe Shell-Befehle isoliert in einer CachyOS Bubblewrap Sandbox (bwrap) aus. Schützt das Wirtssystem und persönliche Dateien. HINWEIS: Nicht für Host-Systemdienste (systemctl) nutzen. Für WhatsApp-Status immer das Tool 'whatsapp_status' aufrufen.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "command": {
                "type": "STRING",
                "description": "Der vollständige Shell-Befehl oder das Skript, das isoliert in der Sandbox ausgeführt werden soll."
            },
            "allow_network": {
                "type": "BOOLEAN",
                "description": "Erlaubt Netzwerk- und Internetzugriff innerhalb der Sandbox (Standard: true). Für maximale Isolation auf false setzen."
            },
            "timeout": {
                "type": "INTEGER",
                "description": "Maximal zulässige Laufzeit in Sekunden vor automatischem Abbruch (Standard: 30)."
            }
        },
        "required": ["command"]
    },
    "handler": sandboxed_shell_handler
}
