"""backend/llm/provider_router.py — Hybrides Multi-LLM Gateway für WebJarvis (Jarvis & Friday).

Ermöglicht dynamisches Routing zwischen lokalen SLMs (Ollama) und Cloud-Providern
(Gemini, Anthropic Claude, OpenAI) mit automatischem Fallback, Quota-Protection und Zero-Token-Ops.
"""

from __future__ import annotations

import os
import json
import asyncio
import logging
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import urllib.request
import urllib.error

logger = logging.getLogger("WebJarvis.LLMRouter")
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
    )


class ModelTier(str, Enum):
    """Klassifikation der Modell-Leistungsstufen für kosten- und ressourcenbewusstes Routing.

    Attributes:
        LOCAL_ROUTINE: Lokale SLMs via Ollama (qwen2.5-coder, mistral) für 0 Token-Kosten und Privatsphäre.
        CLOUD_FAST: Schnelle Cloud-Modelle (Gemini Flash, GPT-4o-mini) für Standardabfragen.
        CLOUD_REASONING: Große Denkmodelle (Claude 3.5 Sonnet, Gemini Pro) für komplexe Synthesen.
    """
    LOCAL_ROUTINE = "local_routine"      # Ollama: qwen2.5-coder, mistral (Zero-Token, Schnell)
    CLOUD_FAST = "cloud_fast"            # Gemini 2.5/3.5 Flash / GPT-4o-mini
    CLOUD_REASONING = "cloud_reasoning"  # Claude 3.5 Sonnet / Gemini 2.5/1.5 Pro


class AgentRole(str, Enum):
    """Rollen-Definition der Triumvirat-Akteure zur differenzierten Modellauswahl.

    Attributes:
        JARVIS: System- und Host-Executor (Priorität: Local First, Shell Tools, minimale CPU-Last).
        FRIDAY: Meta-kognitive Wissens-Managerin (Priorität: Reasoning, Wissensgraphen & Synthese).
    """
    JARVIS = "jarvis"   # System- & Ops-Executor (Priorität: Local First / Shell Tools)
    FRIDAY = "friday"   # Meta-Kognitive Wissens-Managerin (Priorität: Reasoning & Graph)


@dataclass
class LLMMessage:
    """Repräsentiert eine standardisierte Chat-Nachricht für Multi-Provider-Aufrufe.

    Attributes:
        role (str): Die Rolle des Absenders ('system', 'user', 'assistant', 'tool').
        content (str): Textueller Inhalt der Nachricht.
        name (Optional[str]): Optionaler Name des Autors oder Tool-Namens.
        tool_call_id (Optional[str]): Eindeutige ID bei Tool-Rückmeldungen.
        tool_calls (Optional[List[Dict[str, Any]]]): Vom Modell initiierte Tool-Calls.
    """
    role: str
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


@dataclass
class LLMResponse:
    """Standardisierte Modell-Antwort über alle LLM-Adapter hinweg.

    Attributes:
        content (str): Vom Modell generierter Text.
        provider (str): Name des antwortenden Providers ('ollama', 'gemini', 'anthropic').
        model (str): Spezifische Modellbezeichnung (z. B. 'qwen2.5-coder:latest').
        tool_calls (List[Dict[str, Any]]): Extrahierte strukturierte Tool-Calls.
        raw_usage (Dict[str, Any]): Token- und Latenzmetriken des Providers.
    """
    content: str
    provider: str
    model: str
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    raw_usage: Dict[str, Any] = field(default_factory=dict)


class BaseLLMAdapter(ABC):
    """Abstrakte Basisklasse für alle Multi-LLM Provider-Adapter.

    Attributes:
        model_name (str): Kennung des Zielmodells.
        api_key (Optional[str]): Authentifizierungsschlüssel.
        base_url (Optional[str]): Basis-URL des Endpunkts.
    """

    def __init__(
        self,
        model_name: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ) -> None:
        """Initialisiert den Provider-Adapter.

        Args:
            model_name (str): Modellname des Zielanbieters.
            api_key (Optional[str]): API-Key zur Authentifizierung. Standard ist None.
            base_url (Optional[str]): Basis-URL der API. Standard ist None.
        """
        self.model_name: str = model_name
        self.api_key: Optional[str] = api_key
        self.base_url: Optional[str] = base_url

    @abstractmethod
    async def chat(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2
    ) -> LLMResponse:
        """Führt einen asynchronen Chat-Vervollständigungsaufruf durch.

        Args:
            messages (List[LLMMessage]): Historie der Konversationsnachrichten.
            tools (Optional[List[Dict[str, Any]]]): Schemata verfügbarer Tools/Funktionen.
            temperature (float): Sampling-Temperatur (Standard: 0.2 für deterministische Logik).

        Returns:
            LLMResponse: Die standardisierte Antwort des Modells.

        Raises:
            Exception: Wenn der Provider nicht antwortet oder ein Protokollfehler auftritt.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Prüft die Verfügbarkeit des Providers (Konnektivität, API-Key, Daemon).

        Returns:
            bool: True, falls der Provider aufrufbar ist, andernfalls False.
        """
        pass


class OllamaAdapter(BaseLLMAdapter):
    """Lokaler Adapter für Zero-Token Offline Operations via Ollama REST API."""

    def __init__(
        self,
        model_name: str = "qwen2.5-coder:latest",
        base_url: Optional[str] = None
    ) -> None:
        """Initialisiert den Ollama-Adapter.

        Args:
            model_name (str): Lokaler Modellname (Standard: 'qwen2.5-coder:latest').
            base_url (Optional[str]): Ollama HTTP-Basis-URL (Standard: Umgebungsvariable OLLAMA_BASE_URL oder http://127.0.0.1:11434).
        """
        url = base_url or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        super().__init__(model_name=model_name, base_url=url)

    def is_available(self) -> bool:
        """Prüft, ob der lokale Ollama-Daemon erreichbar ist.

        Returns:
            bool: True, falls Ollama mit HTTP 200 auf /api/tags antwortet, sonst False.
        """
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                return resp.status == 200
        except (urllib.error.URLError, OSError, Exception) as exc:
            logger.debug("[OllamaAdapter] Health-Check fehlgeschlagen (offline): %s", exc)
            return False

    async def chat(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2
    ) -> LLMResponse:
        """Führt einen asynchronen Chat-Aufruf über den Hintergrund-Threadpool aus.

        Args:
            messages (List[LLMMessage]): Liste der Konversationsnachrichten.
            tools (Optional[List[Dict[str, Any]]]): Optionale Funktions-/Tooldefinitionen.
            temperature (float): Kreativitäts-Parameter (Standard: 0.2).

        Returns:
            LLMResponse: Generierte Antwort und Tool-Aufrufe.

        Raises:
            RuntimeError: Wenn der lokale Ollama-Server einen HTTP-Fehler oder Verbindungsabbruch meldet.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._sync_chat, messages, tools, temperature)

    def _sync_chat(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]],
        temperature: float
    ) -> LLMResponse:
        """Synchroner HTTP-POST-Worker für die Ollama REST-API.

        Args:
            messages (List[LLMMessage]): Konversationsverlauf.
            tools (Optional[List[Dict[str, Any]]]): Tool-Definitionen.
            temperature (float): Modell-Temperatur.

        Returns:
            LLMResponse: Formatierte Modellantwort.

        Raises:
            RuntimeError: Bei HTTP-Fehlern, Netzwerkabbrüchen oder ungültigem JSON.
        """
        payload: Dict[str, Any] = {
            "model": self.model_name,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {"temperature": temperature}
        }
        if tools:
            payload["tools"] = tools

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=45.0) as resp:
                body = resp.read().decode("utf-8")
                res = json.loads(body)
                msg = res.get("message", {})
                tool_calls = msg.get("tool_calls", [])
                formatted_tools: List[Dict[str, Any]] = []
                for tc in tool_calls:
                    formatted_tools.append({
                        "id": tc.get("id", f"call_{os.urandom(4).hex()}"),
                        "name": tc.get("function", {}).get("name"),
                        "arguments": tc.get("function", {}).get("arguments", {})
                    })
                return LLMResponse(
                    content=msg.get("content", ""),
                    provider="ollama",
                    model=self.model_name,
                    tool_calls=formatted_tools,
                    raw_usage={"prompt_eval_count": res.get("prompt_eval_count", 0)}
                )
        except urllib.error.HTTPError as he:
            err_msg = f"Ollama HTTP-Fehler {he.code}: {he.reason}"
            logger.error("[OllamaAdapter] %s", err_msg)
            raise RuntimeError(err_msg) from he
        except (urllib.error.URLError, json.JSONDecodeError, OSError) as exc:
            logger.error("[OllamaAdapter] Verbindungs-/Parsing-Fehler: %s", exc)
            raise RuntimeError(f"Ollama Anfrage fehlgeschlagen: {exc}") from exc


class GeminiAdapter(BaseLLMAdapter):
    """Google Gemini Adapter für Cloud Multimodal & High-Speed Reasoning."""

    def __init__(
        self,
        model_name: str = "gemini-2.5-flash",
        api_key: Optional[str] = None
    ) -> None:
        """Initialisiert den Gemini-Adapter.

        Args:
            model_name (str): Gemini-Modellkennung (Standard: 'gemini-2.5-flash').
            api_key (Optional[str]): Google API-Key (Standard: GEMINI_API_KEY).
        """
        key = api_key or os.getenv("GEMINI_API_KEY", "")
        super().__init__(model_name=model_name, api_key=key)

    def is_available(self) -> bool:
        """Prüft das Vorhandensein eines gültig formatierten Google API-Keys.

        Returns:
            bool: True, falls ein Key konfiguriert ist, sonst False.
        """
        return bool(self.api_key and len(self.api_key) > 5)

    async def chat(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2
    ) -> LLMResponse:
        """Führt einen asynchronen Aufruf an die Google GenAI SDK aus.

        Args:
            messages (List[LLMMessage]): Konversationsverlauf.
            tools (Optional[List[Dict[str, Any]]]): Optionale Tools.
            temperature (float): Temperaturwert.

        Returns:
            LLMResponse: Modellantwort.

        Raises:
            RuntimeError: Bei SDK-Import- oder API-Kommunikationsfehlern.
        """
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            contents: List[Any] = []
            for m in messages:
                role = "user" if m.role in ("user", "system") else "model"
                contents.append(types.Content(role=role, parts=[types.Part.from_text(text=m.content)]))

            config = types.GenerateContentConfig(temperature=temperature)
            resp = await asyncio.to_thread(
                client.models.generate_content,
                model=self.model_name,
                contents=contents,
                config=config
            )
            return LLMResponse(
                content=resp.text or "",
                provider="gemini",
                model=self.model_name,
                tool_calls=[]
            )
        except ImportError as imp_err:
            logger.error("[GeminiAdapter] 'google-genai' Bibliothek ist nicht installiert: %s", imp_err)
            raise RuntimeError("Gemini SDK (google-genai) fehlt im Python Environment.") from imp_err
        except Exception as exc:
            logger.error("[GeminiAdapter] API-Fehler: %s", exc, exc_info=True)
            raise RuntimeError(f"Gemini API-Aufruf fehlgeschlagen: {exc}") from exc


class AnthropicAdapter(BaseLLMAdapter):
    """Anthropic Claude Adapter für anspruchsvolles Reasoning & Deep Analysis."""

    def __init__(
        self,
        model_name: str = "claude-3-5-sonnet-20241022",
        api_key: Optional[str] = None
    ) -> None:
        """Initialisiert den Claude-Adapter.

        Args:
            model_name (str): Modellkennung (Standard: 'claude-3-5-sonnet-20241022').
            api_key (Optional[str]): Anthropic API-Key (Standard: ANTHROPIC_API_KEY).
        """
        key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        super().__init__(model_name=model_name, api_key=key)

    def is_available(self) -> bool:
        """Prüft das Vorhandensein des Anthropic API-Keys.

        Returns:
            bool: True, falls konfiguriert, sonst False.
        """
        return bool(self.api_key and len(self.api_key) > 10)

    async def chat(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2
    ) -> LLMResponse:
        """Führt einen REST-Aufruf an die Anthropic Messages API aus.

        Args:
            messages (List[LLMMessage]): Konversationsverlauf.
            tools (Optional[List[Dict[str, Any]]]): Tool-Definitionen im Anthropic-Schema.
            temperature (float): Sampling-Temperatur.

        Returns:
            LLMResponse: Generierte Antwort und Tool-Aufrufe.

        Raises:
            RuntimeError: Bei HTTP-Fehlern oder Verbindungsabbrüchen.
        """
        headers = {
            "x-api-key": self.api_key or "",
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        system_prompt = ""
        user_msgs: List[Dict[str, str]] = []
        for m in messages:
            if m.role == "system":
                system_prompt += f"{m.content}\n"
            else:
                user_msgs.append({"role": m.role, "content": m.content})

        payload: Dict[str, Any] = {
            "model": self.model_name,
            "max_tokens": 4096,
            "messages": user_msgs,
            "temperature": temperature
        }
        if system_prompt:
            payload["system"] = system_prompt.strip()
        if tools:
            payload["tools"] = tools

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=data,
            headers=headers,
            method="POST"
        )

        def _do_call() -> Dict[str, Any]:
            with urllib.request.urlopen(req, timeout=60.0) as resp:
                return json.loads(resp.read().decode("utf-8"))

        try:
            res = await asyncio.to_thread(_do_call)
            content_text = ""
            tool_calls: List[Dict[str, Any]] = []
            for block in res.get("content", []):
                if block.get("type") == "text":
                    content_text += block.get("text", "")
                elif block.get("type") == "tool_use":
                    tool_calls.append({
                        "id": block.get("id"),
                        "name": block.get("name"),
                        "arguments": block.get("input", {})
                    })

            return LLMResponse(
                content=content_text,
                provider="anthropic",
                model=self.model_name,
                tool_calls=tool_calls,
                raw_usage=res.get("usage", {})
            )
        except urllib.error.HTTPError as he:
            logger.error("[AnthropicAdapter] HTTP-Fehler %d: %s", he.code, he.reason)
            raise RuntimeError(f"Anthropic API-Fehler {he.code}: {he.reason}") from he
        except Exception as exc:
            logger.error("[AnthropicAdapter] Unerwarteter Kommunikationsfehler: %s", exc, exc_info=True)
            raise RuntimeError(f"Anthropic Aufruf fehlgeschlagen: {exc}") from exc


class LLMRouter:
    """Zentraler Router mit rollen- und bedarfsorientierter 3-Tier Modellauswahl sowie Auto-Fallback und Quota-Protection."""

    def __init__(self, daily_quota_limit: int = 1_000_000) -> None:
        """Initialisiert den LLMRouter mit Standard-Adaptern und Quota-Grenzen.

        Args:
            daily_quota_limit (int): Maximales Tageskontingent in Tokens (Standard: 1.000.000).
        """
        self.daily_quota_limit: int = daily_quota_limit
        self.daily_token_usage: int = 0
        self.adapters: Dict[str, BaseLLMAdapter] = {
            "ollama_coder": OllamaAdapter(model_name="qwen2.5-coder:latest"),
            "ollama_general": OllamaAdapter(model_name="mistral:latest"),
            "gemini_flash": GeminiAdapter(model_name="gemini-3.5-flash"),
            "gemini_pro": GeminiAdapter(model_name="gemini-1.5-pro"),
            "claude_sonnet": AnthropicAdapter(model_name="claude-3-5-sonnet-20241022"),
        }

    def calculate_complexity_score(self, messages: List[LLMMessage]) -> float:
        """Berechnet den Komplexitäts-Score (0.0 bis 1.0) für intelligentes 3-Tier Routing.

        Heuristik-Regeln:
        - Score <= 0.35: Tier 1 (Routine, Fast-Path, minimale CPU/Token-Kosten)
        - Score 0.35 - 0.80: Tier 2 (Standard Chat & HUD, z. B. Gemini Flash)
        - Score > 0.80: Tier 3 (Deep-Reasoning & Meta-Synthese, Claude / Gemini Pro)

        Args:
            messages (List[LLMMessage]): Aktuelle Konversation zur Analyse.

        Returns:
            float: Normalisierter Komplexitäts-Score zwischen 0.0 und 1.0.
        """
        if not messages:
            return 0.15

        total_text = " ".join([m.content for m in messages if m.content]).lower()
        word_count = len(total_text.split())

        routine_keywords = ["ping", "status", "zeit", "format", "json", "echo", "check"]
        deep_keywords = [
            "architektur", "refactor", "blueprint", "deep dive", "kernel", "debatte",
            "konsens", "sicherheitsmatrix", "speicherhierarchie", "lancedb", "vektor",
            "synthese", "post-mortem", "root cause", "heuristik", "analyse", "komplex"
        ]
        hits = sum(1 for kw in deep_keywords if kw in total_text)

        # Wenn reine Routine ohne Deep Keywords und sehr kurz
        if any(rk in total_text for rk in routine_keywords) and hits == 0 and word_count < 25:
            return 0.15

        # Basis für normale Dialoge und Fragen
        score = 0.50

        # Längen-Faktor
        if word_count > 300:
            score += 0.25
        elif word_count > 100:
            score += 0.15

        # Deep Keywords Gewichtung
        score += min(0.45, hits * 0.10)

        return min(1.0, round(score, 2))

    def route_by_complexity(
        self,
        messages: List[LLMMessage],
        role: AgentRole = AgentRole.FRIDAY
    ) -> ModelTier:
        """Bestimmt das optimale Modell-Tier basierend auf Heuristik und Hardware-Schonung.

        Args:
            messages (List[LLMMessage]): Konversationsnachrichten.
            role (AgentRole): Rolle des anfragenden Agenten (Standard: FRIDAY).

        Returns:
            ModelTier: Ziel-Tier (LOCAL_ROUTINE, CLOUD_FAST oder CLOUD_REASONING).
        """
        score = self.calculate_complexity_score(messages)
        if score <= 0.35:
            return ModelTier.LOCAL_ROUTINE
        elif score <= 0.80:
            return ModelTier.CLOUD_FAST
        else:
            return ModelTier.CLOUD_REASONING

    def select_adapter(self, role: AgentRole, tier: ModelTier) -> BaseLLMAdapter:
        """Wählt den passenden und verfügbaren Adapter unter Beachtung der Quota-Schutzmatrix.

        Args:
            role (AgentRole): Rolle des Agenten (JARVIS oder FRIDAY).
            tier (ModelTier): Angefordertes Modell-Tier.

        Returns:
            BaseLLMAdapter: Der zu verwendende LLM-Adapter.

        Raises:
            RuntimeError: Wenn kein einziger LLM-Provider erreichbar oder konfiguriert ist.
        """
        # Quota Protection Guard: Bei > 85% Budget-Auslastung Downgrade auf Flash
        if self.daily_token_usage > (self.daily_quota_limit * 0.85) and tier == ModelTier.CLOUD_REASONING:
            logger.warning("[QUOTA GUARD] Tageslimit zu >85%% erreicht. Downgrade von Cloud Reasoning auf Gemini Flash.")
            tier = ModelTier.CLOUD_FAST

        # Friday bevorzugt Reasoning (Claude / Gemini Pro), mit Fallback auf Flash und lokales SLM
        if role == AgentRole.FRIDAY:
            if tier == ModelTier.CLOUD_REASONING:
                if self.adapters["claude_sonnet"].is_available():
                    return self.adapters["claude_sonnet"]
                if self.adapters["gemini_pro"].is_available():
                    return self.adapters["gemini_pro"]
            if self.adapters["gemini_flash"].is_available():
                return self.adapters["gemini_flash"]
            if self.adapters["ollama_general"].is_available():
                return self.adapters["ollama_general"]

        # Jarvis bevorzugt Fast-Path (lokal oder Flash) zur Schonung der Host-Kerne
        if role == AgentRole.JARVIS:
            if tier == ModelTier.LOCAL_ROUTINE:
                if self.adapters["ollama_coder"].is_available():
                    return self.adapters["ollama_coder"]
                if self.adapters["gemini_flash"].is_available():
                    return self.adapters["gemini_flash"]
            if self.adapters["gemini_flash"].is_available():
                return self.adapters["gemini_flash"]

        # Globaler Standard-Fallback
        for key in ["gemini_flash", "gemini_pro", "ollama_coder", "ollama_general"]:
            adapter = self.adapters.get(key)
            if adapter and adapter.is_available():
                return adapter

        logger.critical("[LLMRouter] Keinerlei LLM-Adapter verfügbar!")
        raise RuntimeError("Kein LLM-Provider erreichbar!")

    async def execute(
        self,
        role: AgentRole,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        desired_tier: Optional[ModelTier] = None
    ) -> LLMResponse:
        """Führt den Routing- und Aufruf-Zyklus mit automatischem Fallback-Schutz aus.

        Args:
            role (AgentRole): Rolle des initiierenden Agenten.
            messages (List[LLMMessage]): Konversationsverlauf.
            tools (Optional[List[Dict[str, Any]]]): Optionale Tools.
            desired_tier (Optional[ModelTier]): Manuell erzwungene Modellstufe (optional).

        Returns:
            LLMResponse: Erfolgreich generierte Modellantwort.

        Raises:
            Exception: Falls sowohl der primäre Adapter als auch der Fallback-Adapter fehlschlagen.
        """
        tier = desired_tier if desired_tier is not None else self.route_by_complexity(messages, role)
        adapter = self.select_adapter(role, tier)

        try:
            logger.info("Route Task für [%s] via [%s] (%s) | Tier: %s",
                        role.value, adapter.__class__.__name__, adapter.model_name, tier.value)
            resp = await adapter.chat(messages, tools=tools)

            # Token Usage erfassen
            usage_tokens = resp.raw_usage.get("total_tokens", resp.raw_usage.get("total_token_count", 250))
            self.daily_token_usage += usage_tokens
            return resp
        except Exception as exc:
            logger.warning("Primärer Adapter [%s] fehlgeschlagen: %s. Aktiviere Notfall-Fallback auf Gemini Flash...",
                           adapter.__class__.__name__, exc)
            fallback = self.adapters["gemini_flash"]
            if fallback.is_available() and fallback != adapter:
                try:
                    return await fallback.chat(messages, tools=tools)
                except Exception as fb_exc:
                    logger.error("Auch Notfall-Fallback auf Gemini Flash fehlgeschlagen: %s", fb_exc, exc_info=True)
                    raise fb_exc
            raise exc
