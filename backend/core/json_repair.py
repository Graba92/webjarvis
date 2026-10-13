"""
backend/core/json_repair.py — Tool-Call Auto-Repair Engine für J.A.R.V.I.S. AI OS.
Repariert automatisch fehlerhaft formatiertes oder unvollständiges JSON aus schnellen
Gemini Live Sprachinteraktionen (fehlende Klammern, ungeschlossene Strings, trailing commas,
Python-Literale wie True/False/None etc.), um Python-Laufzeitabstürze deterministisch zu verhindern.
"""

from __future__ import annotations
import json
import re
from typing import Any, Tuple

_TRAILING_COMMA_RE = re.compile(r",\s*([\]}])")
_PYTHON_LITERALS = [
    (re.compile(r"\bTrue\b"), "true"),
    (re.compile(r"\bFalse\b"), "false"),
    (re.compile(r"\bNone\b"), "null"),
]

def repair_json_string(raw: str) -> str:
    """
    Nimmt einen potenziell defekten JSON-String und wendet heuristische Reparaturen an:
    1. Markdown-Codeblöcke bereinigen
    2. Unescapte Steuerzeichen normalisieren
    3. Python-spezifische Literale ersetzen (True/False/None)
    4. Trailing Commas entfernen
    5. Ungeschlossene Strings schließen
    6. Fehlende schließende Klammern } und ] am Ende ergänzen
    """
    if not isinstance(raw, str):
        return raw

    s = raw.strip()
    if not s:
        return "{}"

    # 1. Markdown Code-Fences entfernen
    if s.startswith("```"):
        lines = s.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        s = "\n".join(lines).strip()

    # Schnellprüfung: Falls es bereits gültiges JSON ist
    try:
        json.loads(s)
        return s
    except Exception:
        pass

    # 2. Python-Literale ersetzen
    for pat, rep in _PYTHON_LITERALS:
        s = pat.sub(rep, s)

    # 3. Trailing commas vor schließenden Klammern entfernen
    s = _TRAILING_COMMA_RE.sub(r"\1", s)

    # 4. Prüfe, ob es wie ein Dictionary aussieht, aber keine führende Klammer hat
    if not s.startswith("{") and not s.startswith("[") and ":" in s:
        s = "{" + s

    # 5. Zähle ungeschlossene Strings und Klammern
    in_string = False
    escape = False
    open_curly = 0
    open_square = 0

    for ch in s:
        if ch == "\\" and not escape:
            escape = True
            continue
        if ch == '"' and not escape:
            in_string = not in_string
        elif not in_string:
            if ch == '{':
                open_curly += 1
            elif ch == '}':
                if open_curly > 0:
                    open_curly -= 1
            elif ch == '[':
                open_square += 1
            elif ch == ']':
                if open_square > 0:
                    open_square -= 1
        escape = False

    # Falls String nicht geschlossen wurde, Anführungszeichen anhängen
    if in_string:
        s += '"'

    # Trailing comma am Ende vor eventuellen Klammerergänzungen entfernen
    s = s.rstrip()
    if s.endswith(","):
        s = s[:-1].rstrip()

    # Fehlende schließende Klammern in umgekehrter Reihenfolge ergänzen
    s += (']' * open_square)
    s += ('}' * open_curly)

    # Erneuter Versuch
    try:
        json.loads(s)
        return s
    except Exception:
        pass

    # 6. Fallback: Ersetze einfache Anführungszeichen durch doppelte, falls nötig
    if "'" in s and '"' not in s:
        s_quoted = s.replace("'", '"')
        try:
            json.loads(s_quoted)
            return s_quoted
        except Exception:
            pass

    return s

def repair_and_parse_parameters(parameters: Any) -> Tuple[dict, bool, str]:
    """
    Hauptfunktion für den ActionLoader.
    Wandelt beliebige Tool-Parameter (dict, str, unvollständiges JSON) in ein sicheres dict um.
    Rückgabe: (parsed_dict, was_repaired, detail_info)
    """
    if parameters is None:
        return {}, False, "Parameter waren None"

    if isinstance(parameters, dict):
        # Tiefenprüfung: Sind String-Werte im Dict fehlerhaft geschachtelt?
        cleaned = {}
        was_sub_repaired = False
        for k, v in parameters.items():
            if isinstance(v, str) and (v.startswith("{") or v.startswith("[")):
                try:
                    repaired_str = repair_json_string(v)
                    cleaned[k] = json.loads(repaired_str)
                    if repaired_str != v:
                        was_sub_repaired = True
                except Exception:
                    cleaned[k] = v
            else:
                cleaned[k] = v
        return cleaned, was_sub_repaired, "Dict-Struktur validiert"

    if isinstance(parameters, (list, tuple)):
        return {"items": list(parameters)}, True, "Liste in Dict gepackt"

    if isinstance(parameters, str):
        raw_str = parameters.strip()
        if not raw_str:
            return {}, False, "Leerer String"
        
        # Versuche direkte JSON-Dekodierung
        try:
            parsed = json.loads(raw_str)
            if isinstance(parsed, dict):
                return parsed, False, "Valides JSON"
            return {"value": parsed}, True, "Skalarer JSON-Wert in Dict gekapselt"
        except json.JSONDecodeError as err:
            # Auto-Repair anwenden
            repaired = repair_json_string(raw_str)
            try:
                parsed = json.loads(repaired)
                if isinstance(parsed, dict):
                    return parsed, True, f"Repariert: unvollständiges JSON geschlossen ({err.msg})"
                return {"value": parsed}, True, "Reparierter Wert in Dict gekapselt"
            except Exception as final_err:
                # Letzte Rettung: Regex Extraktion von key-value Mustern (auch unquoted)
                fallback_dict = {}
                kv_matches = re.findall(r'["\']?([a-zA-Z0-9_]+)["\']?\s*:\s*["\']?([^,"\';}\]]+?)["\']?(?=\s*[,}\]]|$)', raw_str)
                for k, v in kv_matches:
                    v_clean = v.strip()
                    if v_clean.lower() == "true":
                        fallback_dict[k] = True
                    elif v_clean.lower() == "false":
                        fallback_dict[k] = False
                    elif v_clean.isdigit():
                        fallback_dict[k] = int(v_clean)
                    else:
                        fallback_dict[k] = v_clean
                if fallback_dict:
                    return fallback_dict, True, f"Notfall-Regex-Extraktion ({len(fallback_dict)} Felder)"
                return {"raw_input": raw_str}, True, f"Unreparierbar, als raw_input gekapselt: {final_err}"

    return {"value": parameters}, True, f"Unbekannter Typ {type(parameters).__name__} gekapselt"
