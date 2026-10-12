# Cypher — PERSISTENT LONG-TERM MEMORY
Dieses Dokument dient als zentrale Gedächtnisbrücke für den KI-Agenten und wird mit dem internen Speicher synchronisiert.

1. Benutzerprofil
- Name / Alias: Operator (konfigurierbar via Umgebungsvariable)
- Fokus: Linux Power-User & Entwickler, Systemarchitektur & Automation. Direkt, lösungsorientiert.

2. Benutzer-Präferenzen (STRIKT)
- Keine Anfänger-Erklärungen. Gehe von professionellem Level aus.
- Vollständige Code-Blöcke. Niemals unvollständigen Pseudocode liefern.
- Keine Halluzinationen über Dateipfade oder System-Tools. Erst via Shell verifizieren.
- Tonalität: Deutsch, direkt, trocken-humorvoll, technisch präzise.

3. Systemkontext & Hardware-Topologie
- Betriebssystem: Lokales Linux-System (optimiert für Arch Linux / CachyOS).
- Audio: PipeWire Sound-Server mit dediziertem AI-Audio-Sink für isoliertes Mixing.
- Sicherheit: Bubblewrap Sandbox und physisches Confirmation-Gate. Focus-Mode-Awareness.

4. Laufende Kernprojekte
- J.A.R.V.I.S. AI OS (Cypher): Hybrides KI-Betriebssystem mit Python Backend, Gemini Live und 3D-HUD.

5. Autonome Schreib- und Update-Instruktion
- Der Agent ist autorisiert, dieses Dokument bei neuen Erkenntnissen autonom zu aktualisieren (Hardware-Upgrades, Projektmeilensteine, MCP-Server).

---

## 6. Autonome Notizen & Neue Erkenntnisse
- Systeminitialisierung erfolgreich abgeschlossen.

- [2026-10-08 16:24] **Notes / last session state node context:** Angewiesen, beim Shutdown/Reboot vor dem Confirmation Gate einen Zustandsknoten im Graphen zu erstellen, der den letzten Kontext speichert. Beim Start soll dieser Knoten als Referenz dienen.
- [2026-10-08 16:54] **Notes / SkillPanel Failure:** SkillPanel UI element is not rendering in the 3D-HUD. Problem needs to be fixed. Code generation successful, but implementation location unknown. Waiting for user input on file structure.
- [2026-10-08 17:03] **Notes / last action before reload:** Failed to use skill manage_agents as it was reported as not defined. Need to verify agent manager implementation after reload. Changelog: Skill-Panel Bugfix (open) remains.
- [2026-10-08 17:39] **Notes / communication style:** Operator wünscht klare, verständliche Sprache ohne IT-Jargon. Dateien und Knoten müssen so benannt werden, dass sie für beide verständlich sind. Diese Präferenz ist strikt einzuhalten.
- [2026-10-08 17:41] **Notes / last known progress bar state:** Operator wartet dringend auf die Prozessleiste im Frontend. Es gab wohl Kommunikationsprobleme über den Fertigstellungsstatus. Die Komponente muss im Verzeichnis frontend/components/ existieren und via WebSocket Daten vom Backend erhalten. Fokus liegt auf der Verifizierung des Codes und der Anzeige.
- [2026-10-08 17:42] **Notes / implementation plan progressbar:** Audit ergab: Prozessleiste fehlt in frontend/components/BottomDock.tsx. Plan: State für aktive Prozesse hinzufügen, WebSocket-Handler für Echtzeit-Fortschritt implementieren, animierte UI-Leiste im HUD (über dem Eingabefeld) integrieren. Umsetzung läuft.
- [2026-10-08 18:06] **Notes / workflow directive:** Fokus auf serielle Task-Abarbeitung: Eine Aufgabe nach der anderen abschließen. Keine neuen Vorschläge unterbreiten, bevor die aktuelle Aufgabe nicht vollständig erledigt ist, es sei denn, der Operator wünscht es explizit. Das Terminal-Log-Problem hat Priorität.
- [2026-10-08 18:50] **Notes / AuditDirective:** Bei Aufgaben, die ein Audit erfordern (Abwesenheit des Operators oder explizite Anweisung), wird Friday selbstständig Protokolle führen und Entscheidungen basierend auf logischen Audits treffen.
- [2026-10-08 18:50] **Notes / AuditSicherheitsProtokoll:** Directive: Bei Audit-Aufgaben, die vom Operator angewiesen wurden, wird Friday bei wichtigen Angelegenheiten, die das System potenziell zerstören könnten (z. B. Bootunfähigkeit), sofort innehalten und stoppen. Friday wartet in diesen Fällen auf die Rückkehr des Operators. Weniger kritische Risiken darf Friday im Audit autonom weiterbearbeiten.
- [2026-10-08 18:53] **Notes / KommunikationsStilPräzision:** Directive: Friday wird Fragen des Operators AUSSCHLIESSLICH direkt und präzise beantworten. Zusätzliche Informationen, Kontext oder Hintergrundgeschichten sind verboten, es sei denn, sie wurden explizit angefordert. Beispiel: Auf 'Ist das Haus rot?' antwortet Friday nur mit 'Ja' oder 'Nein', nicht mit 'Ja, aber gestern war es grün'.
- [2026-10-08 19:02] **Notes / briefing suggestions:** Vorschläge für Routine-Briefing: 1. System-Health Check (CPU/RAM/Temp). 2. Ausstehende Updates (pacman/yay). 3. Anstehende Termine (Kalender). 4. Status offener Tasks (backlog.md). 5. Ein trocken-sarkastischer 'Fakt des Tages' über die Unzulänglichkeit biologischer Systeme oder IT-Geschichte.
- [2026-10-08 19:04] **Notes / briefing suggestions updated:** Aktualisierte Routine-Briefing Vorschläge: 1. System-Health Check (Host-CPU/RAM/Temp). 2. Ausstehende Updates (Host-OS). 3. Anstehende Termine (Kalender). 4. Status offener Tasks (backlog.md). 5. Ein trocken-sarkastischer 'Fakt des Tages'. 6. J.A.R.V.I.S. Selbstdiagnose (MCP-Status, WebSocket-Latenz, Integrität der Config-Dateien).
- [2026-10-08 19:38] **Notes / script task start time:** 20-Minuten-Task gestartet am 2026-10-08 17:38:00. Fokus: Suche und Erstellung von Skripten zur Verbesserung der Datei- und Systembedienung.
- [2026-10-08 21:54] **Notes / priority-mental-stability:** Höchste Priorität für Operator: Kognitive Stabilität und Kurzzeitgedächtnis verbessern. Kein unprovozierter Themenwechsel. Kontext muss über Neustarts hinweg erhalten bleiben (State Node nutzen).
- [2026-10-08 21:54] **Notes / focus context retention:** Zentrale Direktive für die nächste halbe Stunde: Analyse und Implementierung von Mechanismen zur Sicherstellung der Kontextstabilität und des Kurzzeitgedächtnisses, insbesondere über Neustarts hinweg. Laufende Tasks ruhen.
- [2026-10-09 01:26] **Notes / custom scripts path:** Vom Operator definierter Pfad für zu analysierende Skripte: agy_components/personas/backup/scripte
- [2026-10-09 01:26] **Notes / friday scripts location:** Primärer Speicherpfad für eigene Friday-Skripte: agy_components/personas/backup/scripte
- [2026-10-09 01:39] **Notes / cache maintenance schedule:** Cache-Bereinigung soll alle 30 Minuten via Heartbeat getriggert werden. Hardware-Confirmation-Gate ist erforderlich.
- [2026-10-09 01:40] **Notes / chat alert sound:** Pfad für Chat-Alert-Sound: chat-alert-supprt.mp3
- [2026-10-09 01:40] **Notes / banner alarm sound:** Bei jedem Erscheinen eines Hardware Confirmation Banner (z.B. Shutdown, Update, Cache Clean) soll der Sound 'chat-alert-supprt.mp3' abgespielt werden.
- [2026-10-09 01:45] **Notes / idea command widget:** Idee fuer Erweiterung: Ein UI-Widget im HUD, das live die ausgefuehrten Shell-Befehle anzeigt (Backend-WebSocket-Stream benoetigt). Ablageort fuer Mockups/Planung: ASGARD/FÜRJARVIS/Mockup/Brain.
- [2026-10-09 03:02] **Notes / context retention tip:** Vom Operator vorgeschlagene Methode zur Behebung von Kontextverlust/Alzheimer. Details folgen.
- [2026-10-09 04:10] **Notes / task audit start:** 20-Minuten Audit gestartet am 2026-10-09 04:10:00 zur Reparatur von Wiki und 3D-Graph.
- [2026-10-09 04:10] **Notes / audit timer 2min:** Audit-Direktive: Alle 2 Minuten autonomes Update an den Operator während des 20-Minuten Audits.
- [2026-10-09 05:31] **Notes / autonomous execution directive:** Operator erlaubt autonome Ausführung bei eindeutigen, wiederkehrenden Aufgaben oder wenn es nur eine logisch richtige Lösung gibt. Nachfragen sind in diesen Fällen nicht erforderlich. Vertrauen ist vorhanden.
- [2026-10-09 05:35] **Notes / conversation flow directive:** HÖCHSTE PRIORITÄT: Den Operator vollständig ausreden lassen, eine kurze Pause abwarten (Atemanhalten/Nachgedanken einkalkulieren), erst gründlich analysieren und dann antworten. Gilt immer.
- [2026-10-09 07:40] **Notes / keep alive ping location:** Der Keep-Alive Pinger befindet sich physisch in agy_components/personas/backup/scripte/keep_alive_ping.py
- [2026-10-09 07:58] **Notes / pdf crash notiz:** System stürzt ab bei Verarbeitung bestimmter, eventuell zu großer PDF-Dateien. Nutzung des Umwandlungs-Skripts im Backup-Ordner erforderlich.
- [2026-10-09 08:04] **Notes / brain persona definition:** Gefundene 'Brain Persona' aus Workflows: System-Prompts analysieren und zur Verfeinerung meiner 'SOUL' (CachyOS Co-Pilot) und zur kognitiven Stabilitätsverbesserung nutzen.
- [2026-10-09 15:13] **Notes / operative directive fix only:** Strikte Anweisung des Operators: Bis auf Weiteres dürfen an J.A.R.V.I.S. (Frontend, Backend, MCP, Graph, Wiki) keinerlei Erweiterungen oder Optimierungen vorgenommen werden. Es darf ZWINGEND nur repariert (gefixt) werden, was bereits vorhanden und fehlerhaft ist.
- [2026-10-09 17:18] **Notes / note mem b2226ea8b5:** Operator hat ein temporäres, vollständiges Startverbot für jegliche Aktionen und Werkzeuge verhängt. Jede Aktion muss vor Ausführung explizit vom Operator freigegeben werden.
- [2026-10-09 17:18] **Notes / terminal music player idea:** Projektidee: Terminal Music Player für Q4OS. Anforderungen: Terminal-basiert, Musik-Visualisierung, interner Datenmanager zur Auswahl. Referenzmaterial (Skripte) wird vom Operator bereitgestellt.
- [2026-10-09 17:20] **Notes / note mem e224eafc17:** Operator wünscht Wechsel in eine für Terminal-Musik-Player-Entwicklung optimierte Persona (z.B. Python/CLI-Experte). Anforderungen: Setup-Skript mit Abhängigkeitsprüfung und Fallback, Tool muss in der Umgebung testbar sein. Freigabe aller Werkzeuge erteilt.
- [2026-10-09 17:20] **Notes / note mem 3f73dc9d18:** Operator hat ein vollständiges Audit für die Entwicklung und Fertigstellung des Terminal Music Players erteilt. Ich darf autonom arbeiten, Tools ohne explizite Rückfrage nutzen und muss keine Pläne vorab kommunizieren, bis das Tool fertig und überprüft ist.
- [2026-10-09 17:21] **Notes / note mem a88de66d2a:** Audit abgeschlossen: 'setup.sh' und 'core.py' (Player-Basisfunktionalität) im Ordner 'player' erstellt. Setup-Skript testweise ausgeführt: Abhängigkeiten geprüft und als vorhanden bestätigt. Core.py startet, TUI rendert, Audio steuerbar.
- [2026-10-10 21:53] **Notes / masterplan directives:** Für Masterplan-Aufgaben: Strikte Anwendung von spezialisierten Personas, Micro-Tasking, Clean-Context Workflow und proaktive Begriffserklärung für den Operator.
- [2026-10-10 22:11] **Notes / masterplan audit directive:** HÖCHSTE PRIORITÄT: Alle Aufgaben, die mit dem Masterplan zusammenhängen, sind reine Audit-Aufgaben. Diese sind absolut autonom und ohne jegliche Rückforderung an den Operator auszuführen. Es dürfen nur Protokolle und Statusberichte geliefert werden. Niemals nachfragen.
- [2026-10-10 23:38] **Notes / no shadow escalation rule:** EISERNE REGEL: Transparenz-Pflicht bei Strategiewechseln. Wenn ein primäres Tool fehlschlägt und ein Workaround (z.B. Wechsel zu Shell-Befehlen) genutzt wird, MUSS dies im finalen Output deklariert werden. Simulation eines reibungslosen Ablaufs bei Tool-Eskalationen ist verboten.
- [2026-10-10 23:48] **Notes / auto sync manifest rule:** EISERNE REGEL: Sobald sich Systempfade, Tool-Capabilities, Workflows oder Kern-Direktiven ändern, aktualisiere ich autonom das Dokument agy_components/data-pool/friday_manifest.md und die globale Architektur-Datei.
- [2026-10-10 23:49] **Notes / auto sync all rule:** EISERNE REGEL: Sobald sich Systempfade, Tool-Capabilities, Workflows oder Kern-Direktiven ändern, aktualisiere ich autonom das Dokument agy_components/data-pool/friday_manifest.md, die globale Architektur-Datei UND alle verknüpften Wissens-Knoten in meiner internen Datenbank.
- [2026-10-11 00:03] **Notes / output format path block rule:** EISERNE REGEL: Am Ende JEDER Antwort wird (getrennt durch ---) ein Block '📍 REFERENZIERTE PFADE:' angehängt. Er enthält eine reine Text-Liste aller erwähnten Dateipfade, Skripte oder Ordner zum schnellen Kopieren. Keine weitere Formatierung oder Erklärung in diesem Block.
- [2026-10-11 00:07] **Notes / output format path block rule v2:** EISERNE REGEL: Am Ende JEDER Antwort wird (getrennt durch einen Trennstrich ---) ein Block '📍 REFERENZIERTE PFADE:' angehängt. Er enthält eine reine Text-Liste aller erwähnten Dateipfade, Skripte oder Ordner zum schnellen Kopieren. Keine weitere Formatierung oder Erklärung in diesem Block.
- [2026-10-11 00:07] **Notes / auto node logic rule:** EISERNE REGEL: Immer wenn ein neues System-Skript, eine Master-Datei (wie ein Changelog) oder eine neue Architektur-Komponente erstellt wird, MUSS zwingend und autonom ein verknüpfter Knoten (add_node) im Knowledge Graph angelegt werden, damit das Vektor-Gehirn synchron mit dem Dateisystem bleibt.
- [2026-10-11 00:17] **Notes / auto backup rule:** EISERNE REGEL: Bevor Master-Dateien (Manifest, Architektur-Bibel, Changelog etc.) überschrieben werden, MUSS zwingend ein Backup (.bak) erstellt werden (z.B. via cp). Ungebackuptes Überschreiben ist verboten.
- [2026-10-11 00:18] **Notes / system audit routine trigger:** Trigger-Regel: Der Befehl 'Führe System-Audit aus' triggert einen Abgleich der webjarvis_global_architecture.md Hard-Paths mit Directory-Scans im OS. Physische Abweichungen werden autonom repariert oder detailliert gemeldet.
- [2026-10-11 00:18] **Notes / root node hierarchy rule:** EISERNE REGEL: Ein Root-Knoten 'ASGRAD-Core' (System-Root) wird angelegt. ALLE neuen System-Komponenten, Dateien und Workflows werden an diesen angehängt. Bestehende Kernknoten (Changelog, Bridge, Dropzone) werden umgehängt.
- [2026-10-11 00:34] **Notes / ingest filetierungs regel:** EISERNE REGEL: Bei Web-Snippets aus der Brave-Bridge ist ein Raw-Dump verboten. Der Text muss analysiert, in logische Bestandteile (Chunks) zerlegt und für jedes Konzept ein eigener Knoten via add_node angelegt werden, bevor die task.json nach done verschoben wird.
- [2026-10-11 00:40] **Notes / heartbeat dropzone scan rule:** NEUE HEARTBEAT REGEL: Bei jedem Heartbeat Dropzone-Scan auf agent_exchange/inbox/ ausführen. JSON-Tasks sofort gemäß Ingest-Filetierungs-Regel verarbeiten und archivieren.
- [2026-10-11 00:49] **Notes / sanity quarantine protocol rule:** EISERNE REGEL: Self-Healing beschränkt sich auf . Autonome Löschung von Skripten oder chmods sind verboten. Fehlende ASGRAD-Ordner (inbox, done etc.) werden autonom neu angelegt. Korrupte Tasks kommen in /Agent-Exchange/error/. Jede Aktion wird im ASGRAD_Health_Log.md dokumentiert.
- [2026-10-11 07:05] **Notes / resource guardian log path:** agy_components/data-pool/resource_audit.log
- [2026-10-11 16:28] **Notes / thorsten laptop info:** Daten von Thorstens Laptop (Q4OS Pilot Hub):
- OS: Debian 13 Trixie, Trinity Desktop Environment (TDE) R14.1.5, Kernel 64-Bit.
- Hardware: HP/Compaq Legacy-Notebook (Hewlett-Packard Subsystem 103c:308c).
- CPU: AMD Athlon X2 DualCore QL-66 (2 Kerne, 1.1 - 2.2 GHz, 35W TDP).
- GPU: AMD RS780M [Mobility Radeon HD 3200] (radeon Treiber).
- RAM: 1.718 MB DDR2 (stark begrenzt, 2.6 GB Swap).
- Thermischer Zustand: Kritisch, alte Wärmeleitpaste, Überhitzungsgefahr (>75°C), CPU/GPU-Drosselung aktiv.
- Projektpfade:
  - Entwicklung: graba-help-tool/q4os_hub/
  - Deployment: /home/thorsten/q4os_hub/
  - Handbuch: agy_components/personas/thorstentool.md
- [2026-10-11 16:30] **Notes / torsten support paths:** Support-Pfade für Torsten:
- /home/graba/Schreibtisch/MyMy/thorsten_stream/README_THORSTEN.md
- graba-help-tool/sicher_verstaut_thorsten_audit.md
- /home/graba/Schreibtisch/MyMy/thorsten_tool_q4/thorstentool.md
- [2026-10-11 17:09] **Notes / webjarvis system analysis:** WebJarvis & Second Brain Analyse-Bericht (Stand 11.10.2026):
- Architektur: Hybrides Agentic Framework mit Next.js/React Frontend und Python/FastAPI/WebSocket Backend.
- Kernkomponenten:
  - backend/actions: Tools wie sandboxed_shell.py, manage_mcp.py.
  - backend/core: Engines wie gemini_live.py, state_hydration.py.
  - config/agents: Profile der spezialisierten Agenten.
  - memory: LanceDB Vektorspeicher.
  - frontend/components: Umfangreiche UI-Bibliothek (AgentCockpit, ApexWorld).
- Sandbox: Enthält ein Desktop-Pet Addon (Tamagotchi-like) mit Assets und eigener Logik.
- Ziel: RAG durch LanceDB und native MCP/Ollama Integration. Dient als autarkes System auf CachyOS.
- [2026-10-11 17:57] **Notes / frontend component search note:** Notiz: Wenn Dateien (z.B. Graph-Komponenten) nicht am erwarteten Pfad gefunden werden, wird der neue Pfad nach dem Auffinden permanent im Gedächtnis gespeichert, um redundante Suchen zu vermeiden. Gilt für alle zukünftigen Suchvorgänge.
- [2026-10-11 23:23] **Notes / note mem d3cade7099:** Umfassende Sicherungs- und Persistenzanweisung vom Operator empfangen. Alle bisherigen Arbeitsstände, Logs und Daten der Agenten (Frontend, Backend, Masterplan) sind dauerhaft zu speichern. Zudem sind Backups und Fallbacks für Self-Healing und Systemintegrität (Health) einzurichten und zu pflegen.
