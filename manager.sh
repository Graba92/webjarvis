#!/usr/bin/env bash
# ==============================================================================
# J.A.R.V.I.S. AI OS — Desktop Manager Launcher
# Startet das PyQt6-basierte Wartungs- und Kontrollzentrum
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Bevorzuge System-Python3 (da PyQt6 unter Arch/CachyOS systemweit bereitsteht)
if /usr/bin/python3 -c "import PyQt6" >/dev/null 2>&1; then
    exec /usr/bin/python3 "$SCRIPT_DIR/manager.py" "$@"
elif [ -f "$SCRIPT_DIR/backend/.venv/bin/python3" ] && "$SCRIPT_DIR/backend/.venv/bin/python3" -c "import PyQt6" >/dev/null 2>&1; then
    exec "$SCRIPT_DIR/backend/.venv/bin/python3" "$SCRIPT_DIR/manager.py" "$@"
else
    exec python3 "$SCRIPT_DIR/manager.py" "$@"
fi
