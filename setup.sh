#!/usr/bin/env bash
# ==============================================================================
# J.A.R.V.I.S. AI OS — Universal Setup & Dependency Installer
# Unterstützt CachyOS / Arch Linux (pacman/yay), Debian/Ubuntu & Fedora
# Blueprint by Matthias Haase (Graba92)
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
WHATSAPP_DIR="$BACKEND_DIR/whatsapp_bridge"
VENV_DIR="$BACKEND_DIR/.venv"

# ── Farben für lesbare Terminal-Ausgabe ───────────────────────────────────────
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BOLD='\033[1m'
RESET='\033[0m'

echo -e "${BOLD}${CYAN}=== [J.A.R.V.I.S. AI OS — Automated Setup Installer] ===${RESET}\n"

# ── 1. Paketmanager & Systempakete prüfen ────────────────────────────────────
install_system_deps() {
    echo -e "${CYAN}[*] Prüfe System-Paketmanager & Hardware-Tools...${RESET}"
    if command -v pacman >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${RESET} Arch / CachyOS erkannt."
        PACKAGES=(nodejs npm python python-pip pipewire pipewire-pulse brightnessctl networkmanager bubblewrap libnotify)
        MISSING=()
        for pkg in "${PACKAGES[@]}"; do
            if ! pacman -Qi "$pkg" >/dev/null 2>&1 && ! command -v "$pkg" >/dev/null 2>&1; then
                MISSING+=("$pkg")
            fi
        done
        if [ ${#MISSING[@]} -gt 0 ]; then
            echo -e "  ${YELLOW}!${RESET} Fehlende Pakete: ${MISSING[*]}"
            echo -e "  ${CYAN}Installiere via 'sudo pacman -S --needed' (Passwortabfrage)...${RESET}"
            sudo pacman -S --needed --noconfirm "${MISSING[@]}" || true
        else
            echo -e "  ${GREEN}✓${RESET} Alle Basis-Systempakete sind vorhanden."
        fi
    elif command -v apt-get >/dev/null 2>&1; then
        echo -e "  ${YELLOW}!${RESET} Debian/Ubuntu erkannt. Bitte sicherstellen, dass nodejs, npm, python3-venv, pipewire und bubblewrap installiert sind."
    fi
}

# ── 2. Konfigurationsdateien vorbereiten ──────────────────────────────────────
setup_configs() {
    echo -e "\n${CYAN}[*] Initialisiere Konfigurationsdateien...${RESET}"
    if [ ! -f "$SCRIPT_DIR/.env" ] && [ -f "$SCRIPT_DIR/.env.example" ]; then
        cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
        echo -e "  ${GREEN}✓${RESET} .env aus Vorlage erstellt."
    fi

    if [ ! -f "$BACKEND_DIR/config/api_keys.json" ] && [ -f "$BACKEND_DIR/config/api_keys.example.json" ]; then
        cp "$BACKEND_DIR/config/api_keys.example.json" "$BACKEND_DIR/config/api_keys.json"
        echo -e "  ${GREEN}✓${RESET} backend/config/api_keys.json initialisiert."
    fi

    if [ ! -f "$BACKEND_DIR/config/contacts.json" ] && [ -f "$BACKEND_DIR/config/contacts.example.json" ]; then
        cp "$BACKEND_DIR/config/contacts.example.json" "$BACKEND_DIR/config/contacts.json"
        echo -e "  ${GREEN}✓${RESET} backend/config/contacts.json initialisiert."
    fi
}

# ── 3. Python Virtual Environment & Requirements ─────────────────────────────
setup_python_env() {
    echo -e "\n${CYAN}[*] Richte Python Virtual Environment ein ($VENV_DIR)...${RESET}"
    if [ ! -f "$VENV_DIR/bin/python3" ]; then
        python3 -m venv "$VENV_DIR"
        echo -e "  ${GREEN}✓${RESET} Virtual Environment erfolgreich angelegt."
    fi

    echo -e "  ${CYAN}• Installiere / aktualisiere Python-Abhängigkeiten via pip...${RESET}"
    "$VENV_DIR/bin/pip" install --upgrade pip >/dev/null
    "$VENV_DIR/bin/pip" install -r "$BACKEND_DIR/requirements.txt"
    echo -e "  ${GREEN}✓${RESET} Python-Abhängigkeiten erfolgreich installiert."
}

# ── 4. Frontend & WhatsApp Bridge Abhängigkeiten ──────────────────────────────
setup_node_deps() {
    echo -e "\n${CYAN}[*] Installiere Frontend Node-Pakete (Next.js 15 / Three.js)...${RESET}"
    if [ -d "$FRONTEND_DIR" ]; then
        (cd "$FRONTEND_DIR" && npm install)
        echo -e "  ${GREEN}✓${RESET} Frontend-Abhängigkeiten bereit."
    fi

    if [ -d "$WHATSAPP_DIR" ]; then
        echo -e "\n${CYAN}[*] Installiere WhatsApp Gateway Abhängigkeiten (Baileys)...${RESET}"
        (cd "$WHATSAPP_DIR" && npm install)
        echo -e "  ${GREEN}✓${RESET} WhatsApp-Bridge Abhängigkeiten bereit."
    fi
}

# ── 5. Ausführungsrechte für Skripte vergeben ─────────────────────────────────
make_executables() {
    echo -e "\n${CYAN}[*] Setze Ausführungsrechte auf Starter-Skripte...${RESET}"
    chmod +x "$SCRIPT_DIR/start.sh" "$SCRIPT_DIR/terminate_jarvis.sh" "$SCRIPT_DIR/setup.sh" 2>/dev/null || true
    if [ -f "$BACKEND_DIR/discord_bridge/start_discord.sh" ]; then
        chmod +x "$BACKEND_DIR/discord_bridge/start_discord.sh" 2>/dev/null || true
    fi
    echo -e "  ${GREEN}✓${RESET} Berechtigungen gesetzt."
}

# ── Ausführung ───────────────────────────────────────────────────────────────
install_system_deps
setup_configs
setup_python_env
setup_node_deps
make_executables

echo -e "\n${BOLD}${GREEN}======================================================${RESET}"
echo -e "${BOLD}${GREEN}✓ Installation erfolgreich abgeschlossen!${RESET}"
echo -e "Starte das Gesamtsystem jetzt mit: ${BOLD}./start.sh${RESET}"
echo -e "${BOLD}${GREEN}======================================================${RESET}\n"
