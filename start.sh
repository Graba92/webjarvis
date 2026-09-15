#!/usr/bin/env bash
# ==============================================================================
# J.A.R.V.I.S. AI OS — Linux Master Orchestrator
# Koordiniert Backend (Python Gemini Live), Frontend (Next.js 15), WhatsApp & Discord
# Blueprint by Matthias Haase (Graba92)
# ==============================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
VENV_PYTHON="$BACKEND_DIR/.venv/bin/python3"

# ── Farbcodes ────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# ── Banner ───────────────────────────────────────────────────────────────────
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
    echo -e "${BOLD}${CYAN}   J.A.R.V.I.S. AI Operating System  —  Desktop Edition${RESET}"
    echo -e "${MAGENTA}   Created by Matthias Haase (Graba92)${RESET}"
    echo -e "${BLUE}──────────────────────────────────────────────────────────────────────────────${RESET}"
}

# ── API Key Prüfung & Speicherung ───────────────────────────────────────────
ensure_api_key() {
    if [ -n "${GEMINI_API_KEY:-}" ]; then
        return 0
    fi

    if [ -f "$SCRIPT_DIR/.env" ]; then
        export $(grep -E '^GEMINI_API_KEY=' "$SCRIPT_DIR/.env" | xargs) 2>/dev/null || true
    fi
    if [ -z "${GEMINI_API_KEY:-}" ] && [ -f "$BACKEND_DIR/.env" ]; then
        export $(grep -E '^GEMINI_API_KEY=' "$BACKEND_DIR/.env" | xargs) 2>/dev/null || true
    fi

    if [ -z "${GEMINI_API_KEY:-}" ] && [ -f "$BACKEND_DIR/config/api_keys.json" ]; then
        KEY_JSON=$("$VENV_PYTHON" -c "
import json
try:
    d = json.load(open('$BACKEND_DIR/config/api_keys.json'))
    print(d.get('gemini_api_key') or d.get('GEMINI_API_KEY') or '')
except:
    print('')
" 2>/dev/null || true)
        if [ -n "$KEY_JSON" ]; then
            export GEMINI_API_KEY="$KEY_JSON"
        fi
    fi

    if [ -z "${GEMINI_API_KEY:-}" ]; then
        echo -e "\n${YELLOW}[!] Kein GEMINI_API_KEY gefunden.${RESET}"
        echo -e "${CYAN}Für die Sprach- und KI-Funktionen (gemini-3.1-flash-live-preview) wird ein Google Gemini API Key benötigt.${RESET}"
        echo -e "Kostenlos erhalten unter: ${BOLD}https://aistudio.google.com/app/apikey${RESET}\n"
        echo -ne "${BOLD}Bitte gib deinen GEMINI_API_KEY ein (oder Enter für Standby): ${RESET}"
        read -r KEY_INPUT
        if [ -n "$KEY_INPUT" ]; then
            export GEMINI_API_KEY="$KEY_INPUT"
            echo "GEMINI_API_KEY=$KEY_INPUT" > "$SCRIPT_DIR/.env"
            echo "GEMINI_API_KEY=$KEY_INPUT" > "$BACKEND_DIR/.env"
            "$VENV_PYTHON" -c "
import json
from pathlib import Path
p = Path('$BACKEND_DIR/config/api_keys.json')
p.parent.mkdir(parents=True, exist_ok=True)
d = {}
if p.exists():
    try: d = json.loads(p.read_text())
    except: pass
d['gemini_api_key'] = '$KEY_INPUT'
p.write_text(json.dumps(d, indent=2))
" 2>/dev/null || true
            echo -e "${GREEN}[✓] API Key persistent in .env und config/api_keys.json gespeichert.${RESET}\n"
        else
            echo -e "${YELLOW}[!] Standby-Modus aktiv. Key kann jederzeit im HUD nachgetragen werden.${RESET}\n"
        fi
    fi
}

# ── Virtual Environment Absicherung ─────────────────────────────────────────
ensure_venv() {
    if [ ! -f "$VENV_PYTHON" ]; then
        echo -e "  ${YELLOW}!${RESET} Erstelle Python Virtual Environment..."
        python3 -m venv "$BACKEND_DIR/.venv"
        "$BACKEND_DIR/.venv/bin/pip" install --upgrade pip >/dev/null 2>&1 || true
        "$BACKEND_DIR/.venv/bin/pip" install -r "$BACKEND_DIR/requirements.txt"
    fi
}

# ── System- & Hardware-Check ────────────────────────────────────────────────
check_system() {
    echo -e "\n${BOLD}${CYAN}[*] Prüfe Systemvoraussetzungen...${RESET}"
    
    ensure_venv
    echo -e "  ${GREEN}✓${RESET} Python Virtual Environment: ${BACKEND_DIR}/.venv"

    ensure_api_key
    if [ -n "${GEMINI_API_KEY:-}" ]; then
        MASKED="${GEMINI_API_KEY:0:6}...${GEMINI_API_KEY: -4}"
        echo -e "  ${GREEN}✓${RESET} Gemini Live API Key: Konfiguriert ($MASKED)"
    else
        echo -e "  ${YELLOW}!${RESET} Gemini Live API Key: Nicht konfiguriert (Standby-Modus)"
    fi

    if command -v node >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${RESET} Node.js: $(node -v) (NPM: $(npm -v))"
    else
        echo -e "  ${RED}✗ Node.js nicht gefunden. Bitte installieren.${RESET}"
    fi

    if command -v pactl >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${RESET} PipeWire Audio (pactl): Verfügbar"
    else
        echo -e "  ${YELLOW}!${RESET} pactl nicht im PATH."
    fi

    if command -v brightnessctl >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${RESET} Display-Helligkeit (brightnessctl): Verfügbar"
    else
        echo -e "  ${YELLOW}!${RESET} brightnessctl nicht installiert."
    fi

    if command -v nmcli >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${RESET} Netzwerk-Manager (nmcli): Verfügbar"
    else
        echo -e "  ${YELLOW}!${RESET} nmcli nicht gefunden."
    fi

    if [ -d "$WHATSAPP_DIR/auth_info_baileys" ]; then
        echo -e "  ${GREEN}✓${RESET} WhatsApp Multi-Device Bridge: Gekoppelt (Session aktiv)"
    elif [ -d "$WHATSAPP_DIR" ]; then
        echo -e "  ${YELLOW}!${RESET} WhatsApp Multi-Device Bridge: Bereit (QR-Pairing erforderlich)"
    fi

    if [ -f "$SCRIPT_DIR/.env" ] && grep -q '^DISCORD_BOT_TOKEN=' "$SCRIPT_DIR/.env" 2>/dev/null; then
        echo -e "  ${GREEN}✓${RESET} Discord Gateway Bridge: Konfiguriert"
    elif [ -d "$DISCORD_DIR" ]; then
        echo -e "  ${YELLOW}!${RESET} Discord Gateway Bridge: Bereit"
    fi

    if command -v bwrap >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${RESET} Bubblewrap Sandbox (bwrap): Verfügbar"
    else
        echo -e "  ${YELLOW}!${RESET} bwrap nicht gefunden (Sandbox im Fallback-Modus)."
    fi

    if [ -f "$BACKEND_DIR/config/cron_jobs.json" ]; then
        echo -e "  ${GREEN}✓${RESET} Proaktive Cron-Engine: Konfiguriert (HEARTBEAT aktiv)"
    fi

    echo -e "\n${GREEN}[✓] Systemprüfung abgeschlossen.${RESET}"
}

# ── Start-Routinen ──────────────────────────────────────────────────────────
start_backend() {
    ensure_venv
    ensure_api_key
    echo -e "\n${BOLD}${CYAN}[*] Starte Python Gemini Live WebSocket Backend (ws://127.0.0.1:8765)...${RESET}"
    export PYTHONPATH="$BACKEND_DIR:${PYTHONPATH:-}"
    exec "$VENV_PYTHON" "$BACKEND_DIR/server.py"
}

start_frontend() {
    echo -e "\n${BOLD}${CYAN}[*] Starte Next.js 15 WebGL HUD Frontend (http://localhost:3000)...${RESET}"
    cd "$FRONTEND_DIR"
    if [ ! -d "node_modules" ]; then
        npm install
    fi
    exec npm run dev
}

start_all() {
    ensure_venv
    ensure_api_key
    echo -e "\n${BOLD}${GREEN}[*] Starte J.A.R.V.I.S. AI OS Core (Backend + Frontend HUD)...${RESET}"
    
    export PYTHONPATH="$BACKEND_DIR:${PYTHONPATH:-}"
    "$VENV_PYTHON" "$BACKEND_DIR/server.py" &
    BACKEND_PID=$!
    echo -e "  ${CYAN}• Backend läuft unter PID $BACKEND_PID (ws://127.0.0.1:8765)${RESET}"

    cleanup() {
        echo -e "\n${YELLOW}[*] Fahre Subsysteme herunter...${RESET}"
        kill "$BACKEND_PID" 2>/dev/null || true
        exit 0
    }
    trap cleanup SIGINT SIGTERM EXIT

    cd "$FRONTEND_DIR"
    if [ ! -d "node_modules" ]; then
        npm install
    fi
    npm run dev
}

configure_env() {
    echo -e "\n${BOLD}${CYAN}[*] Konfiguration der Umgebung & Gemini API...${RESET}"
    if [ -n "${GEMINI_API_KEY:-}" ]; then
        echo -e "Aktueller Key: ${GREEN}${GEMINI_API_KEY:0:6}...${GEMINI_API_KEY: -4}${RESET}"
    else
        echo -e "Aktueller Key: ${YELLOW}Keiner hinterlegt${RESET}"
    fi
    
    echo -ne "Neuen Gemini API Key eingeben (Enter für unverändert): "
    read -r KEY_INPUT
    if [ -n "$KEY_INPUT" ]; then
        export GEMINI_API_KEY="$KEY_INPUT"
        echo "GEMINI_API_KEY=$KEY_INPUT" > "$SCRIPT_DIR/.env"
        echo "GEMINI_API_KEY=$KEY_INPUT" > "$BACKEND_DIR/.env"
        "$VENV_PYTHON" -c "
import json
from pathlib import Path
p = Path('$BACKEND_DIR/config/api_keys.json')
p.parent.mkdir(parents=True, exist_ok=True)
d = {}
if p.exists():
    try: d = json.loads(p.read_text())
    except: pass
d['gemini_api_key'] = '$KEY_INPUT'
p.write_text(json.dumps(d, indent=2))
" 2>/dev/null || true
        echo -e "${GREEN}[✓] Neuer API Key erfolgreich gespeichert!${RESET}"
    fi
}

case "${1:-}" in
    -a|--all|--apply)
        banner
        start_all
        exit 0
        ;;
    -b|--backend)
        banner
        start_backend
        exit 0
        ;;
    -f|--frontend)
        banner
        start_frontend
        exit 0
        ;;
    -c|--check)
        banner
        check_system
        exit 0
        ;;
    -h|--help)
        banner
        echo "Verwendung: ./start.sh [OPTION]"
        echo "Optionen:"
        echo "  -a, --all, --apply   Startet Gesamtsystem (Backend + Frontend HUD)"
        echo "  -b, --backend        Startet nur das Python Gemini Live WebSocket Backend"
        echo "  -f, --frontend       Startet nur das Next.js 15 3D WebGL Frontend"
        echo "  -c, --check          Führt System- & Hardware-Prüfungen aus"
        echo "  -h, --help           Zeigt diese Hilfe an"
        exit 0
        ;;
esac

while true; do
    clear
    banner
    echo -e "${BOLD}${CYAN}   1)${RESET} Gesamtsystem starten (Backend + Frontend HUD)"
    echo -e "${BOLD}${CYAN}   2)${RESET} Nur Python Backend starten (Gemini Live WebSocket)"
    echo -e "${BOLD}${CYAN}   3)${RESET} Nur Next.js Frontend starten (Three.js 3D WebGL HUD)"
    echo -e "${BOLD}${CYAN}   4)${RESET} Hardware- & Systemprüfung ausführen"
    echo -e "${BOLD}${CYAN}   5)${RESET} Gemini API Key konfigurieren"
    echo -e "${BOLD}${CYAN}   6)${RESET} Beenden"
    echo -e "${BLUE}──────────────────────────────────────────────────────────────────────────────${RESET}"
    echo -ne "${BOLD}Wähle eine Option [1-6]: ${RESET}"
    read -r CHOICE

    case "$CHOICE" in
        1) start_all ;;
        2) start_backend ;;
        3) start_frontend ;;
        4) check_system; echo -ne "\nDrücke Enter zum Fortfahren..."; read -r ;;
        5) configure_env; echo -ne "\nDrücke Enter zum Fortfahren..."; read -r ;;
        6|q|Q) echo -e "\n${CYAN}J.A.R.V.I.S. beendet. Bis bald, Operator.${RESET}"; exit 0 ;;
        *) echo -e "\n${RED}Ungültige Eingabe.${RESET}"; sleep 1 ;;
    esac
done
