"use client";

import React, { useEffect, useState } from "react";
import { ConfirmRequest } from "@/lib/types";
import { socketManager } from "@/lib/websocket";
import { AlertTriangle, Check, X, ShieldAlert, Clock } from "lucide-react";

export const ConfirmBanner: React.FC = () => {
  const [confirm, setConfirm] = useState<ConfirmRequest | null>(null);
  const [secondsLeft, setSecondsLeft] = useState<number>(90);

  useEffect(() => {
    const unsub = socketManager.onConfirm((req) => {
      setConfirm(req);
      if (req) {
        setSecondsLeft(typeof req.timeout === "number" ? req.timeout : 90);
      }
    });
    return () => unsub();
  }, []);

  useEffect(() => {
    if (!confirm) return;

    const timer = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          socketManager.resolveConfirm(false);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [confirm]);

  if (!confirm) return null;

  const displayAction = (confirm.action || confirm.key || "SYSTEM").toUpperCase();
  const displayLabel = confirm.label || confirm.title || "Systembefehl";
  const displayDetail = confirm.detail || "Hardware Confirmation Gate freigeben?";

  return (
    <div
      style={{ zIndex: 9999 }}
      className="fixed top-12 left-1/2 transform -translate-x-1/2 z-[9999] w-[440px] max-w-[95vw] rounded-2xl border-2 border-[#f59e0b] bg-[#0c0e14]/98 backdrop-blur-2xl p-5 shadow-[0_0_50px_rgba(245,158,11,0.45)] ring-1 ring-[#f59e0b]/40 animate-bounce-short"
    >
      <div className="flex items-start gap-3.5">
        <div className="p-2.5 rounded-xl bg-[#f59e0b]/20 border border-[#f59e0b]/40 text-[#f59e0b] shadow-[0_0_15px_rgba(245,158,11,0.3)]">
          <ShieldAlert className="w-6 h-6 animate-pulse text-[#f59e0b]" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-1.5">
              <span className="inline-block w-2 h-2 rounded-full bg-[#f59e0b] animate-ping" />
              <h4 className="text-[11px] font-black tracking-widest uppercase text-[#f59e0b]">
                HARDWARE SAFETY GATE
              </h4>
            </div>
            <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-black/60 border border-[#f59e0b]/30 text-[10px] font-mono text-[#f59e0b]">
              <Clock className="w-3 h-3 animate-spin text-[#f59e0b]" />
              <span>{secondsLeft}s</span>
            </div>
          </div>

          <div className="mt-1.5 flex items-baseline gap-2">
            <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-[#f59e0b]/20 text-[#f59e0b] border border-[#f59e0b]/30">
              {displayAction}
            </span>
            <p className="text-sm font-black text-white tracking-wide truncate">
              {displayLabel}
            </p>
          </div>

          <p className="text-xs text-gray-300 mt-1.5 leading-relaxed">
            {displayDetail}
          </p>

          <div className="flex items-center gap-2.5 mt-4">
            <button
              onClick={() => socketManager.resolveConfirm(true)}
              className="flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-xl bg-gradient-to-r from-[#22c55e] to-[#16a34a] hover:from-[#16a34a] hover:to-[#15803d] text-black font-black text-xs tracking-wider transition-all duration-150 shadow-[0_0_20px_rgba(34,197,94,0.4)] active:scale-95 cursor-pointer"
            >
              <Check className="w-4 h-4 stroke-[3]" />
              <span>CONFIRM</span>
            </button>
            <button
              onClick={() => socketManager.resolveConfirm(false)}
              className="flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-xl bg-red-950/40 hover:bg-red-900/60 border border-red-500/50 text-red-300 font-bold text-xs tracking-wider transition-all duration-150 active:scale-95 cursor-pointer"
            >
              <X className="w-4 h-4" />
              <span>CANCEL</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

