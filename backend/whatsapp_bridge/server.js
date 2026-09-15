/**
 * backend/whatsapp_bridge/server.js
 * Native Multi-Device WhatsApp Gateway Bridge für J.A.R.V.I.S. AI OS.
 * 
 * Basiert auf @whiskeysockets/baileys (WhatsApp Web Multi-Device Protokoll).
 * - Einmaliges QR-Code Pairing im Terminal oder über http://localhost:3001/qr
 * - Dauerhafte, verschlüsselte Session-Speicherung in auth_info_baileys/
 * - REST-API für J.A.R.V.I.S. Python Backend: POST /send, GET /status, GET /qr
 * - Eingehende WhatsApp-Nachrichten werden automatisch per WebSocket an J.A.R.V.I.S. weitergeleitet.
 */

const {
  default: makeWASocket,
  useMultiFileAuthState,
  DisconnectReason,
  fetchLatestBaileysVersion
} = require("@whiskeysockets/baileys");
const pino = require("pino");
const qrcode = require("qrcode-terminal");
const express = require("express");
const path = require("path");
const fs = require("fs");
const WebSocket = require("ws");
const AutoDoc = require("./auto_doc");

const PORT = parseInt(process.env.WHATSAPP_PORT || "3001", 10);
const HOST = process.env.WHATSAPP_HOST || "127.0.0.1";
const JARVIS_WS_URL = process.env.JARVIS_WS_URL || "ws://127.0.0.1:8765";
const AUTH_DIR = path.join(__dirname, "auth_info_baileys");

if (!fs.existsSync(AUTH_DIR)) {
  fs.mkdirSync(AUTH_DIR, { recursive: true });
}

const autoDoc = new AutoDoc(AUTH_DIR);

let sock = null;
let currentQR = null;
let isConnected = false;
let userJid = null;
let jarvisWs = null;
const recentSentMessageIds = new Set();
let lastSendPromise = Promise.resolve();

// Auto-Doc Log-Monitor installieren
autoDoc.installLogMonitor(() => sock);

// --- WebSocket Verbindung zu J.A.R.V.I.S. Python Backend ---
function connectToJarvisBackend() {
  try {
    jarvisWs = new WebSocket(JARVIS_WS_URL);

    jarvisWs.on("open", () => {
      console.log(`[Bridge -> Jarvis] Verbunden mit J.A.R.V.I.S. Core auf ${JARVIS_WS_URL}`);
    });

    jarvisWs.on("close", () => {
      jarvisWs = null;
      setTimeout(connectToJarvisBackend, 5000);
    });

    jarvisWs.on("error", () => {
      jarvisWs = null;
    });
  } catch (err) {
    jarvisWs = null;
    setTimeout(connectToJarvisBackend, 5000);
  }
}

function sendToJarvis(payload) {
  if (jarvisWs && jarvisWs.readyState === WebSocket.OPEN) {
    jarvisWs.send(JSON.stringify(payload));
  }
}

// --- WhatsApp Multi-Device Socket Initialisierung ---
async function startWhatsAppSocket() {
  const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);
  const { version, isLatest } = await fetchLatestBaileysVersion().catch(() => ({
    version: [2, 3000, 1015901307],
    isLatest: true
  }));

  console.log(`[WhatsApp Bridge] Initialisiere Baileys v${version.join(".")} (Latest: ${isLatest})...`);

  sock = makeWASocket({
    version,
    auth: state,
    logger: pino({ level: "silent" }),
    printQRInTerminal: false, // Wir steuern die Ausgabe selbst via qrcode-terminal
    browser: ["J.A.R.V.I.S. OS", "CachyOS Linux", "1.0.0"],
    syncFullHistory: false,
    generateHighQualityLinkPreview: true,
    msgRetryCounterCache: autoDoc.msgRetryCounterCache,
    placeholderResendCache: autoDoc.placeholderResendCache,
    maxMsgRetryCount: 5,
    retryRequestDelayMs: 250,
    getMessage: async (key) => autoDoc.getMessage(key)
  });

  sock.ev.on("creds.update", saveCreds);

  sock.ev.on("connection.update", async (update) => {
    const { connection, lastDisconnect, qr } = update;

    if (qr) {
      currentQR = qr;
      isConnected = false;
      console.log("\n" + "=".repeat(60));
      console.log("   J.A.R.V.I.S. WHATSAPP PAIRING — BITTE QR-CODE SCANNEN");
      console.log("=".repeat(60));
      console.log("1. Öffne WhatsApp auf deinem Smartphone.");
      console.log("2. Menü (drei Punkte) -> Verknüpfte Geräte -> Gerät verknüpfen.");
      console.log("3. Scanne diesen QR-Code direkt aus dem Terminal:\n");
      qrcode.generate(qr, { small: true });
      console.log("\nAlternativ im Browser öffnen: http://localhost:3001/qr");
      console.log("=".repeat(60) + "\n");

      sendToJarvis({
        type: "log",
        speaker: "SYS",
        text: "WhatsApp-Pairing erforderlich: Bitte den QR-Code im Terminal oder unter http://localhost:3001/qr mit WhatsApp scannen."
      });
    }

    if (connection === "open") {
      isConnected = true;
      currentQR = null;
      userJid = sock.user ? sock.user.id : "Verbunden";
      console.log(`\n[✓] WhatsApp Bridge erfolgreich verbunden! Angemeldet als: ${userJid}\n`);

      sendToJarvis({
        type: "log",
        speaker: "SYS",
        text: `WhatsApp Multi-Device Bridge aktiv verbunden (${userJid.split(":")[0]}).`
      });
    }

    if (connection === "close") {
      isConnected = false;
      const statusCode = lastDisconnect?.error?.output?.statusCode;
      const shouldReconnect = statusCode !== DisconnectReason.loggedOut;

      console.log(`[!] WhatsApp Verbindung getrennt (Status-Code: ${statusCode}). Reconnect: ${shouldReconnect}`);

      if (statusCode === DisconnectReason.loggedOut) {
        console.log("[!] Sitzung wurde auf dem Smartphone beendet. Bereinige auth_info_baileys...");
        try {
          fs.rmSync(AUTH_DIR, { recursive: true, force: true });
          fs.mkdirSync(AUTH_DIR, { recursive: true });
        } catch (e) {}
      }

      if (shouldReconnect) {
        setTimeout(startWhatsAppSocket, 3000);
      } else {
        setTimeout(startWhatsAppSocket, 1000);
      }
    }
  });

  // Eingehende Nachrichten empfangen und an Jarvis übergeben
  sock.ev.on("messages.upsert", async (m) => {
    if (!m.messages || m.messages.length === 0) return;
    const msg = m.messages[0];

    // 1. Loop-Schutz: Nachrichten ignorieren, die wir selbst gerade per API gesendet haben
    if (msg.key && msg.key.id && recentSentMessageIds.has(msg.key.id)) {
      recentSentMessageIds.delete(msg.key.id);
      return;
    }

    const senderJid = msg.key.remoteJid;
    if (!senderJid || senderJid.endsWith("@broadcast")) return;

    // Ermitteln, ob es sich um den "Chat mit sich selbst" (Nachricht an mich) handelt
    const myNumber = userJid ? userJid.split(":")[0].split("@")[0] : "";
    const isSelfChat = senderJid.split("@")[0] === myNumber;

    // 2. Normale ausgehende Nachrichten an andere Kontakte ignorieren (z. B. wenn Matze mit Freunden schreibt).
    // ABER: Wenn Matze in seinem eigenen "Chat mit mir selbst" schreibt, ist das ein Sprach-/Textbefehl an Cypher!
    if (msg.key.fromMe && !isSelfChat) return;

    const senderNumber = "+" + senderJid.split("@")[0];
    const text =
      msg.message?.conversation ||
      msg.message?.extendedTextMessage?.text ||
      msg.message?.imageMessage?.caption ||
      "";

    const cleanText = text.trim();
    if (!cleanText) return;

    // Nachricht im Auto-Doc Vault sichern (für Retry- und Re-Encryption Anfragen)
    if (msg.key && msg.key.id && msg.message) {
      autoDoc.recordMessage(msg.key.id, msg.message, cleanText, senderJid);
    }

    console.log(`[WhatsApp Inbound] Nachricht von ${senderNumber}${isSelfChat ? " (Chat mit sich selbst)" : ""}: "${cleanText}"`);

    // Übergabe an Jarvis Core
    sendToJarvis({
      type: "text_command",
      text: cleanText,
      source: "whatsapp",
      sender: senderNumber,
      is_self: isSelfChat
    });

    sendToJarvis({
      type: "log",
      speaker: "YOU",
      text: `[WhatsApp von ${senderNumber}${isSelfChat ? " (Notiz an mich)" : ""}]: ${cleanText}`
    });
  });
}

// --- Express REST API Server ---
const app = express();
app.use(express.json());

// 1. Status-Abfrage
app.get("/status", (req, res) => {
  res.json({
    online: true,
    connected: isConnected,
    user: userJid ? userJid.split(":")[0] : null,
    qr_available: !!currentQR,
    timestamp: new Date().toISOString()
  });
});

// 2. QR-Code als HTML / SVG zur bequemen Ansicht im Browser
app.get("/qr", (req, res) => {
  if (isConnected) {
    return res.send(`
      <!DOCTYPE html>
      <html>
      <head><title>J.A.R.V.I.S. WhatsApp Bridge</title><meta charset="utf-8">
      <style>body { background: #080808; color: #00f0ff; font-family: monospace; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; text-align: center; }</style>
      </head>
      <body>
        <div>
          <h1 style="color: #00f0ff;">✓ WhatsApp Bridge Verbunden</h1>
          <p style="color: #a5f3fc;">Konto: ${userJid ? userJid.split(":")[0] : "Aktiv"}</p>
          <p style="color: #64748b;">Das System ist bereit zum Senden und Empfangen von Nachrichten.</p>
        </div>
      </body>
      </html>
    `);
  }

  if (!currentQR) {
    return res.send(`
      <!DOCTYPE html>
      <html>
      <head><title>J.A.R.V.I.S. WhatsApp Bridge</title><meta charset="utf-8">
      <meta http-equiv="refresh" content="3">
      <style>body { background: #080808; color: #ff9100; font-family: monospace; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; text-align: center; }</style>
      </head>
      <body>
        <div>
          <h2>Initialisiere WhatsApp Socket...</h2>
          <p>QR-Code wird generiert, bitte kurz warten (Aktualisiert automatisch)...</p>
        </div>
      </body>
      </html>
    `);
  }

  res.send(`
    <!DOCTYPE html>
    <html>
    <head>
      <title>J.A.R.V.I.S. WhatsApp Pairing</title>
      <meta charset="utf-8">
      <meta http-equiv="refresh" content="20">
      <style>
        body { background: #080808; color: #fff; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; }
        .card { background: #0d1117; border: 1px solid #00f0ff40; border-radius: 12px; padding: 28px; text-align: center; max-width: 420px; box-shadow: 0 0 30px rgba(0, 240, 255, 0.15); }
        h2 { color: #00f0ff; margin-top: 0; font-family: monospace; }
        p { font-size: 13px; color: #94a3b8; line-height: 1.5; }
        #qrcode { background: white; padding: 16px; border-radius: 8px; display: inline-block; margin: 16px 0; }
        .footer { font-size: 11px; color: #64748b; font-family: monospace; margin-top: 12px; }
      </style>
      <script src="https://cdn.jsdelivr.net/npm/qrcodejs@1.0.0/qrcode.min.js"></script>
    </head>
    <body>
      <div class="card">
        <h2>J.A.R.V.I.S. PAIRING</h2>
        <p>1. WhatsApp auf dem Handy öffnen<br>2. <b>Verknüpfte Geräte</b> antippen<br>3. Diesen QR-Code scannen:</p>
        <div id="qrcode"></div>
        <div class="footer">Aktualisiert automatisch alle 20 Sekunden</div>
      </div>
      <script>
        new QRCode(document.getElementById("qrcode"), {
          text: ${JSON.stringify(currentQR)},
          width: 256,
          height: 256
        });
      </script>
    </body>
    </html>
  `);
});

// 3. Nachricht senden (POST /send)
app.post("/send", async (req, res) => {
  const { recipient, message } = req.body;

  if (!message || typeof message !== "string") {
    return res.status(400).json({ success: false, error: "Feld 'message' ist erforderlich." });
  }

  if (!isConnected || !sock) {
    return res.status(503).json({
      success: false,
      error: "WhatsApp Bridge ist noch nicht verbunden. Bitte QR-Code scannen (http://localhost:3001/qr oder im Terminal)."
    });
  }

  try {
    // Telefonnummer normalisieren
    let rawNum = String(recipient || "").replace(/[^0-9]/g, "");
    if (!rawNum) {
      return res.status(400).json({ success: false, error: "Ungültige oder fehlende Telefonnummer." });
    }

    // JID erzeugen (z. B. 491500000000@s.whatsapp.net)
    const jid = `${rawNum}@s.whatsapp.net`;

    // Pacing Queue: Mindestens 800ms Abstand zwischen Nachrichten, um Signal-Ratchet Kollisionen zu verhindern
    await (lastSendPromise = lastSendPromise.catch(() => {}).then(() => new Promise(r => setTimeout(r, 800))));

    console.log(`[WhatsApp Outbound] Sende Nachricht an ${jid}: "${message.substring(0, 40)}..."`);
    const sentMsg = await sock.sendMessage(jid, { text: message.trim() });
    if (sentMsg && sentMsg.key && sentMsg.key.id) {
      recentSentMessageIds.add(sentMsg.key.id);
      setTimeout(() => recentSentMessageIds.delete(sentMsg.key.id), 60000);
      autoDoc.recordMessage(sentMsg.key.id, sentMsg.message, message.trim(), jid);
    }

    res.json({
      success: true,
      recipient: "+" + rawNum,
      jid,
      messageId: sentMsg.key.id,
      timestamp: sentMsg.messageTimestamp
    });
  } catch (err) {
    console.error("[WhatsApp Outbound Fehler]", err);
    res.status(500).json({
      success: false,
      error: `Fehler beim Absenden der Nachricht: ${err.message}`
    });
  }
});

// 4. Auto-Doc Status & Selbstreparatur
app.get("/auto-doc/status", (req, res) => {
  res.json(autoDoc.getStatus());
});

app.post("/auto-doc/heal", async (req, res) => {
  const target = req.body.target || req.body.identifier || req.body.jid;
  const reason = req.body.reason || "Manuelle Auto-Doc Reparatur";
  const success = await autoDoc.healSession(target, reason);
  res.json({ success, target, message: success ? `Selbstheilung für ${target} erfolgreich durchgeführt.` : `Keine Heilung für ${target} erforderlich oder Rate-Limit aktiv.` });
});

app.post("/auto-doc/prune", (req, res) => {
  const pruned = autoDoc.pruneStaleClosedSessions();
  res.json({ success: true, pruned, message: `${pruned} veraltete geschlossene Sitzungen bereinigt.` });
});

app.post("/auto-doc/resend-last", async (req, res) => {
  const jid = req.body.jid || (req.body.recipient ? `${req.body.recipient.replace(/[^0-9]/g, "")}@s.whatsapp.net` : null);
  if (!jid) return res.status(400).json({ success: false, error: "JID oder Empfänger fehlt." });
  const result = await autoDoc.resendLastMessage(jid);
  res.json(result);
});

// 5. Bad-MAC / Desynchronisierte Sessions reparieren
app.post("/repair-sessions", (req, res) => {
  try {
    const files = fs.readdirSync(AUTH_DIR);
    let cleaned = 0;
    const backupDir = path.join(AUTH_DIR, "backup_sessions");
    if (!fs.existsSync(backupDir)) fs.mkdirSync(backupDir, { recursive: true });

    for (const f of files) {
      if (f.startsWith("session-") && f.endsWith(".json")) {
        fs.renameSync(path.join(AUTH_DIR, f), path.join(backupDir, f));
        cleaned++;
      }
    }
    console.log(`[Session Repair] ${cleaned} Session-Dateien bereinigt. Re-Handshake wird beim nächsten Paket automatisch initiiert.`);
    res.json({ success: true, message: `${cleaned} Session-Dateien bereinigt. Neuer Handshake initiiert.` });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// 4. Session beenden / Abmelden
app.post("/logout", async (req, res) => {
  try {
    if (sock) {
      await sock.logout();
    }
    fs.rmSync(AUTH_DIR, { recursive: true, force: true });
    fs.mkdirSync(AUTH_DIR, { recursive: true });
    res.json({ success: true, message: "WhatsApp Sitzung erfolgreich beendet und abgemeldet." });
  } catch (e) {
    res.status(500).json({ success: false, error: e.message });
  }
});

// Server starten
app.listen(PORT, HOST, () => {
  console.log(`[WhatsApp Bridge API] Hört auf http://${HOST}:${PORT}`);
  connectToJarvisBackend();
  startWhatsAppSocket();
});
