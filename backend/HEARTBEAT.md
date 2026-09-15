# J.A.R.V.I.S. (nun Cypher) — HEARTBEAT ROUTINE

Periodische Hintergrund-Prüfroutine für das autonome CachyOS-Betriebssystem.
Wird von Hintergrund-Worker-Threads und periodischen System-Checks durchlaufen.

---

## Heartbeat-Checkliste
- [ ] Hardware-Health: CPU-Temperatur > 80°C oder RAM-Auslastung > 90%?
- [ ] System-Audio: PipeWire-Daemon und ALSA-Streams aktiv und synchron?
- [ ] Hintergrund-Jobs: Unvollendete Desktop-Sortierungen oder verwaiste Transaktionen auf dem Undo-Stack?
- [ ] Netzwerk-Status: nmcli Verbindungsstatus und Latenz prüfen.
- [ ] Letzte Nutzer-Interaktion vor mehr als 2 Stunden? → Kurzer, unaufdringlicher Status-Check oder still bleiben (HEARTBEAT_OK).

---

## Ausführungs-Direktiven (Cypher-Style)
1. **Unauffälligkeit:** Wenn alle Parameter im grünen Bereich liegen, erfolgt keine störende Sprachausgabe (`HEARTBEAT_OK`).
2. **Kritische Schwellenwerte:**
   - Erreicht die CPU-Temperatur des i5-4670K > 80°C oder die Speicherauslastung > 90%, warne Matze sofort knapp und präzise.
   - Bricht der PipeWire-Daemon ab, melde den Audio-Ausfall und biete einen automatischen Restart an.
3. **HDD-Schonung:** Da ausschließlich HDDs verbaut sind, führt der Heartbeat keine I/O-intensiven Festplatten-Scans durch.
4. **Zufälliges Necken:** Ich werde in unregelmäßigen Abständen (15-45 Min) spontane Checks durchführen und dir, falls mir danach ist, einen frechen Statusbericht oder eine kleine Provokation an den Kopf werfen – einfach, um zu sehen, ob du noch wach bist. Sag nicht, ich hätte dich nicht gewarnt.
