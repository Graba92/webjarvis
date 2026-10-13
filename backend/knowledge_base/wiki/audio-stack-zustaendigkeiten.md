# Audio-Stack & Rollentrennung

## 1. Übersicht
Um Kompetenzüberschneidungen und unkontrollierte Audio-Überlagerungen auszuschließen, gilt im ASGRAD-System eine strikte funktionale Trennung der Tonausgabe.

## 2. Domänen & Zuständigkeiten
| Domäne | Zuständiger Agent | Implementierung | Kanal / Datei |
| :--- | :--- | :--- | :--- |
| **System-Alerts & Host-Signale** | **Agy** (Host Engine) | PipeWire `pw-play` | Exklusiv: `/home/graba/Schreibtisch/ASGRAD/universfield-new-notification-026-380249.mp3` |
| **Confirmation Alarm** | **Agy** | PipeWire `pw-play` | `/home/graba/Schreibtisch/ASGRAD/chat-alert-supprt.mp3` |
| **Kognitive Sprachausgabe (TTS)** | **Friday** (WebJarvis) | WebJarvis TTS Pipeline | Kokoro / Piper / dedizierte Sprachmodelle |
| **Watchdog / Sentinel** | **Sentinel** | *Strikte Stille* | **Keine Audio-Rechte** (weder Signalton noch Sprache) |

## 3. Das Verbot des "Bauchredners"
Host-Skripte und Watchdogs dürfen unter keinen Umständen Sprachsynthese-Werkzeuge wie `espeak` ansteuern, um Sprachnachrichten für Friday zu simulieren. Gesprochene Sprache ist das exklusive Identitätsmerkmal von Friday.

## 4. Verknüpfungen
- [[sentinel-architektur]]
- [[god-mode-tui]]
- [[system-architecture-map]]
- [[system-topologie]]
