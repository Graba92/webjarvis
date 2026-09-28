#!/usr/bin/env bash
# ==============================================================================
# J.A.R.V.I.S. AI OS — Graceful Tool Restart Utility (restart.sh)
# Startet ausschließlich J.A.R.V.I.S. (Backend & Frontend) neu, NICHT das gesamte OS.
# ==============================================================================

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[*] Starte J.A.R.V.I.S. AI OS Tool neu..."

# 1. Stoppe laufende Komponenten sauber
if [ -f "$SCRIPT_DIR/stop.sh" ]; then
    bash "$SCRIPT_DIR/stop.sh"
else
    pkill -f "[s]erver\.py" 2>/dev/null || true
    pkill -f "next-(dev|start|server)" 2>/dev/null || true
fi

sleep 1

# 2. Starte J.A.R.V.I.S. neu
nohup bash "$SCRIPT_DIR/run.sh" >/dev/null 2>&1 &

echo "[✓] J.A.R.V.I.S. AI OS Neustart initiiert."
