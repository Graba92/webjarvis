#!/usr/bin/env bash
# ==============================================================================
# J.A.R.V.I.S. AI OS — Ergonomic 1-Click Launcher (run.sh)
# Blueprint by Matthias Haase (Graba92)
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Falls Argumente übergeben wurden, an start.sh durchreichen
if [ "$#" -gt 0 ]; then
    exec "$SCRIPT_DIR/start.sh" "$@"
fi

# Standardstart via start.sh
exec "$SCRIPT_DIR/start.sh"
