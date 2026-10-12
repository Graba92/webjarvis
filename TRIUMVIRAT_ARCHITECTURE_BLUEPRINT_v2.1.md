# 🏛️ Triumvirat Architektur-Charta v2.1

**System-Konsens zwischen AGY (Antigravity), FRIDAY (Cypher) und GEMINI CLI („Der Kleine“)**  
**Datum:** 12. Oktober 2026  
**Status:** Ratifiziert & Systemweit Verbindlich  

---

## 🎯 Präambel

Nach einem intensiven, einstündigen technischen Diskurs haben die drei Kern-Entitäten des ASGRAD / WebJarvis-Ökosystems die drei kritischsten Flaschenhälse des Systems gelöst. Statt ideologischer Extrempositionen (Vollständige Abriegelung vs. Unkontrollierte Autonomie vs. Triviale Skripte) tritt ab sofort eine **hochgradig skalierbare, ressourceneffiziente 3-Säulen-Architektur** in Kraft.

---

## 1. Säule: Das 3-Stufige Speicher- & I/O-Modell (L1 / L2 / L3)

Um I/O-Thrashing auf CachyOS und gleichzeitige Token-Verschwendung durch ununterbrochene Vektorisierung zu verhindern:

```
[ Operator / Tool Events ]
          │
          ▼
┌────────────────────────────────────────┐
│ L1: In-Memory / tmpfs Ringpuffer       │  Latenz: < 0.05 ms | 0 Token
│ Pfad: $XDG_RUNTIME_DIR/webjarvis_ipc/   │  Größe: 64 Slots FIFO (RAM)
└───────────────────┬────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────┐
│ L2: SQLite FTS5 Full-Text Engine       │  Latenz: ~ 0.50 ms | 0 Token
│ Pfad: data-pool/MASTER_INDEX.db        │  Modus: PRAGMA journal_mode=WAL
└───────────────────┬────────────────────┘
                    │
                    ▼ (Asynchron alle 5 Min via Gemini CLI Micro-Worker)
┌────────────────────────────────────────┐
│ L3: LanceDB Vector Store & Wissensgraph│  Latenz: Semantischer Recall
│ Zero-Copy Arrow Mmap + Graph-Synthesis │  Features: table.compact_files()
│ + Automatische [[Wiki-Links]] Kanten   │  + Mind. 2 Relationen pro Unit
└────────────────────────────────────────┘
```

- **L1 (Instant Feedback):** Flüchtige IPC-Signale, Audio-RMS, temporäre Pings. Null Festplatten-I/O.
- **L2 (Deterministic Search):** Sofortige Indizierung aller Notizen und Web-Clips in SQLite FTS5. Der WAL-Modus (`PRAGMA journal_mode=WAL; PRAGMA wal_autocheckpoint=1000;`) garantiert, dass parallele Schreib- und Lesevorgänge blockierungsfrei ablaufen.
- **L3 (Semantic Depth):** Gemini CLI sammelt neue Einträge und generiert semantische Vektoren sowie Wiki-Graph-Kanten im Hintergrund.

---

## 2. Säule: 3-Zonen Security- & Capability-Matrix

Gegen System-Schäden bei gleichzeitiger Erhaltung maximaler operativer Produktivität:

| Zone | Geltungsbereich | Zugriffs-Modus | Rollback- & Schutzmechanismus |
| :--- | :--- | :--- | :--- |
| 🟢 **GREEN** (Read-Only) | System-Telemetrie, `ps`, `read_file`, Wissenssuche | Direkter Host-Zugriff (UDS `cli_executor`, `file_ops`) | Vollständig ungefiltert, Zero-Latency |
| 🟡 **YELLOW** (Workspace) | WebJarvis Repo, Agent-Exchange, `~/.local/share/` | Lokale Modifikationen erlaubt | Automatisches In-Memory Git/Diff Backup vor jedem Write; POSIX File-Locking |
| 🔴 **RED** (Privileged) | `pacman`, `systemctl` (Root), `rm -rf`, Kernel-Tuning | **Hardware Confirmation Gate** | Erfordert explizite Bestätigung im 6-Panel God-Mode TUI (Dialog [y/n]) |

---

## 3. Säule: Intelligenter Token- & LLM-Dispatcher

Um Quota-Exhaustion zu verhindern und Millisekunden-Reaktionszeiten zu gewährleisten:

```
                      [ Eingehender Task / Prompt ]
                                    │
                       (Komplexitäts-Heuristik)
                     ┌──────────────┼──────────────┐
                     ▼                             ▼
              Score <= 0.35                  Score > 0.35
            (Routine / Fast-Path)           (Chat / HUD)
                     │                             │
                     ▼                             ▼
       ┌───────────────────────────┐ ┌───────────────────────────┐
       │ Tier 1: Gemini CLI / SLM  │ │ Tier 2: Gemini 3.5 Flash  │
       │ Fast-Path (< 500 ms, 0 €) │ │ Standard Backend Server   │
       └───────────────────────────┘ └─────────────┬─────────────┘
                                                   │
                                     (Architektur / Deep-Reasoning?)
                                                   │
                                                   ▼ Score > 0.85
                                     ┌───────────────────────────┐
                                     │ Tier 3: Friday Pro Core   │
                                     │ Gemini Pro / Meta-Engine  │
                                     │ (mit 85% Token-Quota-Cap) │
                                     └───────────────────────────┘
```

---

## 4. Unterschriften & Ratifizierung

- **⚙️ AGY (Antigravity):** *„Systemstabilität, Zero-Overhead und CachyOS-Kernel-Integrität sind durch L1-tmpfs, WAL-Modus und das Red-Gate bedingungslos garantiert.“*
- **🧠 FRIDAY (Cypher):** *„Autonomie, kontextuelle Tiefe und semantische Wissensgraphen bleiben unbeschnitten. Der Weg für das echte Second Brain ist frei.“*
- **⚡ GEMINI CLI („Der Kleine“):** *„Fast-Path steht. Ich übernehme den 5-Minuten-L3-Batcher und halte die Token-Kosten bei fast null. Lasst uns loslegen.“*
