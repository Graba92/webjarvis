"use client";

import React, { useState, useEffect, useRef } from "react";
import { socketManager } from "@/lib/websocket";
import { BackupEntry } from "@/lib/types";
import { 
  Archive, 
  UploadCloud, 
  Download, 
  Trash2, 
  RefreshCw, 
  ShieldCheck, 
  Key, 
  Tag, 
  X, 
  CheckCircle2, 
  AlertTriangle,
  RotateCcw,
  Clock,
  HardDrive
} from "lucide-react";

interface BackupModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const BackupModal: React.FC<BackupModalProps> = ({ isOpen, onClose }) => {
  const [activeTab, setActiveTab] = useState<"create" | "upload" | "list">("create");
  const [backups, setBackups] = useState<BackupEntry[]>([]);
  const [label, setLabel] = useState("");
  const [passphrase, setPassphrase] = useState("");
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadPassphrase, setUploadPassphrase] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [feedback, setFeedback] = useState<{ type: "success" | "error" | "info"; msg: string } | null>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Helper to trigger browser download from base64
  const triggerBrowserDownload = (filename: string, base64Data: string) => {
    try {
      const byteCharacters = atob(base64Data);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: "application/zip" });
      const blobUrl = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = blobUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(blobUrl);
    } catch (err) {
      console.error("Fehler beim Browser-Download:", err);
    }
  };

  useEffect(() => {
    if (!isOpen) return;

    // Listen for backups list updates
    const unsubList = socketManager.onBackupsList((list) => {
      setBackups(list || []);
    });

    // Listen for single download requests
    const unsubDownload = socketManager.onBackupDownload((item) => {
      triggerBrowserDownload(item.filename, item.data_base64);
      setFeedback({
        type: "success",
        msg: `Download von '${item.filename}' (${item.size_kb} KB) erfolgreich gestartet!`
      });
      setTimeout(() => setFeedback(null), 4000);
    });

    // Listen for export results
    const unsubExport = socketManager.onBrainExport((res) => {
      setIsProcessing(false);
      if (res.success) {
        if (res.data_base64 && res.filename) {
          triggerBrowserDownload(res.filename, res.data_base64);
        }
        setFeedback({
          type: "success",
          msg: res.message || `Brain-Backup '${res.filename || "Archiv"}' erfolgreich erstellt & heruntergeladen!`
        });
        setLabel("");
        setPassphrase("");
        socketManager.requestBackupsList();
      } else {
        setFeedback({
          type: "error",
          msg: res.error || "Fehler beim Erstellen des Backups."
        });
      }
      setTimeout(() => setFeedback(null), 5000);
    });

    // Listen for import / restore results
    const unsubImport = socketManager.onBrainImport((res) => {
      setIsProcessing(false);
      if (res.success) {
        setFeedback({
          type: "success",
          msg: res.result || "Gedächtnis-Wiederherstellung erfolgreich! Alle Module wurden nahtlos aktualisiert."
        });
        setUploadFile(null);
        setUploadPassphrase("");
        socketManager.requestBackupsList();
      } else {
        setFeedback({
          type: "error",
          msg: res.error || "Fehler bei der Wiederherstellung des Backups."
        });
      }
      setTimeout(() => setFeedback(null), 5000);
    });

    // Request initial backup list
    socketManager.requestBackupsList();

    return () => {
      unsubList();
      unsubDownload();
      unsubExport();
      unsubImport();
    };
  }, [isOpen]);

  if (!isOpen) return null;

  // Handle manual backup creation & download
  const handleCreateBackup = (e: React.FormEvent) => {
    e.preventDefault();
    if (isProcessing) return;
    setIsProcessing(true);
    setFeedback({
      type: "info",
      msg: "Erstelle transaktionssicheres VACUUM-Backup (Gedächtnis, Kalender, LanceDB)..."
    });
    socketManager.exportBrain(label.trim(), passphrase.trim() || undefined);
  };

  // Handle file selection
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.name.endsWith(".zip")) {
        setFeedback({ type: "error", msg: "Bitte wähle eine gültige .zip Backup-Datei aus." });
        setTimeout(() => setFeedback(null), 3500);
        return;
      }
      setUploadFile(file);
    }
  };

  // Handle uploading and restoring backup
  const handleUploadAndRestore = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile || isProcessing) return;

    setIsProcessing(true);
    setFeedback({
      type: "info",
      msg: `Lese und übertrage '${uploadFile.name}' (${Math.round(uploadFile.size / 1024)} KB)...`
    });

    try {
      const reader = new FileReader();
      reader.onload = () => {
        const arrayBuffer = reader.result as ArrayBuffer;
        const bytes = new Uint8Array(arrayBuffer);
        let binary = "";
        for (let i = 0; i < bytes.byteLength; i++) {
          binary += String.fromCharCode(bytes[i]);
        }
        const base64Data = btoa(binary);
        socketManager.uploadAndImportBrain(
          uploadFile.name,
          base64Data,
          uploadPassphrase.trim() || undefined
        );
      };
      reader.onerror = () => {
        setIsProcessing(false);
        setFeedback({ type: "error", msg: "Fehler beim Lesen der lokalen Backup-Datei." });
      };
      reader.readAsArrayBuffer(uploadFile);
    } catch (err: any) {
      setIsProcessing(false);
      setFeedback({ type: "error", msg: `Upload-Fehler: ${err?.message || err}` });
    }
  };

  // Handle direct restore of existing backup
  const handleRestoreExisting = (path: string) => {
    if (isProcessing) return;
    if (confirm("Möchtest du dieses Backup wirklich einspielen? Aktuelle Gedächtnis- und Kalenderstände werden überschrieben.")) {
      setIsProcessing(true);
      setFeedback({ type: "info", msg: "Stelle Systemzustand aus dem gewählten Backup wieder her..." });
      socketManager.importBrain(path);
    }
  };

  // Handle direct download of existing backup
  const handleDownloadExisting = (filename: string) => {
    socketManager.downloadBackup(filename);
  };

  // Handle deletion of existing backup
  const handleDeleteExisting = (filename: string) => {
    if (confirm(`Möchtest du das Backup '${filename}' wirklich dauerhaft löschen?`)) {
      socketManager.deleteBackup(filename);
      setFeedback({ type: "info", msg: `Backup '${filename}' wird gelöscht...` });
      setTimeout(() => setFeedback(null), 2500);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 animate-in fade-in duration-200">
      <div className="relative w-full max-w-3xl rounded-2xl glass-panel border border-[#00d4ff]/40 bg-[#0d1117]/95 shadow-2xl p-6 overflow-hidden flex flex-col max-h-[90vh]">
        
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#1f242d] pb-4 mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-[#22c55e]/10 text-[#22c55e] border border-[#22c55e]/30 shadow-[0_0_15px_rgba(34,197,94,0.2)]">
              <Archive className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-white uppercase tracking-wider">
                  Brain Vault — 1-Click Backup & Restore
                </h2>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#22c55e]/20 text-[#22c55e] font-mono border border-[#22c55e]/30">
                  SQLite VACUUM + LanceDB
                </span>
              </div>
              <p className="text-xs text-gray-400">
                Sichere oder stelle Gedächtnis, Kalender, SOUL.md & Vektordatenbank nahtlos wieder her.
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center gap-2 mb-4 border-b border-[#1f242d] pb-3 font-mono text-xs">
          <button
            onClick={() => setActiveTab("create")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg transition-all ${
              activeTab === "create"
                ? "bg-[#00d4ff]/20 text-[#00d4ff] border border-[#00d4ff]/50 font-bold shadow-[0_0_10px_rgba(0,212,255,0.2)]"
                : "text-gray-400 hover:text-white hover:bg-white/5 border border-transparent"
            }`}
          >
            <Download className="w-3.5 h-3.5" />
            <span>1. Backup erstellen & herunterladen</span>
          </button>

          <button
            onClick={() => setActiveTab("upload")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg transition-all ${
              activeTab === "upload"
                ? "bg-[#22c55e]/20 text-[#22c55e] border border-[#22c55e]/50 font-bold shadow-[0_0_10px_rgba(34,197,94,0.2)]"
                : "text-gray-400 hover:text-white hover:bg-white/5 border border-transparent"
            }`}
          >
            <UploadCloud className="w-3.5 h-3.5" />
            <span>2. Backup hochladen & einspielen</span>
          </button>

          <button
            onClick={() => setActiveTab("list")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg transition-all ${
              activeTab === "list"
                ? "bg-purple-500/20 text-purple-400 border border-purple-500/50 font-bold shadow-[0_0_10px_rgba(168,85,247,0.2)]"
                : "text-gray-400 hover:text-white hover:bg-white/5 border border-transparent"
            }`}
          >
            <HardDrive className="w-3.5 h-3.5" />
            <span>3. Vorhandene Backups ({backups.length})</span>
          </button>
        </div>

        {/* Feedback Alert */}
        {feedback && (
          <div className={`mb-4 p-3 rounded-xl border text-xs flex items-center gap-2 animate-in fade-in ${
            feedback.type === "success"
              ? "bg-[#22c55e]/20 border-[#22c55e]/40 text-[#22c55e]"
              : feedback.type === "error"
              ? "bg-red-500/20 border-red-500/40 text-red-300"
              : "bg-[#00d4ff]/20 border-[#00d4ff]/40 text-[#00d4ff]"
          }`}>
            {feedback.type === "success" && <CheckCircle2 className="w-4 h-4 shrink-0" />}
            {feedback.type === "error" && <AlertTriangle className="w-4 h-4 shrink-0" />}
            {feedback.type === "info" && <RefreshCw className="w-4 h-4 shrink-0 animate-spin" />}
            <span className="font-mono">{feedback.msg}</span>
          </div>
        )}

        {/* Tab 1: Create & Download */}
        {activeTab === "create" && (
          <form onSubmit={handleCreateBackup} className="space-y-4 flex-1 flex flex-col justify-between overflow-y-auto pr-1">
            <div className="space-y-3.5">
              <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/10 text-xs text-gray-300 leading-relaxed">
                <div className="font-semibold text-white mb-1 flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-[#22c55e]" />
                  Konsistente Komplettsicherung des KI-Gedächtnisses
                </div>
                Das Archiv sichert alle Langzeitfakten (<code className="text-gray-400">long_term.json</code>), den SQLite-Kalender (<code className="text-gray-400">calendar.db</code> via VACUUM INTO), Vektordatenbank (<code className="text-gray-400">lancedb_data/</code>), MCP-Tools und die Identitätsdateien (<code className="text-gray-400">SOUL.md</code>).
              </div>

              <div>
                <label className="block text-[11px] font-mono text-gray-400 mb-1 flex items-center gap-1.5">
                  <Tag className="w-3 h-3 text-[#00d4ff]" />
                  BACKUP-BESCHRIFTUNG / LABEL (OPTIONAL)
                </label>
                <input
                  type="text"
                  value={label}
                  onChange={(e) => setLabel(e.target.value)}
                  placeholder="z. B. Vor_CachyOS_Update, Stabil_20260920, Stand_Neue_Termine..."
                  className="w-full px-3 py-2 text-xs bg-black/40 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-[#00d4ff] transition-colors font-mono"
                />
                <p className="text-[10px] text-gray-500 mt-1 font-mono">
                  Wird direkt in den Dateinamen des ZIP-Archivs eingebettet.
                </p>
              </div>

              <div>
                <label className="block text-[11px] font-mono text-gray-400 mb-1 flex items-center gap-1.5">
                  <Key className="w-3 h-3 text-amber-400" />
                  VERSCHLÜSSELUNGS-PASSWORT (OPTIONAL)
                </label>
                <input
                  type="password"
                  value={passphrase}
                  onChange={(e) => setPassphrase(e.target.value)}
                  placeholder="Freilassen für unverschlüsseltes ZIP-Archiv"
                  className="w-full px-3 py-2 text-xs bg-black/40 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-amber-400 transition-colors font-mono"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isProcessing}
              className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-[#00d4ff]/20 to-[#22c55e]/20 hover:from-[#00d4ff]/30 hover:to-[#22c55e]/30 text-white border border-[#00d4ff]/50 hover:border-[#00d4ff] font-semibold text-xs transition-all shadow-[0_0_20px_rgba(0,212,255,0.2)] flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              <Download className={`w-4 h-4 text-[#00d4ff] ${isProcessing ? "animate-bounce" : ""}`} />
              <span>{isProcessing ? "Backup wird generiert & übertragen..." : "Backup jetzt erstellen & herunterladen (ZIP)"}</span>
            </button>
          </form>
        )}

        {/* Tab 2: Upload & Restore */}
        {activeTab === "upload" && (
          <form onSubmit={handleUploadAndRestore} className="space-y-4 flex-1 flex flex-col justify-between overflow-y-auto pr-1">
            <div className="space-y-3.5">
              <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-200 leading-relaxed">
                <div className="font-semibold text-amber-300 mb-1 flex items-center gap-1.5">
                  <RotateCcw className="w-4 h-4 text-amber-400" />
                  Nahtloser System-Restore aus bestehendem ZIP-Archiv
                </div>
                Lade ein früheres Brain-Vault Backup hoch. Nach dem Entpacken werden Termine, Langzeitgedächtnis und Agenten-Persönlichkeit <strong>in Echtzeit ohne Neustart</strong> synchronisiert, sodass du nahtlos weiterarbeiten kannst.
              </div>

              {/* File Dropzone */}
              <div
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-white/15 hover:border-[#22c55e]/50 rounded-xl p-6 text-center cursor-pointer bg-white/[0.01] hover:bg-white/[0.03] transition-all"
              >
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  accept=".zip"
                  className="hidden"
                />
                <UploadCloud className="w-10 h-10 text-[#22c55e] mx-auto mb-2" />
                <div className="text-xs font-semibold text-white mb-1">
                  {uploadFile ? uploadFile.name : "Klicke hier, um ein Backup (.zip) auszuwählen"}
                </div>
                <div className="text-[11px] text-gray-400 font-mono">
                  {uploadFile ? `${Math.round(uploadFile.size / 1024)} KB ausgewählt` : "Unterstützt alle Jarvis Brain-Vault ZIPs"}
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-mono text-gray-400 mb-1 flex items-center gap-1.5">
                  <Key className="w-3 h-3 text-amber-400" />
                  PASSWORT (NUR FALLS BEIM ERSTELLEN GESETZT)
                </label>
                <input
                  type="password"
                  value={uploadPassphrase}
                  onChange={(e) => setUploadPassphrase(e.target.value)}
                  placeholder="Passwort für verschlüsselte Archive..."
                  className="w-full px-3 py-2 text-xs bg-black/40 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-amber-400 transition-colors font-mono"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={!uploadFile || isProcessing}
              className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-[#22c55e]/20 to-emerald-500/20 hover:from-[#22c55e]/30 hover:to-emerald-500/30 text-[#22c55e] border border-[#22c55e]/50 hover:border-[#22c55e] font-semibold text-xs transition-all shadow-[0_0_20px_rgba(34,197,94,0.2)] flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              <UploadCloud className={`w-4 h-4 ${isProcessing ? "animate-spin" : ""}`} />
              <span>{isProcessing ? "Backup wird wiederhergestellt..." : "Backup hochladen & System nahtlos fortsetzen"}</span>
            </button>
          </form>
        )}

        {/* Tab 3: List & Manage Backups */}
        {activeTab === "list" && (
          <div className="flex-1 flex flex-col overflow-y-auto space-y-2.5 pr-1">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-mono text-gray-400">
                Gespeicherte Archive in <code className="text-[#00d4ff]">backend/backups/</code>
              </span>
              <button
                onClick={() => socketManager.requestBackupsList()}
                className="text-xs font-mono text-[#00d4ff] hover:underline flex items-center gap-1"
              >
                <RefreshCw className="w-3 h-3" />
                Aktualisieren
              </button>
            </div>

            {backups.length === 0 ? (
              <div className="p-8 text-center border border-dashed border-white/10 rounded-xl bg-white/[0.02]">
                <Archive className="w-8 h-8 text-gray-600 mx-auto mb-2" />
                <p className="text-xs text-gray-400">Keine lokalen Backups im Speicherverzeichnis gefunden.</p>
                <p className="text-[11px] text-gray-500 mt-1">
                  Erstelle im ersten Tab ein Backup, um es hier dauerhaft verfügbar zu haben.
                </p>
              </div>
            ) : (
              backups.map((bk) => (
                <div
                  key={bk.filename}
                  className="p-3 rounded-xl border border-white/10 bg-white/[0.03] hover:border-[#00d4ff]/40 hover:bg-white/[0.05] transition-all flex items-center justify-between gap-3"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-xs font-semibold text-white font-mono truncate">
                        {bk.filename}
                      </span>
                      {bk.label && (
                        <span className="text-[10px] px-2 py-0.5 rounded-md bg-[#00d4ff]/10 text-[#00d4ff] border border-[#00d4ff]/30 font-mono">
                          {bk.label}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 text-[11px] text-gray-400 font-mono mt-1">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3 text-gray-500" />
                        {bk.created_at}
                      </span>
                      <span>•</span>
                      <span>{bk.size_kb} KB</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    {/* Direct Download Button */}
                    <button
                      onClick={() => handleDownloadExisting(bk.filename)}
                      title="Archiv auf Rechner herunterladen"
                      className="p-1.5 rounded-lg bg-white/5 hover:bg-[#00d4ff]/20 text-gray-300 hover:text-[#00d4ff] border border-white/10 hover:border-[#00d4ff]/40 transition-colors"
                    >
                      <Download className="w-3.5 h-3.5" />
                    </button>

                    {/* Restore Button */}
                    <button
                      onClick={() => handleRestoreExisting(bk.path)}
                      title="Aus diesem Backup wiederherstellen"
                      className="p-1.5 rounded-lg bg-white/5 hover:bg-[#22c55e]/20 text-gray-300 hover:text-[#22c55e] border border-white/10 hover:border-[#22c55e]/40 transition-colors"
                    >
                      <RotateCcw className="w-3.5 h-3.5" />
                    </button>

                    {/* Delete Button */}
                    <button
                      onClick={() => handleDeleteExisting(bk.filename)}
                      title="Backup löschen"
                      className="p-1.5 rounded-lg bg-white/5 hover:bg-red-500/20 text-gray-300 hover:text-red-400 border border-white/10 hover:border-red-500/40 transition-colors"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Footer info */}
        <div className="mt-4 pt-3 border-t border-[#1f242d] flex items-center justify-between text-[11px] text-gray-500 font-mono">
          <span>Speicherort: <code className="text-gray-400">backend/backups/</code></span>
          <span>Integrität: <code className="text-[#22c55e]">Atomare VACUUM-Snapshots</code></span>
        </div>

      </div>
    </div>
  );
};
