#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==============================================================================
# J.A.R.V.I.S. AI OS — Discord Bridge Bot
# CachyOS / Arch Edition
# Made by Matthias Haase (Graba92)
# ==============================================================================

import os
import sys
import json
import time
import socket
import asyncio
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

import psutil
import discord
from discord import app_commands
from discord.ext import commands

# ── Pfade und Umgebung ────────────────────────────────────────────────────────
CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
PROJECT_DIR = BACKEND_DIR.parent
START_SCRIPT = PROJECT_DIR / "start.sh"

# Lade Umgebungsvariablen aus Projekt- und Bridge-.env
try:
    from dotenv import load_dotenv
    if (PROJECT_DIR / ".env").exists():
        load_dotenv(PROJECT_DIR / ".env")
    if (BACKEND_DIR / ".env").exists():
        load_dotenv(BACKEND_DIR / ".env")
    if (CURRENT_DIR / ".env").exists():
        load_dotenv(CURRENT_DIR / ".env", override=True)
except ImportError:
    pass

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "").strip()
JARVIS_WS_HOST = os.getenv("JARVIS_WS_HOST", "127.0.0.1")
JARVIS_WS_PORT = int(os.getenv("JARVIS_WS_PORT", "8765"))
JARVIS_WS_URL = os.getenv("JARVIS_WS_URL", f"ws://{JARVIS_WS_HOST}:{JARVIS_WS_PORT}")
DISCORD_CHANNEL_ID_RAW = os.getenv("DISCORD_NOTIFY_CHANNEL_ID", "").strip()
DEFAULT_CHANNEL_ID = int(DISCORD_CHANNEL_ID_RAW) if DISCORD_CHANNEL_ID_RAW.isdigit() else None

# Admin User IDs (kann kommagetrennt in DISCORD_ADMIN_IDS hinterlegt sein)
ADMIN_IDS_RAW = os.getenv("DISCORD_ADMIN_IDS", "").strip()
ADMIN_USER_IDS: List[int] = [int(x.strip()) for x in ADMIN_IDS_RAW.split(",") if x.strip().isdigit()]

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [DiscordBridge] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("JarvisDiscordBridge")

# ── Discord Client Setup ──────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("!j ", "!jarvis "),
    intents=intents,
    help_command=None
)

# ── State & Bridge Management ────────────────────────────────────────────────
class JarvisBridgeState:
    def __init__(self):
        self.ws = None
        self.connected = False
        self.reconnecting = False
        self.last_connected_at: Optional[datetime] = None
        self.active_waiting_replies: Dict[str, asyncio.Future] = {}
        self.broadcast_channel_id: Optional[int] = DEFAULT_CHANNEL_ID
        self.last_safety_request: Optional[Dict[str, Any]] = None

state = JarvisBridgeState()

def is_admin(user: discord.User | discord.Member) -> bool:
    """Prüft, ob der Benutzer Admin-Rechte besitzt (oder keine Admins explizit gefiltert wurden)."""
    if not ADMIN_USER_IDS:
        return True
    return user.id in ADMIN_USER_IDS

def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Prüft, ob ein lokaler Port offen ist."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0

def find_processes_by_cmd(keywords: List[str]) -> List[psutil.Process]:
    """Findet laufende Prozesse anhand von Schlüsselwörtern in der Befehlszeile."""
    matched = []
    for p in psutil.process_iter(attrs=["pid", "name", "cmdline"]):
        try:
            cmd = " ".join(p.info.get("cmdline") or [])
            if any(k in cmd for k in keywords):
                matched.append(p)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return matched

# ── Interactive UI Views (Safety Confirmation) ────────────────────────────────
class SafetyGateView(discord.ui.View):
    def __init__(self, action: str, label: str):
        super().__init__(timeout=90.0)
        self.action = action
        self.label = label
        self.resolved = False

    @discord.ui.button(label="Zulassen (Ausführen)", style=discord.ButtonStyle.green, emoji="✅")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_admin(interaction.user):
            await interaction.response.send_message("❌ Nur autorisierte Admins dürfen Sicherheitsbestätigungen erteilen.", ephemeral=True)
            return

        self.resolved = True
        for item in self.children:
            item.disabled = True
        
        await send_jarvis_raw({"type": "confirm_resolve", "accepted": True})
        await interaction.response.edit_message(
            content=f"✅ **Freigabe erteilt** durch {interaction.user.mention} für: `{self.label}`",
            view=self
        )

    @discord.ui.button(label="Abbrechen (Blockieren)", style=discord.ButtonStyle.danger, emoji="🛑")
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_admin(interaction.user):
            await interaction.response.send_message("❌ Nur autorisierte Admins dürfen Sicherheitsentscheidungen treffen.", ephemeral=True)
            return

        self.resolved = True
        for item in self.children:
            item.disabled = True

        await send_jarvis_raw({"type": "confirm_resolve", "accepted": False})
        await interaction.response.edit_message(
            content=f"🛑 **Aktion blockiert** durch {interaction.user.mention} für: `{self.label}`",
            view=self
        )

    async def on_timeout(self):
        if not self.resolved:
            for item in self.children:
                item.disabled = True
            await send_jarvis_raw({"type": "confirm_resolve", "accepted": False})

# ── WebSocket Client zu J.A.R.V.I.S. Core ─────────────────────────────────────
async def send_jarvis_raw(payload: dict) -> bool:
    """Sendet JSON-Payload an den J.A.R.V.I.S. Core WebSocket."""
    if state.ws and state.connected:
        try:
            await state.ws.send(json.dumps(payload))
            return True
        except Exception as e:
            logger.error(f"Fehler beim Senden an WebSocket: {e}")
            state.connected = False
    return False

async def jarvis_ws_worker():
    """Hintergrund-Worker mit Auto-Reconnect und Keepalive zur J.A.R.V.I.S. WebSocket Bridge."""
    import websockets
    
    backoff = 1.0
    while True:
        try:
            logger.info(f"Verbinde mit J.A.R.V.I.S. Core WebSocket auf {JARVIS_WS_URL}...")
            async with websockets.connect(JARVIS_WS_URL, ping_interval=20, ping_timeout=10) as ws:
                state.ws = ws
                state.connected = True
                state.last_connected_at = datetime.now()
                backoff = 1.0
                logger.info("✓ Erfolgreich mit J.A.R.V.I.S. Core verbunden!")

                # Sende Init-Log an J.A.R.V.I.S.
                await ws.send(json.dumps({
                    "type": "log",
                    "speaker": "SYS",
                    "text": "Discord Gateway Bridge erfolgreich verbunden."
                }))

                async for raw in ws:
                    try:
                        data = json.loads(raw)
                        await handle_incoming_jarvis_message(data)
                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        logger.error(f"Fehler bei Nachrichtenverarbeitung: {e}")

        except (asyncio.CancelledError, KeyboardInterrupt):
            logger.info("WebSocket Worker beendet.")
            break
        except Exception as e:
            state.connected = False
            state.ws = None
            logger.warning(f"J.A.R.V.I.S. Core nicht erreichbar ({e}). Reconnect in {backoff:.1f}s...")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 1.5, 15.0)

async def handle_incoming_jarvis_message(data: dict):
    """Verarbeitet eingehende Events vom J.A.R.V.I.S. Core."""
    msg_type = data.get("type")
    
    # 1. Antwort von J.A.R.V.I.S. (Text/Sprache)
    if msg_type == "log":
        speaker = data.get("speaker")
        text = data.get("text", "")
        ts = data.get("ts", datetime.now().strftime("%H:%M:%S"))

        if speaker == "JARVIS" and text:
            # Benachrichtige wartende Futures
            for req_id, fut in list(state.active_waiting_replies.items()):
                if not fut.done():
                    fut.set_result(text)
                    state.active_waiting_replies.pop(req_id, None)

            # Sende an Standard-Broadcast-Kanal, wenn vorhanden
            if state.broadcast_channel_id:
                channel = bot.get_channel(state.broadcast_channel_id)
                if channel:
                    embed = discord.Embed(
                        description=text[:4000],
                        color=discord.Color.teal(),
                        timestamp=datetime.now()
                    )
                    embed.set_author(name="J.A.R.V.I.S. AI OS", icon_url="https://cdn-icons-png.flaticon.com/512/4712/4712038.png")
                    embed.set_footer(text=f"Core • {ts}")
                    await channel.send(embed=embed)

    # 2. Safety Gate Bestätigungsanfrage
    elif msg_type == "confirm_request":
        action = data.get("action", "unknown")
        label = data.get("label", "Aktion bestätigen")
        detail = data.get("detail", "")
        timeout = data.get("timeout", 90)

        state.last_safety_request = data
        if state.broadcast_channel_id:
            channel = bot.get_channel(state.broadcast_channel_id)
            if channel:
                view = SafetyGateView(action=action, label=label)
                embed = discord.Embed(
                    title="⚠️ J.A.R.V.I.S. Sicherheitsfreigabe erforderlich",
                    description=f"**Aktion:** `{label}`\n**Detail:** {detail}\n**Timeout:** {timeout} Sekunden",
                    color=discord.Color.gold()
                )
                embed.set_footer(text="Bitte unten bestätigen oder abbrechen")
                await channel.send(embed=embed, view=view)

# ── Discord Event Handler ────────────────────────────────────────────────────
@bot.event
async def on_ready():
    logger.info(f"Bot angemeldet als {bot.user.name} ({bot.user.id})")
    logger.info(f"Discord.py Version: {discord.__version__}")
    
    # Slash Commands synchronisieren
    try:
        synced = await bot.tree.sync()
        logger.info(f"✓ {len(synced)} Slash Commands synchronisiert.")
    except Exception as e:
        logger.error(f"Fehler bei Slash Command Sync: {e}")

    activity = discord.Activity(type=discord.ActivityType.listening, name="J.A.R.V.I.S. AI OS")
    await bot.change_presence(status=discord.Status.online, activity=activity)

    # Starte WebSocket Client Worker
    bot.loop.create_task(jarvis_ws_worker())

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    # Direkte Erwähnung oder DM als J.A.R.V.I.S. Befehl werten
    is_dm = isinstance(message.channel, discord.DMChannel)
    is_mentioned = bot.user in message.mentions

    if is_dm or is_mentioned:
        # Prompt bereinigen
        raw_text = message.content
        if is_mentioned:
            raw_text = raw_text.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "")
        prompt = raw_text.strip()

        if prompt:
            async with message.channel.typing():
                response = await ask_jarvis_core(prompt, author=message.author)
                if response:
                    # In Chunks aufteilen (Discord 2000 Zeichen Grenze)
                    for chunk in [response[i:i+1900] for i in range(0, len(response), 1900)]:
                        await message.reply(chunk)
                else:
                    await message.reply("*(Befehl an J.A.R.V.I.S. übermittelt)*")
            return

    await bot.process_commands(message)

# ── Kernfunktion: Text an J.A.R.V.I.S. senden ────────────────────────────────
async def ask_jarvis_core(prompt: str, author: discord.User | discord.Member, timeout: float = 20.0) -> Optional[str]:
    """Übermittelt Textbefehl an J.A.R.V.I.S. und wartet auf synchrone Antwort."""
    if not state.connected or not state.ws:
        return "⚠️ J.A.R.V.I.S. Core ist offline (Port 8765 nicht erreichbar). Starte das System mit `/start`."

    req_id = f"discord_{int(time.time() * 1000)}"
    loop = asyncio.get_running_loop()
    future = loop.create_future()
    state.active_waiting_replies[req_id] = future

    is_user_admin = is_admin(author)
    payload = {
        "type": "text_command",
        "text": prompt,
        "source": "discord",
        "sender": f"{author.name} (Discord)",
        "is_self": is_user_admin
    }

    try:
        await state.ws.send(json.dumps(payload))
        # Warte auf Antwort von J.A.R.V.I.S.
        try:
            result = await asyncio.wait_for(future, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            state.active_waiting_replies.pop(req_id, None)
            return "*(Befehl ausgeführt / Keine direkte Textantwort)*"
    except Exception as e:
        state.active_waiting_replies.pop(req_id, None)
        return f"❌ Verbindungsfehler zu J.A.R.V.I.S. Core: {e}"

# ── Slash Commands ────────────────────────────────────────────────────────────

@bot.tree.command(name="jarvis", description="Sende einen Sprach-/Textbefehl direkt an J.A.R.V.I.S. AI OS")
@app_commands.describe(prompt="Dein Befehl oder deine Frage an J.A.R.V.I.S.")
async def cmd_jarvis(interaction: discord.Interaction, prompt: str):
    await interaction.response.defer(thinking=True)
    ans = await ask_jarvis_core(prompt, interaction.user)
    
    if len(ans) > 1900:
        await interaction.followup.send(ans[:1900])
        for chunk in [ans[i:i+1900] for i in range(1900, len(ans), 1900)]:
            await interaction.channel.send(chunk)
    else:
        embed = discord.Embed(
            description=ans,
            color=discord.Color.blue()
        )
        embed.set_author(name="J.A.R.V.I.S. Antwort", icon_url="https://cdn-icons-png.flaticon.com/512/4712/4712038.png")
        embed.set_footer(text=f"Anfrage von {interaction.user.display_name}")
        await interaction.followup.send(embed=embed)

@bot.tree.command(name="status", description="Zeigt den Live-Status des J.A.R.V.I.S. Gesamtsystems")
async def cmd_status(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)

    backend_ok = is_port_in_use(8765)
    frontend_ok = is_port_in_use(3000)
    wa_ok = is_port_in_use(3001)

    cpu_percent = psutil.cpu_percent(interval=0.2)
    ram = psutil.virtual_memory()

    embed = discord.Embed(
        title="🖥️ J.A.R.V.I.S. AI OS — Systemstatus",
        description="CachyOS / Arch Linux Master Status",
        color=discord.Color.green() if backend_ok else discord.Color.red(),
        timestamp=datetime.now()
    )

    embed.add_field(
        name="Backend Core (Gemini Live)",
        value=f"{'🟢 ONLINE (ws://127.0.0.1:8765)' if backend_ok else '🔴 OFFLINE'}\nBridge-Status: {'✅ Verbunden' if state.connected else '❌ Getrennt'}",
        inline=False
    )
    embed.add_field(
        name="Frontend (Next.js 15 3D WebGL)",
        value='🟢 ONLINE (http://localhost:3000)' if frontend_ok else '🔴 OFFLINE',
        inline=True
    )
    embed.add_field(
        name="WhatsApp Bridge (Baileys)",
        value='🟢 ONLINE (http://127.0.0.1:3001)' if wa_ok else '⚪ INAKTIV',
        inline=True
    )
    embed.add_field(
        name="System-Ressourcen",
        value=f"CPU: `{cpu_percent}%` | RAM: `{ram.percent}%` ({ram.used // (1024*1024)}MB / {ram.total // (1024*1024)}MB)",
        inline=False
    )

    embed.set_footer(text="Steuerung via /start, /stop, /restart oder /check")
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="start", description="Startet J.A.R.V.I.S. Komponenten über start.sh")
@app_commands.describe(komponente="Komponente auswählen (all, backend, frontend, whatsapp)")
@app_commands.choices(komponente=[
    app_commands.Choice(name="Gesamtsystem (Backend + WA + Frontend)", value="all"),
    app_commands.Choice(name="Nur Python Backend (Gemini Live Core)", value="backend"),
    app_commands.Choice(name="Nur Next.js Frontend (3D HUD)", value="frontend"),
    app_commands.Choice(name="Nur WhatsApp Bridge", value="whatsapp"),
])
async def cmd_start(interaction: discord.Interaction, komponente: app_commands.Choice[str]):
    if not is_admin(interaction.user):
        await interaction.response.send_message("❌ Zugriff verweigert: Nur autorisierte Administratoren dürfen Systemprozesse starten.", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)

    flag_map = {
        "all": "-a",
        "backend": "-b",
        "frontend": "-f",
        "whatsapp": "-w"
    }
    flag = flag_map.get(komponente.value, "-a")

    if not START_SCRIPT.exists():
        await interaction.followup.send(f"❌ Skript nicht gefunden: `{START_SCRIPT}`")
        return

    try:
        # Prozess im Hintergrund starten
        proc = subprocess.Popen(
            ["bash", str(START_SCRIPT), flag],
            cwd=str(PROJECT_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        await asyncio.sleep(2.5)
        backend_ok = is_port_in_use(8765)

        embed = discord.Embed(
            title="🚀 J.A.R.V.I.S. Startbefehl übermittelt",
            description=f"Option: `{komponente.name}` (`{flag}`)\nProzess-PID: `{proc.pid}`",
            color=discord.Color.green() if backend_ok else discord.Color.orange()
        )
        embed.add_field(name="Backend Port 8765", value="🟢 Aktiv" if backend_ok else "⏳ Wird hochgefahren...")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Fehler beim Ausführen von `start.sh`: {e}")

@bot.tree.command(name="stop", description="Stoppt J.A.R.V.I.S. Prozesse sauber und sicher")
@app_commands.describe(ziel="Welches Subsystem soll gestoppt werden?")
@app_commands.choices(ziel=[
    app_commands.Choice(name="Alles beenden (Backend + Frontend + Bridges)", value="all"),
    app_commands.Choice(name="Nur Backend Core", value="backend"),
    app_commands.Choice(name="Nur Frontend", value="frontend"),
    app_commands.Choice(name="Nur WhatsApp Bridge", value="whatsapp"),
])
async def cmd_stop(interaction: discord.Interaction, ziel: app_commands.Choice[str]):
    if not is_admin(interaction.user):
        await interaction.response.send_message("❌ Zugriff verweigert: Nur Administratoren dürfen Systemprozesse beenden.", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    stopped = []

    # Backend
    if ziel.value in ("all", "backend"):
        procs = find_processes_by_cmd(["server.py", "start_backend"])
        for p in procs:
            try:
                p.terminate()
                stopped.append(f"Backend (PID {p.pid})")
            except:
                pass

    # Frontend
    if ziel.value in ("all", "frontend"):
        procs = find_processes_by_cmd(["next-server", "next dev"])
        for p in procs:
            try:
                p.terminate()
                stopped.append(f"Frontend (PID {p.pid})")
            except:
                pass

    # WhatsApp Bridge
    if ziel.value in ("all", "whatsapp"):
        procs = find_processes_by_cmd(["whatsapp_bridge/server.js", "baileys"])
        for p in procs:
            try:
                p.terminate()
                stopped.append(f"WhatsApp Bridge (PID {p.pid})")
            except:
                pass

    msg = "🛑 Beendete Prozesse:\n• " + "\n• ".join(stopped) if stopped else "ℹ️ Keine aktiven Prozesse zum Beenden gefunden."
    await interaction.followup.send(msg)

@bot.tree.command(name="restart", description="Startet das J.A.R.V.I.S. Gesamtsystem neu")
async def cmd_restart(interaction: discord.Interaction):
    if not is_admin(interaction.user):
        await interaction.response.send_message("❌ Zugriff verweigert: Nur Administratoren dürfen J.A.R.V.I.S. neu starten.", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)

    # 1. Beenden
    for p in find_processes_by_cmd(["server.py", "next-server", "whatsapp_bridge"]):
        try: p.terminate()
        except: pass
    
    await asyncio.sleep(2)

    # 2. Neu starten
    try:
        proc = subprocess.Popen(
            ["bash", str(START_SCRIPT), "-a"],
            cwd=str(PROJECT_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        await asyncio.sleep(3)
        await interaction.followup.send(f"🔄 J.A.R.V.I.S. neu gestartet (Neuer Master PID: `{proc.pid}`).")
    except Exception as e:
        await interaction.followup.send(f"❌ Neustart fehlgeschlagen: {e}")

@bot.tree.command(name="check", description="Führt System- & Hardwareprüfung via start.sh --check aus")
async def cmd_check(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)

    if not START_SCRIPT.exists():
        await interaction.followup.send(f"❌ Skript `{START_SCRIPT}` nicht gefunden.")
        return

    try:
        res = subprocess.run(
            ["bash", str(START_SCRIPT), "-c"],
            cwd=str(PROJECT_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=15
        )
        # ANSI Farbcodes entfernen für Discord
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        clean_text = ansi_escape.sub('', res.stdout)

        embed = discord.Embed(
            title="🔍 J.A.R.V.I.S. System- & Hardware-Check",
            description=f"```text\n{clean_text[:3900]}\n```",
            color=discord.Color.teal()
        )
        embed.set_footer(text="start.sh -c auf CachyOS")
        await interaction.followup.send(embed=embed)
    except subprocess.TimeoutExpired:
        await interaction.followup.send("⚠️ Zeitüberschreitung bei der Systemprüfung.")
    except Exception as e:
        await interaction.followup.send(f"❌ Fehler bei Prüfung: {e}")

@bot.tree.command(name="undo", description="Letzte J.A.R.V.I.S. Aktion rückgängig machen")
async def cmd_undo(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    if not state.connected:
        await interaction.followup.send("⚠️ J.A.R.V.I.S. Core ist nicht verbunden.")
        return
    
    await send_jarvis_raw({"type": "undo"})
    await interaction.followup.send("↩️ Undo-Befehl an J.A.R.V.I.S. übermittelt.")

@bot.tree.command(name="confirm", description="Manuelle Sicherheitsbestätigung erteilen oder ablehnen")
@app_commands.describe(erlauben="Aktion erlauben (True) oder ablehnen (False)")
async def cmd_confirm(interaction: discord.Interaction, erlauben: bool):
    if not is_admin(interaction.user):
        await interaction.response.send_message("❌ Zugriff verweigert: Nur Administratoren dürfen Bestätigungen erteilen.", ephemeral=True)
        return
    
    await send_jarvis_raw({"type": "confirm_resolve", "accepted": erlauben})
    await interaction.response.send_message(f"{'✅ Freigabe erteilt' if erlauben else '🛑 Aktion abgebrochen'} durch {interaction.user.mention}.")

@bot.tree.command(name="setchannel", description="Diesen Kanal als primären J.A.R.V.I.S. Benachrichtigungskanal festlegen")
async def cmd_setchannel(interaction: discord.Interaction):
    if not is_admin(interaction.user):
        await interaction.response.send_message("❌ Nur Administratoren können den Broadcast-Kanal konfigurieren.", ephemeral=True)
        return

    state.broadcast_channel_id = interaction.channel_id
    await interaction.response.send_message(f"📢 Dieser Kanal (`{interaction.channel.name}`) wurde als primärer J.A.R.V.I.S.-Kanal eingerichtet.")

# ── Main Entrypoint ──────────────────────────────────────────────────────────
def main():
    if not DISCORD_BOT_TOKEN:
        print("[!] Kein DISCORD_BOT_TOKEN in .env oder Umgebungsvariablen gefunden.")
        print("[!] Bitte hinterlege deinen Bot-Token in:")
        print(f"    {CURRENT_DIR}/.env  oder  {PROJECT_DIR}/.env")
        print("    DISCORD_BOT_TOKEN=dein_bot_token_hier")
        sys.exit(1)

    print("=" * 60)
    print("   J.A.R.V.I.S. DISCORD BRIDGE — CachyOS / Arch Edition")
    print("   Made by Matze Graba & Chati")
    print("=" * 60)
    print(f"• J.A.R.V.I.S. WebSocket: {JARVIS_WS_URL}")
    print(f"• Admin-IDs konfiguriert: {ADMIN_USER_IDS if ADMIN_USER_IDS else 'Keine (Jeder darf steuern)'}")
    print("Starte Discord Gateway Bot...")

    try:
        bot.run(DISCORD_BOT_TOKEN, log_handler=None)
    except Exception as e:
        logger.error(f"Fataler Fehler beim Ausführen des Discord Bots: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
