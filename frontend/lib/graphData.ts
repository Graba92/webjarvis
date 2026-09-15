import { GraphData, NodeCategory } from "./types";

export const CATEGORY_COLORS: Record<NodeCategory, string> = {
  // Gruppe 1: Cyan (Routing, Agent-Skills, System-Tools)
  Router: "#00f0ff",
  Skills: "#00f0ff",
  Tools: "#00f0ff",
  // Gruppe 2: Blau (Suites, Wissensdatenbank, Dateisystem)
  Suites: "#2979ff",
  Wiki: "#2979ff",
  Files: "#2979ff",
  // Gruppe 3: Orange (Konzepte, Simulationswelten, Notizen)
  Concepts: "#ff9100",
  Worlds: "#ff9100",
  Notes: "#ff9100"
};

export const INITIAL_GRAPH_DATA: GraphData = {
  nodes: [
    // Top Hubs
    {
      id: "hub-skill-suites",
      name: "Skill Suites",
      category: "Suites",
      connections: 236,
      description: "Zentraler Routing-Knoten aller autonomen Agenten-Skills, Automatisierungsroutinen und Tool-Pipelines.",
      path: "backend/actions"
    },
    {
      id: "hub-claude-code",
      name: "Claude Code",
      category: "Skills",
      connections: 48,
      description: "Terminal-Agent zur Code-Generierung, Refactoring und statischen AST-Synthese.",
      path: "claude"
    },
    {
      id: "hub-gemini-live",
      name: "Gemini Live API",
      category: "Router",
      connections: 112,
      description: "Vollduplex-Multimodal-Streaming-Core (gemini-3.1-flash-live-preview) mit 16/24-kHz-Audio.",
      path: "backend/core/gemini_live.py"
    },
    {
      id: "hub-ai-workshop",
      name: "AI Workshop OS",
      category: "Concepts",
      connections: 184,
      description: "Hauptarchitektur des hybriden Betriebssystems für CachyOS / Arch Linux.",
      path: "/home/graba/Schreibtisch/ASGRAD/GRABAS_GITHUB/eigenjarv/2"
    },
    {
      id: "hub-youtube-channel",
      name: "YouTube Channel",
      category: "Concepts",
      connections: 64,
      description: "Content-Pipeline, Videoskripte, Storyboards und Metadaten-Optimierung.",
      path: "https://youtube.com"
    },
    // Suites
    {
      id: "suite-finance",
      name: "Finance Suite",
      category: "Suites",
      connections: 32,
      description: "Abrechnungen, Rechnungs-Generierung und Stripe-Schnittstellen.",
      path: "backend/actions"
    },
    {
      id: "suite-seo",
      name: "SEO Suite",
      category: "Suites",
      connections: 28,
      description: "Suchmaschinenoptimierung, Keyword-Cluster und Content-Scoring.",
      path: "backend/actions"
    },
    {
      id: "suite-ads",
      name: "Ads Suite",
      category: "Suites",
      connections: 19,
      description: "Werbekampagnen-Steuerung und Performance-Tracking.",
      path: "backend/actions"
    },
    // Tools
    {
      id: "tool-vidiq",
      name: "vidIQ",
      category: "Tools",
      connections: 14,
      description: "YouTube-Trendanalyse und Keyword-Tracking.",
      path: "https://vidiq.com"
    },
    {
      id: "tool-higgsfield",
      name: "Higgsfield",
      category: "Tools",
      connections: 22,
      description: "KI-Videogenerierung und Prompt-Orchestrierung.",
      path: "https://higgsfield.ai"
    },
    {
      id: "tool-zapier",
      name: "Zapier",
      category: "Tools",
      connections: 38,
      description: "Automatisierte Webhook-Verbindungen und Third-Party-Konnektoren.",
      path: "https://zapier.com"
    },
    {
      id: "tool-pipewire",
      name: "PipeWire Audio",
      category: "Tools",
      connections: 45,
      description: "CachyOS Low-Latency Audio-Routing und pactl Hardware-Brücke.",
      path: "pavucontrol"
    },
    // Skills
    {
      id: "skill-os-bridge",
      name: "OS Hardware Bridge",
      category: "Skills",
      connections: 56,
      description: "Native Linux-Steuerung: pactl, brightnessctl, nmcli und Hardware Confirmation Gate.",
      path: "backend/actions/system_monitor.py"
    },
    {
      id: "skill-undo-stack",
      name: "Undo Stack Engine",
      category: "Skills",
      connections: 34,
      description: "Optimistischer 10-Ebenen-Transaktionsspeicher für Dateisystem & Systemeinstellungen.",
      path: "backend/core/undo.py"
    },
    {
      id: "skill-memory-index",
      name: "Dual-Tier Memory",
      category: "Skills",
      connections: 41,
      description: "Langzeitgedächtnis mit 900-Zeichen-Systemprompt-Budget und recall_memory.",
      path: "backend/memory/memory_manager.py"
    },
    // Wiki & Docs
    {
      id: "wiki-cachyos",
      name: "CachyOS Architecture",
      category: "Wiki",
      connections: 27,
      description: "Systemdokumentation zu Kernel-Schedulern, Pacman, PipeWire und KDE Plasma.",
      path: "https://wiki.cachyos.org"
    },
    {
      id: "wiki-gemini-live-spec",
      name: "Gemini Live API Specs",
      category: "Wiki",
      connections: 31,
      description: "WebSocket-Protokolldokumentation für Google GenAI Live Audio & Vision Part.",
      path: "https://ai.google.dev/api/live"
    },
    // Worlds
    {
      id: "world-dev-workspace",
      name: "Dev Workspace",
      category: "Worlds",
      connections: 52,
      description: "Lokale Entwicklungsumgebung und Quellcode-Repositories.",
      path: "/home/graba/Schreibtisch/ASGRAD/GRABAS_GITHUB/eigenjarv/2"
    },
    {
      id: "world-sysadmin",
      name: "Sysadmin Core",
      category: "Worlds",
      connections: 39,
      description: "Systemüberwachung, Backups, Netzwerk- und Kernel-Tools.",
      path: "/home/graba/Schreibtisch/ASGRAD/GRABAS_GITHUB/eigenjarv/2/backend"
    },
    // Notes
    {
      id: "note-2026-roadmap",
      name: "2026-Roadmap",
      category: "Notes",
      connections: 16,
      description: "Meilensteine für das autonome KI-Betriebssystem und TUI-Widgets.",
      path: "backend/knowledge_base/knowledge_map.json"
    },
    {
      id: "note-video-script",
      name: "VIDEO-SCRIPT-FULL",
      category: "Notes",
      connections: 12,
      description: "Skript für Vorstellung des CachyOS AI Betriebssystems.",
      path: "backend/knowledge_base/knowledge_map.json"
    },
    // Files
    {
      id: "file-server-py",
      name: "backend/server.py",
      category: "Files",
      connections: 24,
      description: "Zentraler WebSocket & Telemetrie-Bridge Server auf Port 8765.",
      path: "backend/server.py"
    },
    {
      id: "file-jarvis-core",
      name: "backend/core/gemini_live.py",
      category: "Files",
      connections: 29,
      description: "Vollduplex-Audio & Tool-Routing-Controller.",
      path: "backend/core/gemini_live.py"
    }
  ],
  links: [
    { source: "hub-ai-workshop", target: "hub-gemini-live" },
    { source: "hub-ai-workshop", target: "hub-skill-suites" },
    { source: "hub-ai-workshop", target: "hub-claude-code" },
    { source: "hub-ai-workshop", target: "hub-youtube-channel" },
    { source: "hub-ai-workshop", target: "world-dev-workspace" },
    { source: "hub-ai-workshop", target: "world-sysadmin" },
    { source: "hub-skill-suites", target: "skill-os-bridge" },
    { source: "hub-skill-suites", target: "skill-undo-stack" },
    { source: "hub-skill-suites", target: "skill-memory-index" },
    { source: "hub-skill-suites", target: "tool-zapier" },
    { source: "hub-skill-suites", target: "suite-finance" },
    { source: "hub-skill-suites", target: "suite-seo" },
    { source: "hub-skill-suites", target: "suite-ads" },
    { source: "skill-os-bridge", target: "tool-pipewire" },
    { source: "skill-os-bridge", target: "file-server-py" },
    { source: "hub-gemini-live", target: "file-jarvis-core" },
    { source: "hub-gemini-live", target: "file-server-py" },
    { source: "hub-gemini-live", target: "wiki-gemini-live-spec" },
    { source: "hub-youtube-channel", target: "tool-vidiq" },
    { source: "hub-youtube-channel", target: "tool-higgsfield" },
    { source: "hub-youtube-channel", target: "note-video-script" },
    { source: "world-sysadmin", target: "wiki-cachyos" },
    { source: "world-dev-workspace", target: "note-2026-roadmap" },
    { source: "suite-finance", target: "tool-zapier" }
  ]
};
