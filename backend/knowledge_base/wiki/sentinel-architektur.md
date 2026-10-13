# Sentinel Architektur (sb_exchange_sentinel.py)

## 1. Übersicht
Der **Sentinel** (`sb_exchange_sentinel.py`) fungiert als Host-Level-Sicherheitsnetz und Watchdog für das ASGRAD-Triumvirat. Er überwacht die Dropzone [[agent-exchange-protocol]] und steuert die koordinierte Ausführung von Aufträgen.

## 2. Kernmechaniken & Verifikationsprinzip
1. **Erfassung & Entkopplung (`QUEUED`):**
   - Eintreffende Direktiven werden registriert und als `phase: "QUEUED"` gemeldet.
   - **Eiserne Regel (Kein Bauchredner):** Der Sentinel erzeugt **niemals** ein `ACK` im Namen von [[god-mode-tui|Agy]] oder [[system-architecture-map|Friday]]. Ein `ACK` darf nur durch den annehmenden Agenten-Worker erfolgen.
2. **Deep-State Tracking (`PROGRESS`):**
   - Signalisiert reale Ausführung mit spezifischem Substate (z.B. `substate: "Sub-Process exec..."` oder `"File I/O Watch..."`), visualisiert live im [[god-mode-tui]].
3. **Strenge Härte gegen Fake-DONE:**
   - **`EXECUTION_SUCCEEDED`:** Ein Subprozess mit Exit-Code 0 gilt als technisch beendet, ist aber noch kein fachliches DONE, solange keine Ergebnisprüfung definiert ist.
   - **`DONE`:** Wird ausschließlich gesetzt, wenn eine definierte Zieldatei physisch existiert, nicht leer ist und die inhaltliche Validierung bestanden wurde.
   - **`FAILED`:** Explizite Fehlermeldung bei Exitcode != 0 oder nicht bestandener Inhaltsprüfung.

## 3. Sicherheits-Gate (Command Injection Schutz)
- Unvalidierte Shell-Strings (`shell=True`) sind untersagt.
- Befehle werden gegen Metazeichen (`;`, `&&`, `|`, etc.) und eine Whitelist sicherer Befehle geprüft und als Token-Liste (`shell=False`) ausgeführt.

## 4. Verknüpfungen
- [[agent-exchange-protocol]]
- [[god-mode-tui]]
- [[audio-stack-zustaendigkeiten]]
- [[masterplan-phasen]]
