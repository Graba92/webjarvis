"use client";

import React, { useState } from "react";
import { socketManager } from "@/lib/websocket";
import { Feather, FileText, Send, Sparkles, X } from "lucide-react";

interface ContentStudioProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ContentStudio: React.FC<ContentStudioProps> = ({ isOpen, onClose }) => {
  const [topic, setTopic] = useState("");
  const [format, setFormat] = useState<"video" | "summary" | "code">("video");
  const [draft, setDraft] = useState("");

  if (!isOpen) return null;

  const handleGenerate = () => {
    if (!topic.trim()) return;
    const prompt = `Erstelle als Jarvis ein strukturiertes ${format === "video" ? "YouTube-Videoskript mit Hook, Hauptteil und Call-to-Action" : format === "summary" ? "prägnantes Executive Summary" : "technisches Architekturdokument"} zum Thema: "${topic}".`;
    socketManager.sendText(prompt);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="w-full max-w-lg rounded-2xl glass-panel-glow bg-[#0a0d14]/95 p-5 shadow-2xl border border-[#a855f7]/40 animate-in fade-in zoom-in-95 duration-150">
        <div className="flex items-center justify-between border-b border-[#1f242d] pb-3 mb-4">
          <div className="flex items-center gap-2">
            <Feather className="w-5 h-5 text-[#a855f7]" />
            <div>
              <h2 className="text-sm font-black tracking-wider uppercase text-white">
                Autonomous Content Studio
              </h2>
              <p className="text-[10px] text-gray-400">
                Videoskripte · Markdown Composer · Social Media Funnels
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

        <div className="flex flex-col gap-3">
          <div>
            <label className="text-[11px] font-semibold text-gray-300 block mb-1">
              Thema oder Idee eingeben:
            </label>
            <input
              type="text"
              placeholder="z.B. CachyOS Kernel-Optimierungen für Gaming..."
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-[#080a0f] border border-[#1f242d] text-xs text-white placeholder-gray-500 focus:outline-none focus:border-[#a855f7] transition-colors"
            />
          </div>

          <div>
            <label className="text-[11px] font-semibold text-gray-300 block mb-1">
              Format wählen:
            </label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { id: "video", label: "YouTube Skript" },
                { id: "summary", label: "Briefing Summary" },
                { id: "code", label: "Architektur Doc" }
              ].map(f => (
                <button
                  key={f.id}
                  onClick={() => setFormat(f.id as any)}
                  className={`py-1.5 rounded-lg border text-xs font-semibold transition-colors ${
                    format === f.id
                      ? "bg-[#a855f7]/20 text-[#a855f7] border-[#a855f7]/60"
                      : "bg-white/5 text-gray-400 border-[#1f242d] hover:text-white"
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          <button
            onClick={handleGenerate}
            className="mt-2 flex items-center justify-center gap-2 py-2.5 rounded-xl bg-gradient-to-r from-[#a855f7] to-[#00d4ff] text-black font-bold text-xs tracking-wider transition-opacity hover:opacity-90 shadow-lg shadow-[#a855f7]/20"
          >
            <Sparkles className="w-4 h-4" />
            <span>GENERATE WITH JARVIS</span>
          </button>
        </div>
      </div>
    </div>
  );
};
