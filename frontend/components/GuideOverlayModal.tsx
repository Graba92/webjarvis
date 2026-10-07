"use client";

import React, { useState, useEffect } from "react";
import { GuideOverlayData, GuideStep } from "@/lib/types";
import { socketManager } from "@/lib/websocket";
import { 
  X, ChevronLeft, ChevronRight, Download, BookOpen, 
  HelpCircle, Sparkles, CheckCircle2 
} from "lucide-react";

interface GuideOverlayModalProps {
  guide: GuideOverlayData | null;
  onClose: () => void;
}

export const GuideOverlayModal: React.FC<GuideOverlayModalProps> = ({ guide, onClose }) => {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  useEffect(() => {
    setCurrentStepIndex(0);
  }, [guide?.id]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!guide) return;
      if (e.key === "Escape") {
        onClose();
      } else if (e.key === "ArrowRight") {
        handleNext();
      } else if (e.key === "ArrowLeft") {
        handlePrev();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [guide, currentStepIndex]);

  if (!guide || !guide.steps || guide.steps.length === 0) {
    return null;
  }

  const step: GuideStep = guide.steps[currentStepIndex] || guide.steps[0];
  const totalSteps = guide.steps.length;

  const handleNext = () => {
    if (currentStepIndex < totalSteps - 1) {
      setCurrentStepIndex((prev) => prev + 1);
    }
  };

  const handlePrev = () => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex((prev) => prev - 1);
    }
  };

  const handleDownloadImage = () => {
    if (!step.image_base64) return;
    const link = document.createElement("a");
    link.href = `data:image/jpeg;base64,${step.image_base64}`;
    link.download = `webjarvis_anleitung_schritt_${step.step_number}.jpg`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-md p-4 transition-all animate-in fade-in">
      <div className="relative flex flex-col w-full max-w-4xl max-h-[92vh] bg-[#0c1017] border border-cyan-500/40 rounded-xl shadow-[0_0_50px_rgba(0,255,204,0.15)] overflow-hidden">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-cyan-500/20 bg-[#101722]/80">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
              <BookOpen className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-semibold tracking-wide text-white flex items-center gap-2">
                {guide.title}
                <span className="text-xs px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                  Schritt {step.step_number} von {totalSteps}
                </span>
              </h2>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {step.image_base64 && (
              <button
                onClick={handleDownloadImage}
                title="Aktuelles Anleitungsbild speichern"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-cyan-500/30 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 text-xs font-medium transition-all"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Bild speichern</span>
              </button>
            )}

            <button
              onClick={onClose}
              className="p-1.5 text-gray-400 hover:text-white rounded-lg hover:bg-white/5 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 flex flex-col items-center">
          {/* Screenshot / Annotations-Bild */}
          {step.image_base64 ? (
            <div className="relative w-full max-h-[55vh] flex items-center justify-center rounded-lg overflow-hidden border border-cyan-500/30 bg-black/50 shadow-inner group">
              <img
                src={`data:image/jpeg;base64,${step.image_base64}`}
                alt={step.title}
                className="max-h-[55vh] w-auto object-contain rounded"
              />
              <div className="absolute top-3 left-3 px-2.5 py-1 rounded bg-black/75 border border-cyan-500/40 text-cyan-300 text-[11px] font-mono tracking-wider">
                CALLOUT OVERLAY
              </div>
            </div>
          ) : (
            <div className="w-full h-48 flex flex-col items-center justify-center rounded-lg border border-dashed border-cyan-500/30 bg-cyan-950/20 text-cyan-400 gap-2">
              <Sparkles className="w-8 h-8 text-cyan-400 animate-pulse" />
              <p className="text-sm font-medium">Textbasierter Anleitungs-Schritt</p>
            </div>
          )}

          {/* Schritt-Details */}
          <div className="w-full mt-5 p-4 rounded-lg bg-[#141c2b] border border-cyan-500/20">
            <h3 className="text-base font-semibold text-cyan-300 mb-1 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-cyan-400" />
              {step.title}
            </h3>
            <p className="text-sm text-gray-300 leading-relaxed">
              {step.description}
            </p>
          </div>

          {/* Pagination Indicators */}
          <div className="flex items-center gap-1.5 mt-4">
            {guide.steps.map((_, i) => (
              <button
                key={i}
                onClick={() => setCurrentStepIndex(i)}
                className={`h-2 rounded-full transition-all ${
                  i === currentStepIndex
                    ? "w-8 bg-cyan-400 shadow-[0_0_8px_#00ffcc]"
                    : "w-2 bg-gray-600 hover:bg-gray-400"
                }`}
                title={`Zu Schritt ${i + 1} springen`}
              />
            ))}
          </div>
        </div>

        {/* Footer Navigation */}
        <div className="flex items-center justify-between px-6 py-3.5 border-t border-cyan-500/20 bg-[#101722]/90">
          <button
            onClick={handlePrev}
            disabled={currentStepIndex === 0}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all ${
              currentStepIndex === 0
                ? "text-gray-600 border border-transparent cursor-not-allowed"
                : "text-cyan-300 border border-cyan-500/30 bg-cyan-500/10 hover:bg-cyan-500/20 shadow-sm"
            }`}
          >
            <ChevronLeft className="w-4 h-4" />
            Zurück
          </button>

          <span className="text-xs text-gray-400 font-mono">
            Tipp: Pfeiltasten ◀ / ▶ zum Durchblättern · Esc zum Schließen
          </span>

          {currentStepIndex < totalSteps - 1 ? (
            <button
              onClick={handleNext}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold uppercase tracking-wider text-black bg-cyan-400 hover:bg-cyan-300 shadow-[0_0_15px_rgba(0,255,204,0.3)] transition-all"
            >
              Weiter
              <ChevronRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={onClose}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold uppercase tracking-wider text-black bg-emerald-400 hover:bg-emerald-300 shadow-[0_0_15px_rgba(16,185,129,0.3)] transition-all"
            >
              Verstanden & Schließen
              <CheckCircle2 className="w-4 h-4" />
            </button>
          )}
        </div>

      </div>
    </div>
  );
};
