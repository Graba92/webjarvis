# 🚀 J.A.R.V.I.S. AI OS — Das futuristische 3D WebGL KI-Cockpit (Jetzt auch für Windows via WSL 2!)

Das **J.A.R.V.I.S. AI OS** bringt das ultimative Sci-Fi-Feeling auf deinen Desktop! Mit einer Kombination aus Next.js 15, Three.js 3D-Hologramm, Karpathy-Wissenstresor, Aufgaben-Backlog, interaktiver Bildanleitung und Google Gemini Live Sprachsteuerung hast du deinen persönlichen KI-Assistenten immer an deiner Seite — **nativ unter Linux (CachyOS/Arch) und jetzt mit 1-Klick-Orchestrierung auch unter Windows!**

### 🎮 Features auf einen Blick
- **⚡ Voice-First mit Gemini Live:** Schnelle Sprachein- und -ausgabe ohne spürbare Verzögerung mit Duplex-Audio.
- **🎙️ Dedizierte Voice Commands:** 'jarvis neustart' (sicherer Tool-Neustart ohne OS-Reboot), 'jarvis stop', 'jarvis mute' (Paranoia-Killswitch) und 'jarvis update' (GitHub Self-Update).
- **🪐 3D WebGL Hologramm-HUD:** Three.js Force-Graph mit volumetrischen Fresnel-Shadern, gestochen scharfer 1024px Billboard-Typografie mit adaptivem Entfernungs-LOD & Kollisionsschutz, 90-Iterationen Settle-on-Equilibrium Physik für stabile 60–120 FPS und Neon-Amber Orphan-Warnung.
- **🗺️ Interaktive Bild-Anleitung mit Pfeilen:** Neu! Visuelle Schritt-für-Schritt-Slideshow (`GuideOverlayModal.tsx` & Tool `show_guide`), die Hilfspfeile und Erklärungen direkt über das Interface legt – mit Ein-Klick-Download für jedes Bild!
- **🪟 Windows 1-Klick Starter (`run_windows.bat` / `run_windows.py`):** WSL2-Orchestrierung nach Bastler-Standard: Automatische Erkennung, interaktive TUI-Zustimmung, on-the-fly Pfadübersetzung (`wslpath`) und CRLF-Sanitizer gegen Bash-Crashes.
- **📋 Single-Writer Task Backlog:** Reines Markdown (`backlog.md`) mit Checkboxen, atomarem `os.replace`-Schutz und HUD-Drawer (`Alt+T`) mit Prioritäts-Tags und Pfeil-Sortierung.
- **🧠 Karpathy Knowledge Vault:** Kuratierter Wissensordner mit semantischen `[[Wiki-Links]]`, LanceDB-Vektorindex und Zero-Data-Loss Konflikterkennung.
- **🛡️ Gehärtete Sandbox- & Berechtigungs-Architektur:** Echte Bubblewrap (`bwrap`) Prozessisolation mit Zero-Escape Pfadvalidierung und Hardware-Confirmation-Gate.

---

### 💻 Schnelle Installation & Start

#### Unter Windows (WSL 2):
```cmd
git clone https://github.com/Graba92/webjarvis.git
cd webjarvis
run_windows.bat
```
*(Prüft automatisch WSL2, konvertiert Pfade und startet WebJarvis schlüsselfertig im Browser unter `http://localhost:3000`)*

#### Unter Linux (CachyOS / Arch / Generic):
```bash
git clone https://github.com/Graba92/webjarvis.git
cd webjarvis
chmod +x setup.sh start.sh run.sh
./setup.sh
./run.sh
```
