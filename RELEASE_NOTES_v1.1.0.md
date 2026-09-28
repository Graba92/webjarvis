# 🚀 Release v1.1.0 — Dedicated Voice Commands, 3D Graph Brain Vault & Resilient Sandbox

### 🎙️ Neue dedizierte Voice Commands (Tool Control)
- **`"jarvis neustart"`**: Startet ausschließlich das J.A.R.V.I.S. AI OS Tool (Backend & Frontend) über das neue `restart.sh` Skript neu — **ohne** das gesamte Betriebssystem (CachyOS Host) herunterzufahren oder neu zu starten!
- **`"jarvis stop"`**: Hält Sprachausgabe, Audio-Playback und laufende Tasks augenblicklich an und kehrt in den Bereitschaftsmodus zurück.
- **`"jarvis mute"`**: Aktiviert den hardwarenahen PipeWire **Paranoia-Killswitch**, trennt den Audio-Eingabestrom sofort und signalisiert den Status im HUD.
- **`"jarvis update"`**: Autonomer GitHub-Self-Updater. Vergleicht den lokalen Git-Stand mit `https://github.com/Graba92/webjarvis`, zieht anstehende Aktualisierungen (`git pull --ff-only`) und bietet den direkten Tool-Neustart an.

### 🧠 3D Knowledge Graph Brain Vault Integration
- **Vollständige Sicherung der Graph-Knoten (`graph_nodes.json`)**: Das 1-Click Brain Vault sichert ab sofort auch den interaktiven 3D Force-Directed Wissensgraphen samt semantischer Relationen und Kategorien.
- **Event-Driven Live-HUD-Sync**: Bei der Wiederherstellung eines Backups (direkt oder via Upload) werden alle 3D-Knoten ohne Page-Reload sofort im HUD gerendert (`graph_sync`).

### 🛡️ Gehärtete Sandbox- & Rechte-Matrix
- **Persistenter OS-Vollzugriff**: Der Status von `full_os_access` wird dauerhaft in `sandbox_config.json` gespeichert.
- **Unicode NFC-Normalisierung**: Resiliente Pfadauflösung für Umlaute (z. B. `Ü`, `Ä`, `Ö`) und Symlinks gegen NFD/NFC-Fehlabgleiche.
- **Dynamische MCP-Filesystem-Server-Pfade**: Der `@modelcontextprotocol/server-filesystem` Server erhält dynamisch alle freigegebenen Sandbox-Pfade (oder `/` bei Vollzugriff).
