# Konzept: Voice-to-Text via Keybinding

## Ziel
Erstellung eines Systems, das auf Knopfdruck (`Alt+A`) Sprache aufnimmt, in Text umwandelt und an der aktuellen Cursorposition einfügt.

## Benötigte Komponenten (Linux/Arch)

1.  **Keybinding Manager:** `KDE Global Shortcuts` oder `bindsym` (für i3/sway). Triggert das Aufnahmeskript.
2.  **Audio Ingest:** `pipewire` (pw-record) oder `sox` (rec) zur Aufnahme der Sprache.
3.  **Speech-to-Text (STT) Engine:** `whisper.cpp` (lokal) oder OpenAI API (online) zur Konvertierung.
4.  **Input Simulation:** `xdotool` (X11) oder `ydotool`/`wtype` (Wayland) zum Einfügen des Texts.

## Logischer Workflow
`Keypress (Alt+A)` -> `Start Recording` -> `User speaks` -> `Stop Recording` -> `Run STT Enigne on Audio Code` -> `Simulate Keystrokes with Output Text`.
