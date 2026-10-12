#!/bin/bash
set -e

echo "Starte System-Check..."

DEPENDENCIES=(python ffmpeg pipewire-audio python-rich yt-dlp)
MISSING=()

for pkg in "${DEPENDENCIES[@]}"; do
    if ! pacman -Qi "$pkg" > /dev/null 2>&1; then
        echo "[!] $pkg fehlt."
        MISSING+=("$pkg")
    fi
done

if [ ${#MISSING[@]} -eq 0 ]; then
    echo "[+] Alle Abhängigkeiten vorhanden."
else
    echo "Installiere fehlende Pakete: ${MISSING[*]}"
    if command -v yay > /dev/null 2>&1; then
        yay -S --noconfirm "${MISSING[@]}"
    else
        sudo pacman -S --noconfirm "${MISSING[@]}"
    fi
fi

echo "[+] Setup abgeschlossen."
