/**
 * auto_doc.js — J.A.R.V.I.S. WhatsApp Bridge Auto-Doc (Selbstheilungs-Engine)
 * 
 * Behebt autonom:
 * 1. "Warte auf diese Nachricht. Das kann einen Moment dauern." (Waiting for this message)
 *    -> Durch persistenten MessageVault & msgRetryCounterCache / placeholderResendCache
 * 2. "Closing session" & "Decrypted message with closed session"
 *    -> Durch automatisches Bereinigen veralteter geschlossener Ratchet-Sessions
 * 3. "Error: Bad MAC" / "Failed to decrypt message"
 *    -> Durch autonome Session-Reparatur und sofortigen Neu-Handshake via assertSessions
 */

const fs = require("fs");
const path = require("path");
const { NodeCache } = require("@cacheable/node-cache");

class AutoDoc {
  constructor(authDir) {
    this.authDir = authDir || path.join(__dirname, "auth_info_baileys");
    this.vaultFile = path.join(this.authDir, "messages_vault.json");
    this.backupDir = path.join(this.authDir, "backup_sessions");

    // Message Store: ID -> { message: proto.IMessage, jid: string, text: string, timestamp: number }
    this.messageVault = new Map();
    this.lastSentByJid = new Map(); // jid -> messageId

    // Caches für Baileys Retry-Handling
    this.msgRetryCounterCache = new NodeCache({ stdTTL: 3600, useClones: false });
    this.placeholderResendCache = new NodeCache({ stdTTL: 3600, useClones: false });

    // Rate-Limiting für Heilsitzungen (verhindert Heal-Loops)
    this.lastHealedAt = new Map();

    this.sockGetter = null;
    this.stats = {
      healsPerformed: 0,
      retriesServed: 0,
      staleSessionsPruned: 0,
      startedAt: new Date().toISOString()
    };

    this.initVault();
  }

  // --- 1. Persistent Message Vault ---
  initVault() {
    try {
      if (!fs.existsSync(this.authDir)) {
        fs.mkdirSync(this.authDir, { recursive: true });
      }
      if (!fs.existsSync(this.backupDir)) {
        fs.mkdirSync(this.backupDir, { recursive: true });
      }

      if (fs.existsSync(this.vaultFile)) {
        const raw = fs.readFileSync(this.vaultFile, "utf-8");
        const parsed = JSON.parse(raw);
        for (const [id, data] of Object.entries(parsed)) {
          this.messageVault.set(id, data);
          if (data.jid) {
            this.lastSentByJid.set(data.jid, id);
          }
        }
        console.log(`[Auto-Doc 🩺] MessageVault geladen: ${this.messageVault.size} Nachrichten im Cache.`);
      }
    } catch (err) {
      console.error("[Auto-Doc 🩺] Fehler beim Laden des MessageVault:", err.message);
    }
  }

  saveVaultToDisk() {
    try {
      // Beschränkung auf die neuesten 1500 Nachrichten, um Dateigröße minimal zu halten
      if (this.messageVault.size > 1500) {
        const excess = this.messageVault.size - 1500;
        const keys = this.messageVault.keys();
        for (let i = 0; i < excess; i++) {
          this.messageVault.delete(keys.next().value);
        }
      }

      const obj = Object.fromEntries(this.messageVault);
      fs.writeFileSync(this.vaultFile, JSON.stringify(obj, null, 2), "utf-8");
    } catch (err) {
      console.error("[Auto-Doc 🩺] Fehler beim Speichern des MessageVault:", err.message);
    }
  }

  recordMessage(id, messageProto, text = "", jid = "") {
    if (!id) return;
    try {
      let cleanMsg = messageProto;
      if (!cleanMsg && text) {
        cleanMsg = { conversation: text };
      }

      const entry = {
        message: cleanMsg,
        text: text || "",
        jid: jid || "",
        timestamp: Date.now()
      };

      this.messageVault.set(id, entry);
      if (jid) {
        this.lastSentByJid.set(jid, id);
      }

      // Debounced Persistierung
      if (this._saveTimeout) clearTimeout(this._saveTimeout);
      this._saveTimeout = setTimeout(() => this.saveVaultToDisk(), 1500);
    } catch (err) {
      console.error("[Auto-Doc 🩺] Fehler beim Aufzeichnen im Vault:", err.message);
    }
  }

  async getMessage(key) {
    const id = key?.id;
    if (!id) return undefined;

    // 1. Suche im In-Memory Vault
    if (this.messageVault.has(id)) {
      const entry = this.messageVault.get(id);
      this.stats.retriesServed++;
      console.log(`[Auto-Doc 🩺] Retry-Anfrage für Nachricht ${id} (JID: ${key.remoteJid}) erfolgreich aus Vault bedient.`);
      return entry.message;
    }

    // 2. Suche direkt in der Datei, falls Nachricht kurz vor Neustart gesichert wurde
    try {
      if (fs.existsSync(this.vaultFile)) {
        const raw = fs.readFileSync(this.vaultFile, "utf-8");
        const parsed = JSON.parse(raw);
        if (parsed[id] && parsed[id].message) {
          this.messageVault.set(id, parsed[id]);
          this.stats.retriesServed++;
          console.log(`[Auto-Doc 🩺] Retry-Anfrage für ${id} direkt von Disk rekonstruiert.`);
          return parsed[id].message;
        }
      }
    } catch (e) {}

    return undefined;
  }

  // --- 2. Session Healer & Pruning ---

  /**
   * Bereinigt veraltete geschlossene Sitzungen aus allen session-*.json Dateien.
   * Behebt "Decrypted message with closed session" und verhindert Session-Aufblähung.
   */
  pruneStaleClosedSessions() {
    try {
      if (!fs.existsSync(this.authDir)) return 0;
      const files = fs.readdirSync(this.authDir);
      let prunedCount = 0;

      for (const file of files) {
        if (file.startsWith("session-") && file.endsWith(".json")) {
          const filePath = path.join(this.authDir, file);
          try {
            const content = JSON.parse(fs.readFileSync(filePath, "utf-8"));
            const sessionKey = content._sessions ? "_sessions" : (content.sessions ? "sessions" : null);

            if (sessionKey && content[sessionKey]) {
              const sessions = content[sessionKey];
              const entries = Object.entries(sessions);

              // Wenn mehr als 2 Sitzungen existieren, alte geschlossene bereinigen:
              if (entries.length > 2) {
                // Finde aktive Sitzung (closed === -1)
                const activeEntries = entries.filter(([k, v]) => v.indexInfo?.closed === -1);
                // Finde geschlossene Sitzungen, sortiert nach Nutzungszeit/Schließzeitpunkt
                const closedEntries = entries
                  .filter(([k, v]) => v.indexInfo?.closed !== -1)
                  .sort((a, b) => (b[1].indexInfo?.closed || 0) - (a[1].indexInfo?.closed || 0));

                // Behalte aktive Sitzung + maximal 1 jüngste geschlossene Sitzung (für evtl. noch eintreffende Pakete)
                const toKeep = new Map();
                for (const [k, v] of activeEntries) toKeep.set(k, v);
                if (closedEntries.length > 0) {
                  toKeep.set(closedEntries[0][0], closedEntries[0][1]);
                }

                if (toKeep.size < entries.length) {
                  content[sessionKey] = Object.fromEntries(toKeep);
                  fs.writeFileSync(filePath, JSON.stringify(content), "utf-8");
                  prunedCount += (entries.length - toKeep.size);
                }
              }
            }
          } catch (e) {
            // Defekte JSON-Datei ignorieren oder durch healSession behandeln
          }
        }
      }

      if (prunedCount > 0) {
        this.stats.staleSessionsPruned += prunedCount;
        console.log(`[Auto-Doc 🩺] ${prunedCount} veraltete geschlossene Sitzungen bereinigt.`);
      }
      return prunedCount;
    } catch (err) {
      console.error("[Auto-Doc 🩺] Fehler beim Pruning geschlossener Sessions:", err.message);
      return 0;
    }
  }

  /**
   * Vollständige Selbstreparatur für eine bestimmte Identifikationsnummer (z. B. Lisa LID oder Telefon).
   * Schiebt defekte Session-Dateien ins Backup und forciert sofort einen frischen PreKey-Austausch.
   */
  async healSession(identifier, reason = "Automatische Reparatur") {
    if (!identifier) return false;
    const cleanId = String(identifier).replace(/[^0-9]/g, "");
    if (!cleanId) return false;

    // Rate-Limiting: maximal 1x alle 10 Sekunden pro Identität reparieren
    const now = Date.now();
    const last = this.lastHealedAt.get(cleanId) || 0;
    if (now - last < 10000) {
      return false;
    }
    this.lastHealedAt.set(cleanId, now);

    console.log(`[Auto-Doc 🩺] STARTE SELBSTHEILUNG für ${cleanId} (Grund: ${reason})...`);
    let moved = 0;

    try {
      const files = fs.readdirSync(this.authDir);
      for (const f of files) {
        if (f.startsWith(`session-${cleanId}`) && f.endsWith(".json")) {
          const src = path.join(this.authDir, f);
          const dst = path.join(this.backupDir, `${f}.${now}.bak`);
          fs.renameSync(src, dst);
          moved++;
        }
      }

      const sock = this.sockGetter ? this.sockGetter() : null;
      if (sock && sock.assertSessions) {
        // Frischen Session-Handshake mit WhatsApp PreKey Server anfordern
        const targetJid = cleanId.includes("@") ? cleanId : (cleanId.length > 13 ? `${cleanId}@lid` : `${cleanId}@s.whatsapp.net`);
        console.log(`[Auto-Doc 🩺] Fordere frischen PreKey-Handshake für ${targetJid} an...`);
        await sock.assertSessions([targetJid], true).catch(e => {
          console.warn("[Auto-Doc 🩺] assertSessions Hinweis:", e.message);
        });
      }

      this.stats.healsPerformed++;
      console.log(`[Auto-Doc 🩺] ✓ Selbstheilung für ${cleanId} abgeschlossen (${moved} Session-Dateien archiviert).`);
      return true;
    } catch (err) {
      console.error(`[Auto-Doc 🩺] Fehler während Selbstheilung für ${cleanId}:`, err.message);
      return false;
    }
  }

  // --- 3. Log-Monitor & Hook ---

  /**
   * Installiert intelligente Überwachung für libsignal-Ausgaben.
   * Fängt "Bad MAC", "Failed to decrypt" und "closed session" automatisch ab.
   */
  installLogMonitor(sockGetter) {
    this.sockGetter = sockGetter;

    const originalWarn = console.warn;
    const originalError = console.error;
    const originalInfo = console.info;

    console.info = (...args) => {
      const first = String(args[0] || "");
      if (first.startsWith("Closing session:")) {
        // Unterdrücke riesigen internen libsignal-Objekt-Dump im Terminal
        console.log("[Signal Protocol] Ratchet-Sitzung erfolgreich aktualisiert.");
        return;
      }
      originalInfo.apply(console, args);
    };

    console.warn = (...args) => {
      const str = args.map(a => (typeof a === "object" ? JSON.stringify(a) : String(a))).join(" ");

      if (str.includes("Closing open session in favor of incoming prekey bundle")) {
        console.log("[Signal Protocol] Neuer PreKey-Schlüsselaustausch synchronisiert.");
        return;
      }

      if (str.includes("Decrypted message with closed session")) {
        // Gelegentlich aufräumen, damit sich geschlossene Sitzungen nicht stapeln
        setTimeout(() => this.pruneStaleClosedSessions(), 2000);
        return;
      }

      originalWarn.apply(console, args);
    };

    console.error = (...args) => {
      originalError.apply(console, args);
      const str = args.map(a => (typeof a === "object" ? (a?.stack || JSON.stringify(a)) : String(a))).join(" ");

      if (str.includes("Bad MAC") || str.includes("Failed to decrypt message with any known session")) {
        // Suche nach Identifikatoren im Log
        const match = str.match(/(?:session-|at async )([0-9]{10,16})/);
        if (match && match[1]) {
          const brokenId = match[1];
          this.healSession(brokenId, "Bad MAC Log-Erkennung");
        } else {
          // Falls kein direkter Match: Pruning und Prüfung ausführen
          this.pruneStaleClosedSessions();
        }
      }
    };

    console.log("[Auto-Doc 🩺] Log-Überwachung & Autonome Fehlererkennung aktiv.");
  }

  /**
   * Resend-Hilfe für die letzte an eine JID gesendete Nachricht.
   * Löst "Warte auf diese Nachricht..." manuell oder proaktiv auf.
   */
  async resendLastMessage(jid) {
    const sock = this.sockGetter ? this.sockGetter() : null;
    if (!sock) return { success: false, error: "Socket offline" };

    const lastId = this.lastSentByJid.get(jid);
    if (!lastId || !this.messageVault.has(lastId)) {
      return { success: false, error: `Keine archivierte Nachricht für ${jid} gefunden.` };
    }

    const entry = this.messageVault.get(lastId);
    try {
      console.log(`[Auto-Doc 🩺] Sende letzte Nachricht (${lastId}) erneut an ${jid}...`);
      await sock.assertSessions([jid], true).catch(() => {});
      const sent = await sock.sendMessage(jid, { text: entry.text || "Nachricht wird aktualisiert..." });
      return { success: true, messageId: sent?.key?.id };
    } catch (err) {
      return { success: false, error: err.message };
    }
  }

  getStatus() {
    return {
      auto_doc_active: true,
      vault_size: this.messageVault.size,
      stats: this.stats,
      retry_cache_stats: {
        keys: this.msgRetryCounterCache.keys().length,
        placeholder_keys: this.placeholderResendCache.keys().length
      }
    };
  }
}

module.exports = AutoDoc;
