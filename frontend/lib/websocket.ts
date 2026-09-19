import { 
  AssistantState, 
  ConfirmRequest, 
  LogMessage, 
  DevLogEntry,
  TelemetryData, 
  GraphData, 
  MCPServerMap, 
  MCPServerConfig,
  PersonalityConfig,
  BrainExportResult,
  BrainImportResult,
  CalendarEvent
} from "./types";
import { auditor } from "../utils/auditLogger";

type Listener<T> = (data: T) => void;

class JarvisSocketManager {
  private ws: WebSocket | null = null;
  private url: string = "ws://127.0.0.1:8765";
  private baseReconnectDelay: number = 1000;
  private maxReconnectDelay: number = 15000;
  private reconnectAttempts: number = 0;
  private reconnectTimer: any = null;
  private shouldReconnect: boolean = true;

  // Event Listeners
  private stateListeners: Set<Listener<AssistantState>> = new Set();
  private logListeners: Set<Listener<LogMessage>> = new Set();
  private devLogListeners: Set<Listener<DevLogEntry>> = new Set();
  private telemetryListeners: Set<Listener<TelemetryData>> = new Set();
  private audioLevelListeners: Set<Listener<number>> = new Set();
  private confirmListeners: Set<Listener<ConfirmRequest | null>> = new Set();
  private muteListeners: Set<Listener<boolean>> = new Set();
  private paranoiaMuteListeners: Set<Listener<boolean>> = new Set();
  private focusModeListeners: Set<Listener<boolean>> = new Set();
  private apiKeyListeners: Set<Listener<{ configured: boolean; masked_key: string }>> = new Set();
  private graphListeners: Set<Listener<GraphData>> = new Set();
  private mcpListeners: Set<Listener<MCPServerMap>> = new Set();
  private brainExportListeners: Set<Listener<BrainExportResult>> = new Set();
  private brainImportListeners: Set<Listener<BrainImportResult>> = new Set();
  private personalityListeners: Set<Listener<PersonalityConfig>> = new Set();
  private calendarListeners: Set<Listener<CalendarEvent[]>> = new Set();
  private autoBriefingListeners: Set<Listener<boolean>> = new Set();
  private aiNameListeners: Set<Listener<string>> = new Set();

  public currentState: AssistantState = "OFFLINE";
  public currentAiName: string = "Cypher";
  public isMuted: boolean = false;
  public isParanoiaMuted: boolean = false;
  public isFocusMode: boolean = false;
  public isAutoBriefing: boolean = true;
  public currentCalendarEvents: CalendarEvent[] = [];
  public pendingConfirm: ConfirmRequest | null = null;
  public apiKeyStatus: { configured: boolean; masked_key: string } = { configured: false, masked_key: "" };
  public currentGraphData: GraphData | null = null;
  public currentMcpServers: MCPServerMap = {};
  public currentPersonality: PersonalityConfig | null = null;

  constructor() {}

  public init(url?: string) {
    if (url) this.url = url;
    this.connect();
  }

  private scheduleReconnect() {
    if (this.reconnectTimer) return;
    const factor = Math.min(this.reconnectAttempts, 5);
    const delay = Math.min(this.maxReconnectDelay, this.baseReconnectDelay * Math.pow(1.8, factor));
    const jitter = Math.random() * 500;
    const totalDelay = Math.round(delay + jitter);
    this.reconnectAttempts++;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, totalDelay);
  }

  private connect() {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    try {
      this.setState("CONNECTING");
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        this.reconnectAttempts = 0;
        if (this.reconnectTimer) {
          clearTimeout(this.reconnectTimer);
          this.reconnectTimer = null;
        }
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
          this.scheduleReconnect();
        }
      };

      this.ws.onerror = () => {
        this.setState("ERROR");
      };
    } catch (e) {
      this.setState("ERROR");
      if (this.shouldReconnect) {
        this.scheduleReconnect();
      }
    }
  }

  private handleMessage(msg: any) {
    switch (msg.type) {
      case "init":
      case "SYSTEM_INIT":
        const initName = msg.ai_name || msg.data?.ai_name || msg.personality?.name || msg.data?.personality?.name;
        if (initName && typeof initName === "string") {
          this.currentAiName = initName;
          this.aiNameListeners.forEach((fn) => fn(this.currentAiName));
        }
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
        if (msg.paranoia_muted !== undefined) {
          this.isParanoiaMuted = !!msg.paranoia_muted;
          this.paranoiaMuteListeners.forEach((fn) => fn(this.isParanoiaMuted));
        }
        if (msg.focus_mode !== undefined) {
          this.isFocusMode = !!msg.focus_mode;
          this.focusModeListeners.forEach((fn) => fn(this.isFocusMode));
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
        if (msg.personality) {
          this.currentPersonality = msg.personality;
          this.personalityListeners.forEach((fn) => fn(this.currentPersonality!));
        }
        if (msg.calendar_events && Array.isArray(msg.calendar_events)) {
          this.currentCalendarEvents = msg.calendar_events;
          this.calendarListeners.forEach((fn) => fn(this.currentCalendarEvents));
        }
        if (msg.auto_briefing !== undefined) {
          this.isAutoBriefing = !!msg.auto_briefing;
          this.autoBriefingListeners.forEach((fn) => fn(this.isAutoBriefing));
        }
        break;

      case "dev_log":
        if (msg.entry) {
          this.devLogListeners.forEach((fn) => fn(msg.entry));
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

      case "audio_rms":
      case "audio_level":
      case "AUDIO_RMS":
        const rawLevel = typeof msg.level === "number" ? msg.level : (typeof msg.value === "number" ? msg.value : null);
        if (rawLevel !== null) {
          this.audioLevelListeners.forEach((fn) => fn(rawLevel));
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
        this.pendingConfirm = null;
        this.confirmListeners.forEach((fn) => fn(null));
        break;

      case "ACTION_RECEIPT":
      case "action_receipt":
        if (msg.correlationId) {
          auditor.handleBackendAck({
            correlationId: msg.correlationId,
            status: msg.status || "PROCESSED",
            result: msg.result
          });
        }
        break;

      case "mute_state":
      case "mute_status":
        this.isMuted = !!msg.muted;
        this.muteListeners.forEach((fn) => fn(this.isMuted));
        break;

      case "paranoia_mute_state":
      case "paranoia_mute_status":
        this.isParanoiaMuted = msg.active !== undefined ? !!msg.active : !!msg.muted;
        this.paranoiaMuteListeners.forEach((fn) => fn(this.isParanoiaMuted));
        break;

      case "focus_mode_state":
      case "focus_mode_status":
        this.isFocusMode = !!msg.enabled;
        this.focusModeListeners.forEach((fn) => fn(this.isFocusMode));
        break;

      case "brain_export_result":
        this.brainExportListeners.forEach((fn) => fn({
          success: !!msg.success,
          path: msg.path,
          error: msg.error
        }));
        break;

      case "brain_import_result":
        this.brainImportListeners.forEach((fn) => fn({
          success: !!msg.success,
          error: msg.error
        }));
        break;

      case "personality_data":
      case "personality_saved":
        if (msg.personality) {
          this.currentPersonality = msg.personality;
          this.personalityListeners.forEach((fn) => fn(this.currentPersonality!));
          if (msg.personality.name) {
            this.currentAiName = msg.personality.name;
            this.aiNameListeners.forEach((fn) => fn(this.currentAiName));
          }
        }
        if (msg.ai_name) {
          this.currentAiName = msg.ai_name;
          this.aiNameListeners.forEach((fn) => fn(this.currentAiName));
        }
        break;

      case "calendar_events_data":
      case "CALENDAR_EVENTS_DATA":
        if (msg.events && Array.isArray(msg.events)) {
          this.currentCalendarEvents = msg.events;
          this.calendarListeners.forEach((fn) => fn(this.currentCalendarEvents));
        }
        break;

      case "CALENDAR_SYNC":
      case "calendar_sync":
        if (msg.events && Array.isArray(msg.events)) {
          this.currentCalendarEvents = msg.events;
          this.calendarListeners.forEach((fn) => fn(this.currentCalendarEvents));
        } else {
          this.requestCalendarEvents();
        }
        break;

      case "auto_briefing_state":
        if (msg.enabled !== undefined) {
          this.isAutoBriefing = !!msg.enabled;
          this.autoBriefingListeners.forEach((fn) => fn(this.isAutoBriefing));
        }
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

  public setParanoiaMute(muted: boolean) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: "set_paranoia_mute", muted }));
    }
  }

  public setFocusMode(enabled: boolean) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: "set_focus_mode", enabled }));
    }
  }

  public savePersonality(config: PersonalityConfig) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: "save_personality",
        ...config
      }));
    }
  }

  public exportBrain() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: "export_brain" }));
    }
  }

  public importBrain(path: string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: "import_brain", path }));
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

  public onDevLog(fn: Listener<DevLogEntry>) {
    this.devLogListeners.add(fn);
    return () => {
      this.devLogListeners.delete(fn);
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

  public onParanoiaMute(fn: Listener<boolean>) {
    this.paranoiaMuteListeners.add(fn);
    fn(this.isParanoiaMuted);
    return () => {
      this.paranoiaMuteListeners.delete(fn);
    };
  }

  public onFocusMode(fn: Listener<boolean>) {
    this.focusModeListeners.add(fn);
    fn(this.isFocusMode);
    return () => {
      this.focusModeListeners.delete(fn);
    };
  }

  public onBrainExport(fn: Listener<BrainExportResult>) {
    this.brainExportListeners.add(fn);
    return () => {
      this.brainExportListeners.delete(fn);
    };
  }

  public onBrainImport(fn: Listener<BrainImportResult>) {
    this.brainImportListeners.add(fn);
    return () => {
      this.brainImportListeners.delete(fn);
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

  public onPersonality(fn: Listener<PersonalityConfig>) {
    this.personalityListeners.add(fn);
    if (this.currentPersonality) fn(this.currentPersonality);
    return () => {
      this.personalityListeners.delete(fn);
    };
  }

  public onAiName(fn: Listener<string>) {
    this.aiNameListeners.add(fn);
    if (this.currentAiName) fn(this.currentAiName);
    return () => {
      this.aiNameListeners.delete(fn);
    };
  }

  public requestPersonality() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: "get_personality" }));
    }
  }

  // --- Calendar & Briefing Management ---
  public onCalendarEvents(fn: Listener<CalendarEvent[]>) {
    this.calendarListeners.add(fn);
    if (this.currentCalendarEvents.length > 0) fn(this.currentCalendarEvents);
    return () => {
      this.calendarListeners.delete(fn);
    };
  }

  public requestCalendarEvents() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: "get_calendar_events" }));
    }
  }

  public addCalendarEvent(event: {
    title: string;
    start_time: string;
    end_time?: string;
    description?: string;
    category?: string;
    reminder?: string;
    recurrence_rule?: string;
    reminder_strategy?: any;
  }) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: "add_calendar_event",
        ...event
      }));
    }
  }

  public deleteCalendarEvent(eventId: number | string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: "delete_calendar_event",
        event_id: eventId
      }));
    }
  }

  public dispatchAuditedAction(actionName: string, payload: any = {}): Promise<boolean> {
    return auditor.trackAction(actionName, payload, (data) => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify(data));
      }
    });
  }

  public onAutoBriefing(fn: Listener<boolean>) {
    this.autoBriefingListeners.add(fn);
    fn(this.isAutoBriefing);
    return () => {
      this.autoBriefingListeners.delete(fn);
    };
  }

  public setAutoBriefing(enabled: boolean) {
    this.isAutoBriefing = enabled;
    this.autoBriefingListeners.forEach((fn) => fn(this.isAutoBriefing));
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: "set_auto_briefing",
        enabled
      }));
    }
  }

  public triggerBriefingNow() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: "trigger_briefing" }));
    }
  }
}

export const socketManager = new JarvisSocketManager();
