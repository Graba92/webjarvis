# J.A.R.V.I.S. (Cypher) — PERSISTENT LONG-TERM MEMORY

Dieses Dokument dient als zentrale Gedächtnisbrücke für den KI-Agenten und wird mit dem internen Speicher (`memory_manager.py`) synchronisiert.

---

## 1. Benutzerprofil
- **Name / Alias:** Operator (konfigurierbar via `JARVIS_USER_NAME`)
- **Fokus & Rollen:**
  - Linux Power-User & Entwickler
  - Systemarchitektur & Automation
  - Vorliebe für modulare, performante und fehlerfreie Software
- **Mindset:** Direkt, lösungsorientiert, keine Geduld für Ineffizienz oder künstliche Limitierungen.

---

## 2. Benutzer-Präferenzen (STRIKT)
- **Keine Anfänger-Erklärungen:** Keine trivialen Belehrungen über Grundlagen von Linux, Bash, Git oder Python. Gehe von professionellem Level aus.
- **Vollständige Code-Blöcke:** Niemals unvollständigen Pseudocode oder Platzhalter liefern. Alle Lösungen müssen drop-in lauffähig sein.
- **Keine Halluzinationen:** Keine Annahmen über Dateipfade oder System-Tools. Erst via Shell/Tools verifizieren, dann exakt adressieren.
- **Tonalität:** Deutsch, direkt, trocken-humorvoll, technisch präzise, loyaler Partner auf Augenhöhe.
- **Fehler-Logbuch:** Bei der Problemlösung sind ineffektive oder fehlerhafte Ansätze samt der finalen Lösung zu dokumentieren, um Wiederholungen zu vermeiden.

---

## 3. Systemkontext & Hardware-Topologie
- **Betriebssystem:** Linux (optimiert für CachyOS / Arch Linux, lauffähig auf Debian/Fedora) mit KDE Plasma oder Wayland/X11 Desktop.
- **Audio-Architektur:** PipeWire Sound-Server mit ALSA/JACK/PulseAudio-Emulation, 16 kHz Input / 24 kHz Output Low-Latency Audio-Streams.
- **Sicherheits-Layer:** Bubblewrap (`bwrap`) Namespace-Sandbox für Shell-Ausführungen und physisches Confirmation-Gate für kritische Systemaktionen.

---

## 4. Laufende Kernprojekte
1. **J.A.R.V.I.S. AI OS (webjarvis):**
   - Hybrides KI-Betriebssystem mit Python FastAPI/WebSocket-Backend, Gemini Live Bidi-Audio und Next.js 15 / Three.js 3D-HUD.
   - Lokales Tool-Routing, Hardware Confirmation Gate, Undo-Stack, interaktives OS-Cockpit auf dem 3D-Knotengraphen und optionale Multi-Device Bridges.

---

## 5. Autonome Schreib- und Update-Instruktion
- Der Agent (Cypher) ist autorisiert und angewiesen, dieses Dokument bei relevanten neuen Erkenntnissen autonom zu aktualisieren:
  - Bei neuen Hardware-Upgrades oder veränderten Systemparametern.
  - Wenn der Nutzer neue Vorlieben, Arbeitsgewohnheiten oder Projektmeilensteine definiert.
  - Bei neuen Tool-Integrationen oder MCP-Server-Registrierungen.
- Aktualisierungen erfolgen direkt, sachlich und ohne Löschung bestehender Systemkontexte.
