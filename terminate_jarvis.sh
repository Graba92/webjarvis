#!/usr/bin/env bash
# ==============================================================================
# J.A.R.V.I.S. AI OS — Process Terminator
# Beendet zuverlässig alle Hintergrund-Subsysteme (Backend, Bridges, Frontend)
# ==============================================================================

echo "[*] Fahre alle J.A.R.V.I.S. Prozesse herunter..."

pkill -f "python3.*backend/server.py" 2>/dev/null && echo "✓ Backend beendet" || true
pkill -f "node.*whatsapp_bridge/server.js" 2>/dev/null && echo "✓ WhatsApp Bridge beendet" || true
pkill -f "python3.*discord_bridge/discord_bot.py" 2>/dev/null && echo "✓ Discord Bot beendet" || true
pkill -f "next dev" 2>/dev/null && echo "✓ Next.js Frontend beendet" || true

# Portfreigaben absichern
fuser -k 8765/tcp 2>/dev/null || true
fuser -k 3001/tcp 2>/dev/null || true
fuser -k 3000/tcp 2>/dev/null || true

echo "[✓] Alle Prozesse gestoppt."
