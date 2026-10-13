#!/usr/bin/env bash
# ==============================================================================
# J.A.R.V.I.S. AI OS — Linux Master Orchestrator
# Koordiniert Backend (Python Gemini Live), Frontend (Next.js 15), Sandbox & Docker
# Blueprint by Matthias Haase (Graba92)
# ==============================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
VENV_PYTHON="$BACKEND_DIR/.venv/bin/python3"
SANDBOX_CONFIG_FILE="$BACKEND_DIR/config/sandbox_config.json"

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

# ── Sandbox-Verzeichnis Verwaltung ───────────────────────────────────────────
get_primary_sandbox_path() {
    if [ -n "${JARVIS_WORKSPACE:-}" ]; then
        echo "$JARVIS_WORKSPACE"
        return 0
    fi

    if [ -f "$SANDBOX_CONFIG_FILE" ]; then
        local p
        p=$(python3 -c "
import json
try:
    d = json.load(open('$SANDBOX_CONFIG_FILE'))
    paths = d.get('allowed_paths', [])
    if paths: print(paths[0])
    else: print('')
except:
    print('')
" 2>/dev/null || true)
        if [ -n "$p" ]; then
            echo "$p"
            return 0
        fi
    fi

    echo "$HOME/Schreibtisch/jarvistestlauf"
}

set_sandbox_path() {
    local target_path="${1:-}"
    if [ -z "$target_path" ]; then
        return 1
    fi

    # Tilde und relative Pfade auflösen
    target_path="${target_path/#\~/$HOME}"
    target_path="$(mkdir -p "$target_path" && cd "$target_path" && pwd)"

    export JARVIS_WORKSPACE="$target_path"
    export JARVIS_SANDBOX_PATH="$target_path"

    mkdir -p "$BACKEND_DIR/config"
    python3 -c "
import json
from pathlib import Path
cfg_file = Path('$SANDBOX_CONFIG_FILE')
cfg = {'allowed_paths': []}
if cfg_file.exists():
    try: cfg = json.loads(cfg_file.read_text(encoding='utf-8'))
    except: pass
paths = cfg.get('allowed_paths', [])
if '$target_path' not in paths:
    paths.insert(0, '$target_path')
cfg['allowed_paths'] = paths
cfg_file.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding='utf-8')
" 2>/dev/null || true

    echo -e "${GREEN}[✓] Sandbox-Arbeitsbereich erfolgreich gesetzt auf:${RESET} ${BOLD}$target_path${RESET}"
    echo -e "    (Jarvis kann darin und in allen Unterordnern lesen und schreiben)\n"
}

configure_sandbox_workspace() {
    echo -e "\n${BOLD}${CYAN}[*] Konfiguration der Sandbox & Arbeitsverzeichnisse...${RESET}"
    local current_p
    current_p=$(get_primary_sandbox_path)
    echo -e "Aktueller Haupt-Arbeitsbereich: ${GREEN}${BOLD}$current_p${RESET}"
    if [ -f "$SANDBOX_CONFIG_FILE" ]; then
        echo -e "Alle freigegebenen Pfade:"
        python3 -c "
import json
try:
    d = json.load(open('$SANDBOX_CONFIG_FILE'))
    for idx, p in enumerate(d.get('allowed_paths', []), 1):
        print(f'   {idx}) {p}')
except Exception as e:
    print(f'   Fehler beim Lesen: {e}')
" 2>/dev/null || true
    fi

    echo -e "\nOptionen:"
    echo -e "  1) Neuen Pfad eingeben oder als Haupt-Arbeitsbereich setzen"
    echo -e "  2) Pfad aus Sandbox entfernen"
    echo -e "  3) Zurück"
    echo -ne "${BOLD}Wähle [1-3] (Standard: 1): ${RESET}"
    read -r SB_CHOICE

    case "$SB_CHOICE" in
        2)
            echo -ne "Pfad oder Teilstring zum Entfernen eingeben: "
            read -r REMOVE_PATH
            if [ -n "$REMOVE_PATH" ]; then
                python3 -c "
import json
from pathlib import Path
cfg_file = Path('$SANDBOX_CONFIG_FILE')
if cfg_file.exists():
    d = json.loads(cfg_file.read_text())
    orig = d.get('allowed_paths', [])
    d['allowed_paths'] = [p for p in orig if '$REMOVE_PATH' not in p]
    cfg_file.write_text(json.dumps(d, indent=2))
" 2>/dev/null || true
                echo -e "${GREEN}[✓] Pfad entfernt.${RESET}"
            fi
            ;;
        3)
            return 0
            ;;
        *)
            echo -ne "Gib den absoluten oder relativen Pfad ein (z.B. ~/workspace oder ./sandbox_workspace): "
            read -r INPUT_PATH
            if [ -n "$INPUT_PATH" ]; then
                set_sandbox_path "$INPUT_PATH"
            fi
            ;;
    esac
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
        KEY_JSON=$(python3 -c "
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
        echo -e "${CYAN}Für die Sprach- und KI-Funktionen wird ein Google Gemini API Key benötigt.${RESET}"
        echo -e "Kostenlos erhalten unter: ${BOLD}https://aistudio.google.com/app/apikey${RESET}\n"
        echo -ne "${BOLD}Bitte gib deinen GEMINI_API_KEY ein (oder Enter für Standby): ${RESET}"
        read -r KEY_INPUT
        if [ -n "$KEY_INPUT" ]; then
            export GEMINI_API_KEY="$KEY_INPUT"
            echo "GEMINI_API_KEY=$KEY_INPUT" > "$SCRIPT_DIR/.env"
            echo "GEMINI_API_KEY=$KEY_INPUT" > "$BACKEND_DIR/.env"
            python3 -c "
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

    local current_ws
    current_ws=$(get_primary_sandbox_path)
    echo -e "  ${GREEN}✓${RESET} Sandbox-Arbeitsbereich: $current_ws (Vollzugriff R/W + Subdirs)"

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

    if command -v bwrap >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${RESET} Bubblewrap Sandbox (bwrap): Verfügbar"
    else
        echo -e "  ${YELLOW}!${RESET} bwrap nicht gefunden (Sandbox im Fallback-Modus)."
    fi

    if command -v docker >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${RESET} Docker Engine: $(docker --version 2>/dev/null | cut -d',' -f1)"
    fi

    echo -e "\n${GREEN}[✓] Systemprüfung abgeschlossen.${RESET}"
}

# ── Start-Routinen ──────────────────────────────────────────────────────────
start_backend() {
    ensure_venv
    ensure_api_key
    local current_ws
    current_ws=$(get_primary_sandbox_path)
    export JARVIS_WORKSPACE="$current_ws"
    export JARVIS_SANDBOX_PATH="$current_ws"

    echo -e "\n${BOLD}${CYAN}[*] Starte Python Gemini Live WebSocket Backend (ws://127.0.0.1:8765)...${RESET}"
    echo -e "  ${CYAN}• Sandbox-Arbeitsbereich: ${BOLD}$current_ws${RESET}"
    export PYTHONPATH="$BACKEND_DIR:${PYTHONPATH:-}"
    exec "$VENV_PYTHON" "$BACKEND_DIR/server.py"
}

start_frontend() {
    echo -e "\n${BOLD}${CYAN}[*] Starte Next.js 15 WebGL HUD Frontend (http://localhost:3000)...${RESET}"
    cd "$FRONTEND_DIR"
    if [ ! -d "node_modules" ]; then
        npm install --no-fund --no-audit --loglevel=error > /dev/null
    fi
    exec npm run dev
}

start_all() {
    ensure_venv
    ensure_api_key
    local current_ws
    current_ws=$(get_primary_sandbox_path)
    export JARVIS_WORKSPACE="$current_ws"
    export JARVIS_SANDBOX_PATH="$current_ws"

    echo -e "\n${BOLD}${GREEN}[*] Starte J.A.R.V.I.S. AI OS Core (Backend + Frontend HUD)...${RESET}"
    echo -e "  ${CYAN}• Sandbox-Arbeitsbereich: ${BOLD}$current_ws${RESET}"
    
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
        npm install --no-fund --no-audit --loglevel=error > /dev/null
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
        python3 -c "
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

# ── Argumenten-Parsing ───────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        -w|--workspace|--sandbox-path)
            if [ -n "${2:-}" ]; then
                set_sandbox_path "$2"
                shift 2
            else
                echo -e "${RED}Fehler: Kein Pfad nach $1 angegeben.${RESET}"
                exit 1
            fi
            ;;
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
            echo "Verwendung: ./start.sh [OPTIONEN]"
            echo "Optionen:"
            echo "  -w, --workspace PFAD  Setzt den erlaubten Sandbox-Arbeitsbereich für Jarvis"
            echo "  -a, --all, --apply    Startet Gesamtsystem nativ (Backend + Frontend HUD)"
            echo "  -b, --backend         Startet nur das Python Gemini Live WebSocket Backend"
            echo "  -f, --frontend        Startet nur das Next.js 15 3D WebGL Frontend"
            echo "  -c, --check           Führt System- & Hardware-Prüfungen aus"
            echo "  -h, --help            Zeigt diese Hilfe an"
            exit 0
            ;;
        *)
            echo -e "${RED}Unbekannte Option: $1${RESET}"
            exit 1
            ;;
    esac
done

# ── Interaktives Menü ────────────────────────────────────────────────────────
while true; do
    clear
    banner
    CURRENT_WS=$(get_primary_sandbox_path)
    echo -e "${BOLD}${CYAN}   1)${RESET} Gesamtsystem starten (Backend + Frontend HUD)"
    echo -e "${BOLD}${CYAN}   2)${RESET} Nur Python Backend starten (Gemini Live WebSocket)"
    echo -e "${BOLD}${CYAN}   3)${RESET} Nur Next.js Frontend starten (Three.js 3D WebGL HUD)"
    echo -e "${BOLD}${CYAN}   4)${RESET} Sandbox-Arbeitsbereich festlegen / anpassen"
    echo -e "      ${MAGENTA}↳ Aktiv: ${BOLD}$CURRENT_WS${RESET}"
    echo -e "${BOLD}${CYAN}   5)${RESET} Hardware- & Systemprüfung ausführen"
    echo -e "${BOLD}${CYAN}   6)${RESET} Gemini API Key konfigurieren"
    echo -e "${BOLD}${CYAN}   7)${RESET} Beenden"
    echo -e "${BLUE}──────────────────────────────────────────────────────────────────────────────${RESET}"
    echo -ne "${BOLD}Wähle eine Option [1-7]: ${RESET}"
    read -r CHOICE

    case "$CHOICE" in
        1) start_all ;;
        2) start_backend ;;
        3) start_frontend ;;
        4) configure_sandbox_workspace; echo -ne "\nDrücke Enter zum Fortfahren..."; read -r ;;
        5) check_system; echo -ne "\nDrücke Enter zum Fortfahren..."; read -r ;;
        6) configure_env; echo -ne "\nDrücke Enter zum Fortfahren..."; read -r ;;
        7|q|Q) echo -e "\n${CYAN}J.A.R.V.I.S. beendet. Bis bald, Operator.${RESET}"; exit 0 ;;
        *) echo -e "\n${RED}Ungültige Eingabe.${RESET}"; sleep 1 ;;
    esac
done
