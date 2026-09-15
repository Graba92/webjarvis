"""
backend/core/action_loader.py — Dynamische Tool-Discovery für das Gemini Live Backend.
Durchsucht das actions/-Verzeichnis nach Modulen mit TOOL oder TOOLS Deklarationen.
"""

from __future__ import annotations
import importlib.util
import inspect
import re
import sys
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional, Any
from core.json_repair import repair_and_parse_parameters

_NAME_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]{0,63}$")
_DEFAULT_PARAMS = {"type": "OBJECT", "properties": {}}
_CTX_KEYS = ("player", "speak", "response", "session_memory", "ws_broadcast", "registry")

@dataclass
class ActionRecord:
    name: str
    description: str = ""
    parameters: dict = field(default_factory=lambda: dict(_DEFAULT_PARAMS))
    handler: Optional[Callable] = None
    file: str = ""
    valid: bool = False
    error: str = ""

class ActionRegistry:
    def __init__(self, actions: dict[str, ActionRecord], logger: Callable[[str], None] = print):
        self._actions = actions
        self._all_records: list[ActionRecord] = []
        self._logger = logger

    def get_tool_declarations(self) -> list[dict]:
        return [
            {"name": rec.name, "description": rec.description, "parameters": rec.parameters}
            for rec in self._actions.values()
        ]

    def has(self, name: str) -> bool:
        return name in self._actions

    def names(self) -> set[str]:
        return set(self._actions.keys())

    def reload_mcp(self, mcp_config: Path) -> list[str]:
        """Lädt MCP-Tools basierend auf der aktuellen mcp_servers.json dynamisch in die Registry."""
        to_remove = [name for name, rec in self._actions.items() if rec.file.startswith("mcp_servers.json")]
        for name in to_remove:
            del self._actions[name]

        added = []
        if mcp_config.exists():
            try:
                from core.mcp_client import MCPManager
                mcp_mgr = MCPManager(mcp_config, logger=self._logger)
                mcp_tools = mcp_mgr.load_mcp_servers()
                for raw_tool in mcp_tools:
                    rec = _validate_single(raw_tool, raw_tool.get("file", "mcp_servers.json"))
                    if rec.valid and rec.name not in self._actions:
                        self._actions[rec.name] = rec
                        added.append(rec.name)
                        self._logger(f"[ActionRegistry / MCP] Dynamisch aktualisiert: {rec.name}")
            except Exception as e:
                self._logger(f"[ActionRegistry] Fehler beim dynamischen MCP-Reload: {e}")
        return added

    def run(self, name: str, parameters: dict | str | Any, ctx: dict | None = None) -> str:
        rec = self._actions.get(name)
        if rec is None or not rec.valid:
            return f"Action '{name}' ist nicht registriert oder verfügbar."
        try:
            # Tool-Call Auto-Repair: Repariert defektes JSON oder unvollständige Strukturen
            repaired_params, was_repaired, repair_info = repair_and_parse_parameters(parameters)
            if was_repaired:
                self._logger(f"[Auto-Repair] Tool '{name}' Parameter repariert: {repair_info}")
            return _call_handler(rec.handler, repaired_params, ctx or {}) or "Erledigt."
        except Exception as e:
            self._logger(f"[ActionRegistry] Fehler bei Ausführung von '{name}': {e}")
            traceback.print_exc()
            return f"Fehler bei Tool '{name}': {e}"

def _call_handler(fn: Callable, parameters: dict, ctx: dict) -> str:
    sig = inspect.signature(fn)
    has_var_kw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
    kwargs = {}
    for key in _CTX_KEYS:
        if has_var_kw or key in sig.parameters:
            kwargs[key] = ctx.get(key)

    # 1. Wenn die Funktion explizit einen Parameter namens 'parameters' verlangt:
    if "parameters" in sig.parameters:
        return fn(parameters=parameters, **kwargs)

    # 2. Wenn die Funktion benannte Parameter wie message, recipient, label etc. erwartet:
    call_args = dict(parameters) if isinstance(parameters, dict) else {}
    if has_var_kw:
        call_args["parameters"] = parameters
        call_args.update(kwargs)
        return fn(**call_args)

    # Falls die Funktion kein **kwargs hat, nur passende deklarierte Argumente übergeben:
    filtered_args = {k: v for k, v in call_args.items() if k in sig.parameters}
    filtered_args.update({k: v for k, v in kwargs.items() if k in sig.parameters})
    return fn(**filtered_args)

def _validate_single(tool: dict, filename: str) -> ActionRecord:
    if not isinstance(tool, dict):
        return ActionRecord(name=Path(filename).stem, file=filename, error="TOOL ist kein Dictionary.")
    name = tool.get("name")
    if not isinstance(name, str) or not _NAME_RE.match(name):
        return ActionRecord(name=str(name or Path(filename).stem), file=filename, error="Ungültiger Identifier.")
    description = tool.get("description", "").strip()
    if not description:
        return ActionRecord(name=name, file=filename, error="Fehlende Beschreibung.")
    parameters = tool.get("parameters", _DEFAULT_PARAMS)
    handler = tool.get("handler")
    if not callable(handler):
        return ActionRecord(name=name, file=filename, error="Handler ist nicht callable.")
    return ActionRecord(name=name, description=description, parameters=parameters, handler=handler, file=filename, valid=True)

def discover_actions(actions_dir: Path, reserved_names: set[str] | None = None, logger: Callable[[str], None] = print) -> ActionRegistry:
    reserved = reserved_names or set()
    actions_dir.mkdir(parents=True, exist_ok=True)
    valid: dict[str, ActionRecord] = {}
    all_records: list[ActionRecord] = []

    files = sorted(actions_dir.glob("*.py"), key=lambda p: p.name)
    for path in files:
        if path.name.startswith("_"):
            continue
        try:
            module_name = f"actions.{path.stem}"
            module = sys.modules.get(module_name)
            if module is None:
                spec = importlib.util.spec_from_file_location(module_name, path)
                if spec is None or spec.loader is None:
                    continue
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)

            tools_list = []
            if hasattr(module, "TOOLS") and isinstance(module.TOOLS, list):
                tools_list = module.TOOLS
            elif hasattr(module, "TOOL") and isinstance(module.TOOL, dict):
                tools_list = [module.TOOL]

            if not tools_list:
                continue

            for raw_tool in tools_list:
                rec = _validate_single(raw_tool, path.name)
                if rec.valid and rec.name in reserved:
                    rec.valid = False
                    rec.error = f"Kollision mit reserviertem Core-Tool '{rec.name}'."
                elif rec.valid and rec.name in valid:
                    rec.valid = False
                    rec.error = f"Tool-Name '{rec.name}' bereits vorhanden."

                all_records.append(rec)
                if rec.valid:
                    valid[rec.name] = rec
                    logger(f"[ActionLoader] Aktiviert: {rec.name} ({path.name})")
                else:
                    logger(f"[ActionLoader] Abgelehnt: {rec.name} ({path.name}) — {rec.error}")

        except Exception as e:
            logger(f"[ActionLoader] Fehler beim Laden von {path.name}: {e}")
            all_records.append(ActionRecord(name=path.stem, file=path.name, error=str(e)))

    # MCP-Server einbinden (Model Context Protocol Bridge)
    mcp_config = actions_dir.parent / "config" / "mcp_servers.json"
    if mcp_config.exists():
        try:
            from core.mcp_client import MCPManager
            mcp_mgr = MCPManager(mcp_config, logger=logger)
            mcp_tools = mcp_mgr.load_mcp_servers()
            for raw_tool in mcp_tools:
                rec = _validate_single(raw_tool, raw_tool.get("file", "mcp"))
                if rec.valid and rec.name not in valid and rec.name not in reserved:
                    valid[rec.name] = rec
                    all_records.append(rec)
                    logger(f"[ActionLoader / MCP] Aktiviert: {rec.name}")
        except Exception as e:
            logger(f"[ActionLoader] Fehler beim Laden von MCP-Servern: {e}")

    reg = ActionRegistry(valid, logger)
    reg._all_records = all_records
    return reg
