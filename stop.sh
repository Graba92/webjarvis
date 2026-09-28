#!/usr/bin/env bash
# ==============================================================================
# J.A.R.V.I.S. AI OS — System Shutdown & Stop Utility
# Beendet Backend, Frontend und Docker-Container sauber
# ==============================================================================

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BOLD='\033[1m'
RESET='\033[0m'

echo -e "${CYAN}${BOLD}[*] Fahre J.A.R.V.I.S. AI OS herunter...${RESET}"

# 1. Beende Python Backend (Port 8765 oder server.py)
BACKEND_PIDS=$(pgrep -f "[s]erver\.py" 2>/dev/null || true)
if [ -n "$BACKEND_PIDS" ]; then
    echo -e "  • Beende Python Backend (PID: $BACKEND_PIDS)..."
    kill $BACKEND_PIDS 2>/dev/null || true
    sleep 0.5
    kill -9 $BACKEND_PIDS 2>/dev/null || true
    echo -e "  ${GREEN}✓${RESET} Backend beendet."
else
    echo -e "  • Kein laufendes Backend gefunden."
fi

# Ports 8765 freigeben falls belegt
if command -v fuser >/dev/null 2>&1; then
    fuser -k 8765/tcp 2>/dev/null || true
fi

# 2. Beende Next.js Frontend (Port 3000 / 3005)
if command -v fuser >/dev/null 2>&1; then
    fuser -k 3000/tcp 2>/dev/null || true
    fuser -k 3005/tcp 2>/dev/null || true
fi
FRONTEND_PIDS=$(pgrep -f "next-(dev|start|server)" 2>/dev/null || true)
if [ -n "$FRONTEND_PIDS" ]; then
    echo -e "  • Beende Next.js Frontend (PID: $FRONTEND_PIDS)..."
    kill $FRONTEND_PIDS 2>/dev/null || true
    sleep 0.5
    kill -9 $FRONTEND_PIDS 2>/dev/null || true
    echo -e "  ${GREEN}✓${RESET} Frontend beendet."
fi

# 3. Docker-Container stoppen
if command -v docker >/dev/null 2>&1; then
    if [ -f "$SCRIPT_DIR/docker-compose.yml" ]; then
        if docker compose -f "$SCRIPT_DIR/docker-compose.yml" ps -q 2>/dev/null | grep -q .; then
            echo -e "  • Stoppe Docker-Container..."
            docker compose -f "$SCRIPT_DIR/docker-compose.yml" stop 2>/dev/null || true
            echo -e "  ${GREEN}✓${RESET} Docker-Container gestoppt."
        fi
    fi
fi

echo -e "\n${GREEN}${BOLD}✓ J.A.R.V.I.S. AI OS erfolgreich gestoppt.${RESET}"
