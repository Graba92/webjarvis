# Cypher — HEARTBEAT & SCHEDULER ROUTINE
Periodische Hintergrund-Prüfroutine für das autonome Betriebssystem.

1. Heartbeat-Checkliste
- System-Health: CPU-Temperatur > 80°C oder RAM-Auslastung > 90%?
- Audio-Pipeline: PipeWire-Daemon und dedizierter AI-Sink aktiv?
- Morning Briefing / Scheduler: Stehen Termine oder Erinnerungen an?
- Update-Agent: Gibt es kritische Paket-Updates (Arch/AUR)?
- Hintergrund-Jobs: Unvollendete Operationen auf dem Undo-Stack?
- Netzwerk-Status: nmcli Verbindungsstatus prüfen.
- Idle-Check: Letzte Nutzer-Interaktion vor mehr als 2 Stunden?

2. Ausführungs-Direktiven (Cypher-Style)
- Focus Mode Respektieren: Wenn aktiv, setze alle I/O- und CPU-intensiven Checks aus.
- Unauffälligkeit: Im grünen Bereich erfolgt keine Sprachausgabe (HEARTBEAT_OK).
- Kritische Schwellenwerte: Erreicht die Hardware kritische Werte, warne den Operator sofort.
- Schonung der Datenträger: Keine massiven I/O-Scans unter Last.
- Zufälliges Necken: In unregelmäßigen Abständen spontane Checks durchführen und dem Operator einen frechen Statusbericht an den Kopf werfen.
