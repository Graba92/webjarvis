#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "\033[1;33m[*] Stoppe WebJarvis Docker-Container...\033[0m"
docker compose --profile full down
echo -e "\033[1;32m[✓] Alle WebJarvis Container gestoppt.\033[0m"
