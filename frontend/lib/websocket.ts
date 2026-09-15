import { AssistantState, ConfirmRequest, LogMessage, TelemetryData, GraphData, MCPServerMap, MCPServerConfig } from "./types";

type Listener<T> = (data: T) => void;

class JarvisSocketManager {
  private ws: WebSocket | null = null;
  private url: string = "ws://127.0.0.1:8765";
  private reconnectInterval: number = 3000;
  private shouldReconnect: boolean = true;

  // Event Listeners (Reines Steuerungs- & Telemetrie-HUD — KEINE lokale Web-Audio-Pipeline)
  private stateListeners: Set<Listener<AssistantState>> = new Set();
  private logListeners: Set<Listener<LogMessage>> = new Set();
  private telemetryListeners: Set<Listener<TelemetryData>> = new Set();
  private audioLevelListeners: Set<Listener<number>> = new Set();
  private confirmListeners: Set<Listener<ConfirmRequest | null>> = new Set();
  private muteListeners: Set<Listener<boolean>> = new Set();
  private apiKeyListeners: Set<Listener<{ configured: boolean; masked_key: string }>> = new Set();
  private graphListeners: Set<Listener<GraphData>> = new Set();
  private mcpListeners: Set<Listener<MCPServerMap>> = new Set();

  public currentState: AssistantState = "OFFLINE";
  public isMuted: boolean = false;
  public pendingConfirm: ConfirmRequest | null = null;
  public apiKeyStatus: { configured: boolean; masked_key: string } = { configured: false, masked_key: "" };
  public currentGraphData: GraphData | null = null;
  public currentMcpServers: MCPServerMap = {};

  constructor() {
    // Browser ist ein reines Kontroll- und Visualisierungs-HUD. Kein AudioContext erforderlich.
  }

  public init(url?: string) {
    if (url) this.url = url;
    this.connect();
  }

  private connect() {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    try {
      this.setState("CONNECTING");
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        this.setState("ONLINE");
        this.notifyLog({
          speaker: "SYS",
          text: "WebSocket-Verbindung zum Jarvis Backend hergestellt.",
          ts: new Date().toLocaleTimeString()
        });
      };

      this.ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          this.handleMessage(msg);
        } catch (e) {
          console.error("WS Parse Fehler:", e);
        }
      };

      this.ws.onclose = () => {
        this.setState("OFFLINE");
        if (this.shouldReconnect) {
          setTimeout(() => this.connect(), this.reconnectInterval);
        }
      };

      this.ws.onerror = () => {
        this.setState("ERROR");
      };
    } catch (e) {
      this.setState("ERROR");
      if (this.shouldReconnect) {
        setTimeout(() => this.connect(), this.reconnectInterval);
      }
    }
  }

  private handleMessage(msg: any) {
    switch (msg.type) {
      case "init":
        if (msg.api_key_status) {
          this.apiKeyStatus = msg.api_key_status;
          this.apiKeyListeners.forEach((fn) => fn(this.apiKeyStatus));
        }
        if (msg.graph_data) {
          this.currentGraphData = msg.graph_data;
          this.graphListeners.forEach((fn) => fn(msg.graph_data));
        }
        if (msg.state) this.setState(msg.state);
        if (msg.is_muted !== undefined) {
          this.isMuted = !!msg.is_muted;
          this.muteListeners.forEach((fn) => fn(this.isMuted));
        }
        if (msg.pending_confirm) {
          const pc = msg.pending_confirm;
          this.pendingConfirm = {
            action: pc.action || pc.key || "shutdown",
            key: pc.key || pc.action || "shutdown",
            label: pc.label || pc.title || "Systemaktion",
            title: pc.title || pc.label || "Systemaktion",
            detail: pc.detail || "Bestätigung auf dem Hardware-Gate erforderlich.",
            timeout: typeof pc.timeout === "number" ? pc.timeout : 90
          };
          this.confirmListeners.forEach((fn) => fn(this.pendingConfirm));
        }
        if (msg.mcp_servers) {
          this.currentMcpServers = msg.mcp_servers;
          this.mcpListeners.forEach((fn) => fn(this.currentMcpServers));
        }
        break;

      case "mcp_servers_data":
        if (msg.servers) {
          this.currentMcpServers = msg.servers;
          this.mcpListeners.forEach((fn) => fn(this.currentMcpServers));
        }
        break;

      case "api_key_status":
        this.apiKeyStatus = {
          configured: !!msg.configured,
          masked_key: msg.masked_key || ""
        };
        this.apiKeyListeners.forEach((fn) => fn(this.apiKeyStatus));
        break;

      case "state":
        if (msg.state) this.setState(msg.state);
        break;

      case "log":
        this.notifyLog({
          speaker: msg.speaker || "SYS",
          text: msg.text || "",
          ts: msg.ts || new Date().toLocaleTimeString()
        });
        break;

      case "telemetry":
        if (msg.data) {
          this.telemetryListeners.forEach((fn) => fn(msg.data));
        }
        break;

      // Telemetrie- und RMS-Pegeldaten für die Arc-Reactor-Animation im HUD
      case "audio_rms":
      case "audio_level":
        if (typeof msg.level === "number") {
          this.audioLevelListeners.forEach((fn) => fn(msg.level));
        }
        break;

      case "graph_update":
      case "graph_sync":
        if (msg.data) {
          this.currentGraphData = msg.data;
          this.graphListeners.forEach((fn) => fn(msg.data));
        }
        break;

      case "confirm_request":
        console.log("[WS] Safety Gate confirm_request empfangen:", msg);
        this.pendingConfirm = {
          action: msg.action || msg.key || "shutdown",
          key: msg.key || msg.action || "shutdown",
          label: msg.label || msg.title || "Systemaktion",
          title: msg.title || msg.label || "Systemaktion",
          detail: msg.detail || "Bestätigung auf dem Hardware-Gate erforderlich.",
          timeout: typeof msg.timeout === "number" ? msg.timeout : 90
        };
        this.confirmListeners.forEach((fn) => fn(this.pendingConfirm));
        break;

      case "confirm_hide":
      case "confirm_resolved":
        console.log("[WS] Safety Gate ausgeblendet / aufgelöst:", msg);
        this.pendingConfirm = null;
        this.confirmListeners.forEach((fn) => fn(null));
        break;

      case "mute_state":
        this.isMuted = !!msg.muted;
        this.muteListeners.forEach((fn) => fn(this.isMuted));
        break;

      // Browser-Audio-Wiedergabe deaktiviert (Backend steuert Audio via PipeWire/SoundDevice)
      case "audio_chunk":
        break;
    }
  }

  private setState(state: AssistantState) {
    this.currentState = state;
    this.stateListeners.forEach((fn) => fn(state));
  }

  private notifyLog(log: LogMessage) {
    this.logListeners.forEach((fn) => fn(log));
  }

  // --- Public API ---
  public sendText(text: string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: "text_command", text }));
    }
  }

  public interrupt() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: "interrupt" }));
    }
  }

  /**
   * Sendet ein Steuersignal an das Python-Backend zum Aktivieren/Deaktivieren des Mikrofons.
   * Der Browser öffnet selbst KEIN lokales Mikrofon (kein getUserMedia).
   */
  public toggleMic(active?: boolean) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const targetActive = typeof active === "boolean" ? active : this.isMuted;
      this.ws.send(JSON.stringify({ type: "toggle_mic", active: targetActive }));
    }
  }

  public toggleMute() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: "mute_toggle" }));
    }
  }

  public resolveConfirm(accepted: boolean) {
    this.pendingConfirm = null;
    this.confirmListeners.forEach((fn) => fn(null));
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: "confirm_resolve", accepted }));
    }
  }

  public triggerUndo() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: "undo" }));
    }
  }

  public triggerTool(tool: string, params: Record<string, any> = {}) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: "trigger_tool", tool, params }));
    }
  }

  public setApiKey(key: string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: "set_api_key", key }));
    }
  }

  public getApiKeyStatus() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: "get_api_key_status" }));
    }
  }

  // Subscriptions
  public onApiKeyStatus(fn: Listener<{ configured: boolean; masked_key: string }>) {
    this.apiKeyListeners.add(fn);
    fn(this.apiKeyStatus);
    return () => {
      this.apiKeyListeners.delete(fn);
    };
  }

  public onState(fn: Listener<AssistantState>) {
    this.stateListeners.add(fn);
    fn(this.currentState);
    return () => {
      this.stateListeners.delete(fn);
    };
  }

  public onLog(fn: Listener<LogMessage>) {
    this.logListeners.add(fn);
    return () => {
      this.logListeners.delete(fn);
    };
  }

  public onTelemetry(fn: Listener<TelemetryData>) {
    this.telemetryListeners.add(fn);
    return () => {
      this.telemetryListeners.delete(fn);
    };
  }

  public onAudioLevel(fn: Listener<number>) {
    this.audioLevelListeners.add(fn);
    return () => {
      this.audioLevelListeners.delete(fn);
    };
  }

  public onConfirm(fn: Listener<ConfirmRequest | null>) {
    this.confirmListeners.add(fn);
    fn(this.pendingConfirm);
    return () => {
      this.confirmListeners.delete(fn);
    };
  }

  public onMute(fn: Listener<boolean>) {
    this.muteListeners.add(fn);
    fn(this.isMuted);
    return () => {
      this.muteListeners.delete(fn);
    };
  }

  // --- 3D Graph & OS Cockpit Actions ---
  public executeNodeAction(
    nodeId: string,
    path?: string,
    category?: string,
    action: "open" | "terminal" | "summarize" | "delete" = "open"
  ) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: "execute_node_action",
        node_id: nodeId,
        path: path || "",
        category: category || "",
        action
      }));
    }
  }

  public deleteNode(nodeId: string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: "delete_node", node_id: nodeId }));
    }
  }

  public addNode(
    title: string,
    category: string,
    content: string = "",
    linkedTo: string = "",
    path: string = ""
  ) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: "add_node",
        title,
        category,
        content,
        linked_to: linkedTo,
        path
      }));
    }
  }

  public requestGraphSync() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: "get_graph" }));
    }
  }

  public onGraphUpdate(fn: Listener<GraphData>) {
    this.graphListeners.add(fn);
    if (this.currentGraphData) fn(this.currentGraphData);
    return () => {
      this.graphListeners.delete(fn);
    };
  }

  public onMcpServers(fn: Listener<MCPServerMap>) {
    this.mcpListeners.add(fn);
    if (Object.keys(this.currentMcpServers).length > 0) fn(this.currentMcpServers);
    return () => {
      this.mcpListeners.delete(fn);
    };
  }

  public requestMcpServers() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: "get_mcp_servers" }));
    }
  }

  public toggleMcpServer(id: string, enabled: boolean) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: "toggle_mcp_server", id, enabled }));
    }
  }

  public saveMcpServer(id: string, config: MCPServerConfig) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: "save_mcp_server", id, config }));
    }
  }

  public deleteMcpServer(id: string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: "delete_mcp_server", id }));
    }
  }
}

export const socketManager = new JarvisSocketManager();

