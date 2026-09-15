# J.A.R.V.I.S. Discord Bridge Bot — Linux Edition
*Made by Matthias Haase (Graba92)*

Die **J.A.R.V.I.S. Discord Bridge** verbindet deinen Discord-Server direkt und bidirektional mit dem J.A.R.V.I.S. AI Operating System auf deinem CachyOS / Arch System.

---

## 🌟 Funktionsumfang

1. **Vollwertiger J.A.R.V.I.S.-Chat & Sprachassistent**:
   - `/jarvis <befehl>`: Sendet Prompts an J.A.R.V.I.S. (Gemini Live / Tool-Calling) und gibt die Antwort zurück.
   - **Erwähnung & DMs**: Schreibe `@J.A.R.V.I.S. <text>` oder sende dem Bot eine Direktnachricht (DM).
2. **System- & Prozesssteuerung von `start.sh`**:
   - `/status`: Zeigt Live-Metriken (CPU, RAM, Status von Backend, 3D HUD Frontend & WhatsApp Bridge).
   - `/start <komponente>`: Startet `start.sh -a` (Gesamtsystem), Backend, Frontend oder WhatsApp Bridge.
   - `/stop <ziel>`: Beendet gezielt oder komplett laufende Prozesse sauber.
   - `/restart`: Beendet und startet das J.A.R.V.I.S.-System neu via `start.sh -a`.
   - `/check`: Führt `start.sh -c` aus und liefert die Hardware- & Systemdiagnose direkt nach Discord.
3. **Interaktive Sicherheits-Freigabe (Safety Gates)**:
   - Verlangt J.A.R.V.I.S. eine Bestätigung (z. B. vor Dateilöschungen oder Terminal-Eingriffen), sendet der Bot interaktive Buttons (✅ Zulassen / 🛑 Abbrechen).
   - `/confirm <true/false>`: Manuelle Freigabe/Ablehnung.
   - `/undo`: Macht die letzte J.A.R.V.I.S.-Aktion rückgängig.
4. **Sicherheit & Zugriffsschutz**:
   - Über `DISCORD_ADMIN_IDS` in `.env` kann festgelegt werden, wer administrative Befehle (`/start`, `/stop`, `/restart`) ausführen darf.

---

## 🚀 Einrichtung & Discord Bot erstellen

### 1. Bot im Discord Developer Portal erstellen
1. Öffne das [Discord Developer Portal](https://discord.com/developers/applications).
2. Klicke auf **New Application** und vergib einen Namen (z. B. `J.A.R.V.I.S.`).
3. Gehe im linken Menü auf **Bot**:
   - Klicke auf **Reset Token** und kopiere den Token.
   - Aktiviere unter **Privileged Gateway Intents**:
     - ✅ **Message Content Intent** (Erforderlich!)
     - ✅ **Server Members Intent** (Optional)
4. Gehe auf **OAuth2 -> URL Generator**:
   - Scopes: `bot`, `applications.commands`
   - Bot Permissions:
     - `Send Messages`
     - `Embed Links`
     - `Attach Files`
     - `Read Message History`
     - `View Channels`
5. Kopiere die generierte URL und lade den Bot auf deinen Server ein.

### 2. Token hinterlegen
Öffne `backend/discord_bridge/.env` (oder starte `./start_discord.sh`, Option 3) und trage deinen Token ein:
```bash
DISCORD_BOT_TOKEN=dein_discord_bot_token_hier
DISCORD_ADMIN_IDS=deine_discord_user_id
```

### 3. Starten
```bash
cd backend/discord_bridge
./start_discord.sh
```
Oder direkt aus dem J.A.R.V.I.S. Hauptmenü (`start.sh`).
