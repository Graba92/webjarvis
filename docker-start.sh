#!/usr/bin/env bash
# ==============================================================================
# WebJarvis Docker Test Orchestrator
# Startet WebJarvis im isolierten Docker-Container-Verbund
# ==============================================================================
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "\033[1;36m====================================================\033[0m"
echo -e "\033[1;32m  🚀 STARTE WEBJARVIS DOCKER TESTUMGEBUNG\033[0m"
echo -e "\033[1;36m====================================================\033[0m"

# Verzeichnisse anlegen falls nötig
mkdir -p data/lancedb data/logs data/whatsapp_auth

# Optional: WhatsApp Bridge mit --full starten
PROFILE_ARG=""
if [[ "${1:-}" == "--full" ]]; then
  echo -e "\033[1;33m[+] Starte mit vollem Profil inkl. WhatsApp Bridge\033[0m"
  PROFILE_ARG="--profile full"
fi

# Build & Start via Docker Compose
docker compose $PROFILE_ARG up -d --build

echo -e "\n\033[1;32m[✓] WebJarvis Docker-Container erfolgreich gestartet!\033[0m"
echo -e "\033[1;34m----------------------------------------------------\033[0m"
echo -e "  🌐 \033[1;37mWebJarvis HUD Cockpit:\033[0m  \033[1;32mhttp://localhost:3005\033[0m"
echo -e "  ⚡ \033[1;37mBackend WebSocket:\033[0m      \033[1;32mws://127.0.0.1:8765\033[0m"
echo -e "  📊 \033[1;37mPortainer Dashboard:\033[0m    \033[1;32mhttps://localhost:9443\033[0m"
echo -e "\033[1;34m----------------------------------------------------\033[0m"
echo -e "Logs ansehen: \033[1;33m./docker-logs.sh\033[0m | Stoppen: \033[1;31m./docker-stop.sh\033[0m\n"
