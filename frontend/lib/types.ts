export type NodeCategory = 
  | "Router"
  | "Wiki"
  | "Concepts"
  | "Suites"
  | "Skills"
  | "Tools"
  | "Worlds"
  | "Notes"
  | "Files";

export interface GraphNode {
  id: string;
  name: string;
  category: NodeCategory;
  connections: number;
  description: string;
  path?: string;
  x?: number;
  y?: number;
  z?: number;
  vx?: number;
  vy?: number;
  vz?: number;
}

export interface GraphLink {
  source: string;
  target: string;
  value?: number;
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

export interface TelemetryData {
  cpu_percent: number;
  cpu_cores: number[];
  ram_percent: number;
  ram_used_gb: number;
  ram_total_gb: number;
  swap_percent: number;
  disk_percent: number;
  disk_free_gb: number;
  temperatures: Record<string, number>;
  gpu: string;
}

export interface LogMessage {
  speaker: "YOU" | "JARVIS" | "SYS" | "ERR";
  text: string;
  ts: string;
}

export interface DevLogEntry {
  speaker: string;
  text: string;
  ts: string;
}

export type AssistantState = 
  | "OFFLINE"
  | "CONNECTING"
  | "ONLINE"
  | "LISTENING"
  | "THINKING"
  | "SPEAKING"
  | "ERROR";

export interface ConfirmRequest {
  key?: string;
  action: string;
  title?: string;
  label: string;
  detail: string;
  timeout?: number;
}

export interface MCPServerConfig {
  command: string;
  args: string[];
  description?: string;
  category?: string;
  enabled: boolean;
  env?: Record<string, string>;
}

export type MCPServerMap = Record<string, MCPServerConfig>;

export interface PersonalityConfig {
  name: string;
  role: string;
  tone: string;
  domain: string;
  humor: string;
  boundaries: string;
  custom_prompt?: string;
  soul?: string;
  soul_text?: string;
}

export interface BrainExportResult {
  success: boolean;
  path?: string;
  error?: string;
}

export interface BrainImportResult {
  success: boolean;
  error?: string;
}

export interface CalendarEvent {
  id: number;
  title: string;
  description: string;
  start_time: string;
  end_time?: string;
  category: string;
  reminder_offset_minutes: number;
  is_completed: number;
  created_at: string;
}
