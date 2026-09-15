"use client";

import React, { useState, useEffect } from "react";
import { socketManager } from "@/lib/websocket";
import { KeyRound, ShieldCheck, ShieldAlert, Eye, EyeOff, ExternalLink, X, Save } from "lucide-react";

interface ApiKeyModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ApiKeyModal: React.FC<ApiKeyModalProps> = ({ isOpen, onClose }) => {
  const [apiKeyStatus, setApiKeyStatus] = useState<{ configured: boolean; masked_key: string }>({
    configured: false,
    masked_key: ""
  });
  const [keyInput, setKeyInput] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    const unsub = socketManager.onApiKeyStatus(setApiKeyStatus);
    return () => unsub();
  }, []);

  if (!isOpen) return null;

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    if (!keyInput.trim()) return;
    socketManager.setApiKey(keyInput.trim());
    setSavedSuccess(true);
    setTimeout(() => {
      setSavedSuccess(false);
      setKeyInput("");
      onClose();
    }, 1200);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="w-full max-w-md rounded-2xl glass-panel-glow bg-[#0a0d14]/95 p-5 shadow-2xl border border-[#00d4ff]/40 animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#1f242d] pb-3 mb-4">
          <div className="flex items-center gap-2">
            <KeyRound className="w-5 h-5 text-[#00d4ff]" />
            <div>
              <h2 className="text-sm font-black tracking-wider uppercase text-white">
                Gemini API Key Setup
              </h2>
              <p className="text-[10px] text-gray-400">
                Google AI Studio · Live API WebSocket Auth
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-white/10 text-gray-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Status Badge */}
        <div className="rounded-xl bg-[#080a0f] border border-[#1f242d] p-3 mb-4">
          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-400 font-medium">Aktueller Status:</span>
            {apiKeyStatus.configured ? (
              <span className="flex items-center gap-1.5 font-bold text-[#22c55e]">
                <ShieldCheck className="w-4 h-4 text-[#22c55e]" />
                <span>Aktiv ({apiKeyStatus.masked_key})</span>
              </span>
            ) : (
              <span className="flex items-center gap-1.5 font-bold text-[#ff6b00]">
                <ShieldAlert className="w-4 h-4 text-[#ff6b00] animate-pulse" />
                <span>Nicht konfiguriert</span>
              </span>
            )}
          </div>
        </div>

        {/* Formular */}
        <form onSubmit={handleSave} className="flex flex-col gap-3">
          <div>
            <label className="text-[11px] font-semibold text-gray-300 block mb-1.5">
              Neuen Google Gemini API Key eingeben:
            </label>
            <div className="relative">
              <input
                type={showKey ? "text" : "password"}
                placeholder="AIzaSy..."
                value={keyInput}
                onChange={(e) => setKeyInput(e.target.value)}
                className="w-full pl-3 pr-10 py-2 rounded-lg bg-[#080a0f] border border-[#1f242d] text-xs text-white placeholder-gray-500 font-mono focus:outline-none focus:border-[#00d4ff] transition-colors"
              />
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="absolute right-2.5 top-2.5 text-gray-400 hover:text-white transition-colors"
              >
                {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <div className="flex items-center justify-between text-[11px] text-gray-400 mt-1">
            <span>Noch keinen Key?</span>
            <a
              href="https://aistudio.google.com/app/apikey"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-[#00d4ff] hover:underline"
            >
              <span>Google AI Studio öffnen</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>

          <button
            type="submit"
            disabled={!keyInput.trim() || savedSuccess}
            className={`mt-2 flex items-center justify-center gap-2 py-2.5 rounded-xl font-bold text-xs tracking-wider transition-all shadow-lg ${
              savedSuccess
                ? "bg-[#22c55e] text-black shadow-[#22c55e]/20"
                : "bg-gradient-to-r from-[#00d4ff] to-[#a855f7] text-black hover:opacity-95 shadow-[#00d4ff]/20 disabled:opacity-40"
            }`}
          >
            {savedSuccess ? (
              <>
                <ShieldCheck className="w-4 h-4" />
                <span>KEY GESPEICHERT & VERBUNDEN!</span>
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                <span>SPEICHERN & LIVE-SITZUNG STARTEN</span>
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};
