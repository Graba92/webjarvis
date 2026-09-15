#!/usr/bin/env bash
# ==============================================================================
# J.A.R.V.I.S. Discord Bridge Starter — CachyOS / Arch Edition
# Steuerung und Gateway für den J.A.R.V.I.S. Discord Bot
# Made by Matthias Haase (Graba92)
# ==============================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_DIR="$(cd "$BACKEND_DIR/.." && pwd)"
VENV_PYTHON="$BACKEND_DIR/.venv/bin/python3"
START_SCRIPT="$PROJECT_DIR/start.sh"

# ── Farbcodes nach Konvention ────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# ── Banner-Funktion ──────────────────────────────────────────────────────────
banner() {
    echo -e "${CYAN}"
    cat << "BANNER_ART"
      ___   _____  ______      __ _____ _____       ____   _____ 
     / / \ |  __ \|  ____/\   / /|_   _/ ____|     / __ \ / ____|
    / / _ \| |__) | |__ /  \ / /   | || (___      | |  | | (___  
   / / ___ \  _  /|  __/ /\ \ /    | | \___ \     | |  | |\___ \ 
  / / /   \ \ | \ \| | / ____ \   _| |_ ____) | _  | |__| |____) |
 /_/_/   \_\_|  \_\_|/_/    \_\ |_____|_____/ (_)  \____/|_____/ 
BANNER_ART
    echo -e "${BOLD}${CYAN}   J.A.R.V.I.S. Discord Gateway Bridge  —  CachyOS / Arch Edition${RESET}"
    echo -e "${MAGENTA}   Made by Matze Graba & Chati${RESET}"
    echo -e "${BLUE}──────────────────────────────────────────────────────────────────────────────${RESET}"
}

# ── Environment & Token Prüfung ─────────────────────────────────────────────
ensure_env() {
    if [ -f "$PROJECT_DIR/.env" ]; then
        export $(grep -v '^#' "$PROJECT_DIR/.env" | xargs) 2>/dev/null || true
    fi
    if [ -f "$SCRIPT_DIR/.env" ]; then
        export $(grep -v '^#' "$SCRIPT_DIR/.env" | xargs) 2>/dev/null || true
    fi

    if [ -z "$DISCORD_BOT_TOKEN" ]; then
        if [ -f "$PROJECT_DIR/setup_discord_wizard.sh" ]; then
            echo -e "\n${YELLOW}[!] Kein DISCORD_BOT_TOKEN gefunden.${RESET}"
            echo -e "${CYAN}Starte den interaktiven Setup-Wizard zur schnellen Einrichtung...${RESET}"
            sleep 1
            exec bash "$PROJECT_DIR/setup_discord_wizard.sh"
        fi
        echo -e "\n${YELLOW}[!] Kein DISCORD_BOT_TOKEN gefunden.${RESET}"
        echo -e "${CYAN}Für den Discord-Bot wird ein Bot-Token aus dem Discord Developer Portal benötigt.${RESET}"
        echo -e "Erhalten unter: ${BOLD}https://discord.com/developers/applications${RESET}\n"
        echo -ne "${BOLD}Bitte gib deinen DISCORD_BOT_TOKEN ein: ${RESET}"
        read -r TOKEN_INPUT
        if [ -n "$TOKEN_INPUT" ]; then
            export DISCORD_BOT_TOKEN="$TOKEN_INPUT"
            echo "DISCORD_BOT_TOKEN=$TOKEN_INPUT" >> "$SCRIPT_DIR/.env"
            if [ -f "$PROJECT_DIR/.env" ] && ! grep -q "DISCORD_BOT_TOKEN" "$PROJECT_DIR/.env"; then
                echo "DISCORD_BOT_TOKEN=$TOKEN_INPUT" >> "$PROJECT_DIR/.env"
            fi
            echo -e "${GREEN}[✓] Discord Bot Token erfolgreich in .env gespeichert.${RESET}\n"
        else
            echo -e "${RED}[✗] Kein Token übergeben. Bot kann nicht gestartet werden.${RESET}\n"
            exit 1
        fi
    fi
}

# ── Abhängigkeiten prüfen ───────────────────────────────────────────────────
check_dependencies() {
    echo -e "\n${BOLD}${CYAN}[*] Prüfe Discord Bridge Voraussetzungen...${RESET}"
    
    if [ -f "$SCRIPT_DIR/.env" ]; then
        export $(grep -v '^#' "$SCRIPT_DIR/.env" | xargs) 2>/dev/null || true
    fi
    if [ -f "$PROJECT_DIR/.env" ]; then
        export $(grep -v '^#' "$PROJECT_DIR/.env" | xargs) 2>/dev/null || true
    fi
    
    if [ ! -f "$VENV_PYTHON" ]; then
        echo -e "  ${YELLOW}!${RESET} Python Virtual Environment fehlt. Erstelle venv..."
        python3 -m venv --system-site-packages "$BACKEND_DIR/.venv"
    fi
    echo -e "  ${GREEN}✓${RESET} Python venv: $VENV_PYTHON"

    # Prüfe discord.py
    if ! "$VENV_PYTHON" -c "import discord" 2>/dev/null; then
        echo -e "  ${YELLOW}!${RESET} discord.py fehlt im venv. Installiere..."
        "$VENV_PYTHON" -m pip install discord.py psutil websockets
    fi
    local DISC_VER=$("$VENV_PYTHON" -c "import discord; print(discord.__version__)" 2>/dev/null || echo "aktiv")
    echo -e "  ${GREEN}✓${RESET} discord.py Version: $DISC_VER"

    # Token prüfen
    if [ -n "$DISCORD_BOT_TOKEN" ]; then
        local MASKED="${DISCORD_BOT_TOKEN:0:6}...${DISCORD_BOT_TOKEN: -4}"
        echo -e "  ${GREEN}✓${RESET} Discord Bot Token: Hinterlegt ($MASKED)"
    else
        echo -e "  ${YELLOW}!${RESET} Discord Bot Token: Nicht hinterlegt"
    fi

    # J.A.R.V.I.S. Core WebSocket prüfen
    local WS_PORT="${JARVIS_WS_PORT:-8765}"
    if command -v ss >/dev/null 2>&1 && ss -tuln | grep -q ":$WS_PORT "; then
        echo -e "  ${GREEN}✓${RESET} J.A.R.V.I.S. WebSocket Core (Port $WS_PORT): ONLINE"
    else
        echo -e "  ${YELLOW}!${RESET} J.A.R.V.I.S. WebSocket Core (Port $WS_PORT): OFFLINE (kann über Bot via /start gestartet werden)"
    fi

    echo -e "\n${GREEN}[✓] Voraussetzungsprüfung abgeschlossen.${RESET}"
}

# ── Bot starten ─────────────────────────────────────────────────────────────
start_bot() {
    ensure_env
    echo -e "\n${BOLD}${CYAN}[*] Starte J.A.R.V.I.S. Discord Bridge Bot...${RESET}"
    exec "$VENV_PYTHON" "$SCRIPT_DIR/discord_bot.py"
}

# ── Token konfigurieren ─────────────────────────────────────────────────────
configure_token() {
    echo -e "\n${BOLD}${CYAN}[*] Discord Bot Token konfigurieren...${RESET}"
    if [ -n "$DISCORD_BOT_TOKEN" ]; then
        echo -e "Aktueller Token: ${GREEN}${DISCORD_BOT_TOKEN:0:6}...${DISCORD_BOT_TOKEN: -4}${RESET}"
    else
        echo -e "Aktueller Token: ${YELLOW}Keiner hinterlegt${RESET}"
    fi

    echo -ne "Neuen Discord Bot Token eingeben (Enter für unverändert): "
    read -r NEW_TOKEN
    if [ -n "$NEW_TOKEN" ]; then
        export DISCORD_BOT_TOKEN="$NEW_TOKEN"
        # Aktualisiere in .env
        sed -i '/^DISCORD_BOT_TOKEN=/d' "$SCRIPT_DIR/.env" 2>/dev/null || true
        echo "DISCORD_BOT_TOKEN=$NEW_TOKEN" >> "$SCRIPT_DIR/.env"
        if [ -f "$PROJECT_DIR/.env" ]; then
            sed -i '/^DISCORD_BOT_TOKEN=/d' "$PROJECT_DIR/.env" 2>/dev/null || true
            echo "DISCORD_BOT_TOKEN=$NEW_TOKEN" >> "$PROJECT_DIR/.env"
        fi
        echo -e "${GREEN}[✓] Neuer Token erfolgreich gespeichert!${RESET}"
    fi
}

# ── CLI Parameter ───────────────────────────────────────────────────────────
case "$1" in
    -a|--apply|-s|--start)
        banner
        start_bot
        exit 0
        ;;
    -c|--check)
        banner
        check_dependencies
        exit 0
        ;;
    -h|--help)
        banner
        echo "Verwendung: ./start_discord.sh [OPTION]"
        echo "Optionen:"
        echo "  -a, --apply, -s, --start   Startet den Discord Gateway Bot direkt"
        echo "  -c, --check                Führt Abhängigkeits- und Systemprüfungen durch"
        echo "  -h, --help                 Zeigt diese Hilfe an"
        exit 0
        ;;
esac

# ── Interaktives TUI-Menü ───────────────────────────────────────────────────
while true; do
    clear
    banner
    echo -e "${BOLD}${CYAN}   1)${RESET} Discord Bot starten"
    echo -e "${BOLD}${CYAN}   2)${RESET} Abhängigkeiten & Status prüfen"
    echo -e "${BOLD}${CYAN}   3)${RESET} Vollständigen Setup-Wizard starten (Portal-Guide & Invite-Link)"
    echo -e "${BOLD}${CYAN}   4)${RESET} J.A.R.V.I.S. Gesamtsystem via start.sh starten"
    echo -e "${BOLD}${CYAN}   5)${RESET} Beenden"
    echo -e "${BLUE}──────────────────────────────────────────────────────────────────────────────${RESET}"
    echo -ne "${BOLD}Wähle eine Option [1-5]: ${RESET}"
    read -r CHOICE

    case "$CHOICE" in
        1) start_bot ;;
        2) check_dependencies; echo -ne "\nDrücke Enter zum Fortfahren..."; read -r ;;
        3) 
            if [ -f "$PROJECT_DIR/setup_discord_wizard.sh" ]; then
                bash "$PROJECT_DIR/setup_discord_wizard.sh"
            else
                configure_token
            fi
            echo -ne "\nDrücke Enter zum Fortfahren..."; read -r
            ;;
        4) 
            if [ -f "$START_SCRIPT" ]; then
                bash "$START_SCRIPT" -a
            else
                echo -e "${RED}[✗] start.sh nicht gefunden unter $START_SCRIPT${RESET}"
                sleep 2
            fi
            ;;
        5|q|Q) echo -e "\n${CYAN}Bis bald, Matze.${RESET}"; exit 0 ;;
        *) echo -e "\n${RED}Ungültige Eingabe.${RESET}"; sleep 1 ;;
    esac
done
