"use client";

import React, { useState, useEffect, useRef } from "react";
import { ChatMessage } from "@/lib/types";
import { socketManager } from "@/lib/websocket";
import { 
  MessageSquare, Send, Trash2, ChevronDown, ChevronUp, X, 
  Terminal, Move, Sparkles, User, Bot, Volume2
} from "lucide-react";

interface JarvisChatWindowProps {
  isOpen: boolean;
  onClose: () => void;
  onOpenDevConsole?: () => void;
}

export const JarvisChatWindow: React.FC<JarvisChatWindowProps> = ({ 
  isOpen, 
  onClose,
  onOpenDevConsole 
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      speaker: "JARVIS",
      text: "Cypher online. CachyOS-Subsysteme nominal, PipeWire Audio geroutet. Bereit für Instruktionen, Operator.",
      ts: new Date().toLocaleTimeString()
    }
  ]);
  const [input, setInput] = useState("");
  const [isMinimized, setIsMinimized] = useState<boolean>(false);
  const [aiName, setAiName] = useState<string>("CYPHER");

  // Draggable Position & Resizable Size
  const [pos, setPos] = useState<{ x: number; y: number } | null>(null);
  const [size, setSize] = useState<{ width: number; height: number }>({ width: 540, height: 460 });

  const scrollRef = useRef<HTMLDivElement>(null);
  const draggingRef = useRef<{ startX: number; startY: number; posX: number; posY: number } | null>(null);
  const resizingRef = useRef<{ startX: number; startY: number; startW: number; startH: number } | null>(null);

  // Initial Position (zentriert oder leicht links über der unteren Leiste)
  useEffect(() => {
    if (typeof window !== "undefined" && pos === null) {
      setPos({
        x: Math.max(20, Math.round((window.innerWidth - 540) / 2)),
        y: Math.max(50, window.innerHeight - 560)
      });
    }
  }, [pos]);

  useEffect(() => {
    const unsubChat = socketManager.onChat((newMsg) => {
      setMessages((prev) => [...prev.slice(-150), newMsg]);
    });
    const unsubAiName = socketManager.onAiName((name) => {
      if (name) setAiName(name);
    });
    return () => {
      unsubChat();
      unsubAiName();
    };
  }, []);

  useEffect(() => {
    if (scrollRef.current && !isMinimized) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isMinimized]);

  if (!isOpen) return null;

  // --- Dragging Handler ---
  const handleHeaderMouseDown = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest("button") || (e.target as HTMLElement).closest("input")) return;
    e.preventDefault();
    const currentX = pos ? pos.x : 100;
    const currentY = pos ? pos.y : 100;
    draggingRef.current = {
      startX: e.clientX,
      startY: e.clientY,
      posX: currentX,
      posY: currentY,
    };

    const handleMouseMove = (ev: MouseEvent) => {
      if (!draggingRef.current) return;
      const dx = ev.clientX - draggingRef.current.startX;
      const dy = ev.clientY - draggingRef.current.startY;
      setPos({
        x: Math.max(10, Math.min(window.innerWidth - 120, draggingRef.current.posX + dx)),
        y: Math.max(10, Math.min(window.innerHeight - 60, draggingRef.current.posY + dy)),
      });
    };

    const handleMouseUp = () => {
      draggingRef.current = null;
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };

    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
  };

  // --- Resizing Handler ---
  const handleResizeMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    resizingRef.current = {
      startX: e.clientX,
      startY: e.clientY,
      startW: size.width,
      startH: size.height,
    };

    const handleMouseMove = (ev: MouseEvent) => {
      if (!resizingRef.current) return;
      const dw = ev.clientX - resizingRef.current.startX;
      const dh = ev.clientY - resizingRef.current.startY;
      setSize({
        width: Math.max(360, Math.min(window.innerWidth - 40, resizingRef.current.startW + dw)),
        height: Math.max(220, Math.min(window.innerHeight - 60, resizingRef.current.startH + dh)),
      });
    };

    const handleMouseUp = () => {
      resizingRef.current = null;
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };

    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
  };

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    const clean = input.trim();
    if (!clean) return;
    socketManager.sendText(clean);
    setInput("");
  };

  return (
    <div
      style={{
        position: "fixed",
        left: pos ? `${pos.x}px` : "auto",
        top: pos ? `${pos.y}px` : "auto",
        width: isMinimized ? "320px" : `${size.width}px`,
        height: isMinimized ? "42px" : `${size.height}px`,
        zIndex: 42,
      }}
      className="rounded-2xl glass-panel-glow border border-[#00d4ff]/40 shadow-2xl bg-[#0a0d14]/95 flex flex-col overflow-hidden select-none animate-in fade-in duration-100"
    >
      {/* Draggable Header */}
      <div
        onMouseDown={handleHeaderMouseDown}
        className="flex items-center justify-between px-3.5 py-2.5 border-b border-[#1f242d] bg-[#0d1117] cursor-grab active:cursor-grabbing shrink-0"
      >
        <div className="flex items-center gap-2 pointer-events-none">
          <MessageSquare className="w-4 h-4 text-[#00d4ff]" />
          <span className="text-xs font-black text-white tracking-wider flex items-center gap-1.5 font-mono">
            <span>{aiName.toUpperCase()} LIVE CHAT</span>
            <span className="text-[10px] text-gray-500 font-normal">| Dialog</span>
          </span>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#00d4ff]/15 text-[#00d4ff] font-bold border border-[#00d4ff]/30 font-mono">
            {messages.length}
          </span>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-1.5">
          {onOpenDevConsole && (
            <button
              onClick={onOpenDevConsole}
              title="Dev-Console mit ungefilterten Systemlogs öffnen"
              className="flex items-center gap-1 px-2 py-0.5 rounded bg-white/5 hover:bg-white/10 text-[10px] text-[#00d4ff] hover:text-white transition-colors cursor-pointer font-mono"
            >
              <Terminal className="w-2.5 h-2.5" />
              <span>Dev-Console</span>
            </button>
          )}

          <button
            onClick={() => setMessages([])}
            title="Chat-Verlauf leeren"
            className="p-1 rounded text-gray-400 hover:text-red-400 hover:bg-white/5 transition-colors cursor-pointer"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            title={isMinimized ? "Maximieren" : "Minimieren"}
            className="p-1 rounded text-gray-400 hover:text-white hover:bg-white/5 transition-colors cursor-pointer"
          >
            {isMinimized ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
          <button
            onClick={onClose}
            title="Schließen"
            className="p-1 rounded text-gray-400 hover:text-red-400 hover:bg-red-500/10 transition-colors cursor-pointer"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {!isMinimized && (
        <>
          {/* Chat Messages Body */}
          <div
            ref={scrollRef}
            className="flex-1 overflow-y-auto p-4 flex flex-col gap-3 text-xs select-text bg-[#080a0f]/60"
          >
            {messages.length === 0 ? (
              <div className="text-gray-500 italic p-8 text-center text-xs">
                Noch keine Nachrichten. Sprich mit Jarvis oder tippe unten einen Befehl ein.
              </div>
            ) : (
              messages.map((item, idx) => {
                const isYou = item.speaker === "YOU";
                return (
                  <div
                    key={idx}
                    className={`flex flex-col gap-1 max-w-[85%] ${
                      isYou ? "self-end items-end" : "self-start items-start"
                    }`}
                  >
                    {/* Header: Name & Zeit */}
                    <div className="flex items-center gap-1.5 text-[10px] text-gray-400 font-mono px-1">
                      {isYou ? (
                        <>
                          <span className="text-gray-500">[{item.ts}]</span>
                          <span className="font-bold text-[#22c55e]">Operator (DU)</span>
                          <User className="w-3 h-3 text-[#22c55e]" />
                        </>
                      ) : (
                        <>
                          <Bot className="w-3 h-3 text-[#00d4ff]" />
                          <span className="font-bold text-[#00d4ff]">{aiName}</span>
                          <span className="text-gray-500">[{item.ts}]</span>
                        </>
                      )}
                    </div>

                    {/* Chat Bubble */}
                    <div
                      className={`p-3 rounded-2xl leading-relaxed text-xs shadow-lg ${
                        isYou
                          ? "bg-[#22c55e]/15 border border-[#22c55e]/40 text-gray-100 rounded-tr-sm"
                          : "bg-[#0d131f] border border-[#00d4ff]/30 text-white rounded-tl-sm shadow-[#00d4ff]/5"
                      }`}
                    >
                      <p className="whitespace-pre-wrap select-text leading-relaxed">
                        {item.text}
                      </p>
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Integrated Input Form inside Chat Window */}
          <form
            onSubmit={handleSend}
            className="p-2.5 bg-[#0a0d14] border-t border-[#1f242d] flex items-center gap-2 shrink-0"
          >
            <input
              type="text"
              placeholder={`Schreibe eine Nachricht an ${aiName}...`}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              className="flex-1 bg-[#080a0f] border border-[#1f242d] rounded-xl px-3 py-2 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-[#00d4ff]/60"
            />
            <button
              type="submit"
              disabled={!input.trim()}
              className="p-2 rounded-xl bg-[#00d4ff]/20 hover:bg-[#00d4ff]/30 text-[#00d4ff] border border-[#00d4ff]/40 disabled:opacity-30 transition-all cursor-pointer"
              title="Nachricht senden"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>

          {/* Footer mit Resize Handle */}
          <div className="relative px-3 py-1 bg-[#0d1117] border-t border-[#1f242d]/80 flex items-center justify-between text-[10px] text-gray-500 font-mono shrink-0">
            <span className="flex items-center gap-1.5">
              <Move className="w-3 h-3 text-gray-500" />
              <span>Fenster frei verschiebbar & in der Größe anpassbar</span>
            </span>

            {/* Resize Handle unten rechts */}
            <div
              onMouseDown={handleResizeMouseDown}
              className="w-4 h-4 cursor-se-resize flex items-center justify-center text-gray-400 hover:text-[#00d4ff] transition-colors"
              title="Klicken & Ziehen zum Ändern der Fenstergröße"
            >
              <svg width="10" height="10" viewBox="0 0 10 10" fill="currentColor">
                <circle cx="8" cy="8" r="1.2" />
                <circle cx="8" cy="4" r="1.2" />
                <circle cx="4" cy="8" r="1.2" />
              </svg>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
