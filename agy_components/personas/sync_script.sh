#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_POOL="${AGY_DATA_POOL:-$SCRIPT_DIR/../data-pool}"
mkdir -p "$DATA_POOL"
rsync -av ~/.local/share/ "$DATA_POOL/"
