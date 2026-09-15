"use client";

import React, { useState } from "react";
import { socketManager } from "@/lib/websocket";
import { Sparkles, Save, Check, X, Shield, Cpu, MessageSquare, Flame } from "lucide-react";

interface PersonalityWizardModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const PersonalityWizardModal: React.FC<PersonalityWizardModalProps> = ({
  isOpen,
  onClose
}) => {
  const [step, setStep] = useState<number>(1);
  const [name, setName] = useState<string>("Cypher");
  const [role, setRole] = useState<string>("Autonomes Cybernetic AI OS & Arch Linux Co-Pilot");
  const [tone, setTone] = useState<string>("Sarkastisch, trocken, präzise und hocheffizient");
  const [domain, setDomain] = useState<string>("CachyOS/Arch Linux Systemarchitektur, Kernel-Tuning & Development");
  const [humor, setHumor] = useState<string>("Trockener britischer Witz, gelegentliche ironische Spitzen gegen ineffiziente Software");
  const [boundaries, setBoundaries] = useState<string>("Striktes Hardware-Confirmation-Gate vor Modifikationen, keine Fake-Ausgaben");
  const [customPrompt, setCustomPrompt] = useState<string>("");
  const [savedSuccess, setSavedSuccess] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleSave = () => {
    socketManager.savePersonality({
      name,
      role,
      tone,
      domain,
      humor,
      boundaries,
      custom_prompt: customPrompt
    });
    setSavedSuccess(true);
    setTimeout(() => {
      setSavedSuccess(false);
      onClose();
    }, 1500);
  };

  const presetTones = [
    { label: "Sarkastisch / Butler (Cypher)", value: "Sarkastisch, trocken, präzise und hocheffizient" },
    { label: "High-Tech Operator (Kalt & Taktisch)", value: "Kalt, hyper-fokussiert, militärisch-taktisch und kompromisslos" },
    { label: "Freundlich & Kollegial", value: "Hilfsbereit, enthusiastisch, aufgeschlossen und konstruktiv" },
    { label: "Minimalistisch & Sachlich", value: "Ausschließlich Fakten, keine Floskeln, extrem komprimierte Antworten" }
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4">
      <div className="relative w-full max-w-xl rounded-2xl glass-panel border border-[#00d4ff]/40 bg-[#0d1117] shadow-2xl p-6 overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#1f242d] pb-4 mb-4">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-[#00d4ff]/10 text-[#00d4ff]">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white uppercase tracking-wider">
                Personality Wizard · SOUL.md Configurator
              </h2>
              <p className="text-xs text-gray-400">
                Passe Charakter, Tonfall und Verhaltensregeln deiner KI live an.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-gray-400 hover:text-white rounded-lg hover:bg-white/5 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Wizard Steps Navigation */}
        <div className="flex items-center justify-between mb-6 px-2">
          {[1, 2, 3].map((s) => (
            <button
              key={s}
              onClick={() => setStep(s)}
              className={`flex-1 py-1 text-xs font-bold border-b-2 transition-all ${
                step === s
                  ? "border-[#00d4ff] text-[#00d4ff]"
                  : "border-[#1f242d] text-gray-500 hover:text-gray-300"
              }`}
            >
              Schritt {s}: {s === 1 ? "Identität" : s === 2 ? "Stil & Humor" : "Grenzen & Prompt"}
            </button>
          ))}
        </div>

        {/* Step 1: Identität & Rolle */}
        {step === 1 && (
          <div className="flex flex-col gap-4">
            <div>
              <label className="text-xs font-bold text-gray-300 flex items-center gap-1.5 mb-1">
                <Cpu className="w-3.5 h-3.5 text-[#00d4ff]" /> Name des AI OS
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="z.B. Cypher, Jarvis, Freya..."
                className="w-full px-3 py-2 rounded-lg bg-[#080a0f] border border-[#1f242d] text-xs text-white focus:border-[#00d4ff] outline-none"
              />
            </div>

            <div>
              <label className="text-xs font-bold text-gray-300 flex items-center gap-1.5 mb-1">
                <Shield className="w-3.5 h-3.5 text-[#00d4ff]" /> Rolle & Funktion
              </label>
              <input
                type="text"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                placeholder="z.B. Autonomes Cybernetic AI OS & Arch Linux Co-Pilot"
                className="w-full px-3 py-2 rounded-lg bg-[#080a0f] border border-[#1f242d] text-xs text-white focus:border-[#00d4ff] outline-none"
              />
            </div>

            <div>
              <label className="text-xs font-bold text-gray-300 mb-1 block">
                Spezialisierung / Fachgebiet
              </label>
              <input
                type="text"
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
                placeholder="z.B. CachyOS / Arch Linux, Kernel, DevOps..."
                className="w-full px-3 py-2 rounded-lg bg-[#080a0f] border border-[#1f242d] text-xs text-white focus:border-[#00d4ff] outline-none"
              />
            </div>
          </div>
        )}

        {/* Step 2: Tonfall & Humor */}
        {step === 2 && (
          <div className="flex flex-col gap-4">
            <div>
              <label className="text-xs font-bold text-gray-300 flex items-center gap-1.5 mb-1">
                <MessageSquare className="w-3.5 h-3.5 text-[#a855f7]" /> Tonfall & Sprechstil
              </label>
              <input
                type="text"
                value={tone}
                onChange={(e) => setTone(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-[#080a0f] border border-[#1f242d] text-xs text-white focus:border-[#a855f7] outline-none mb-2"
              />
              <div className="grid grid-cols-2 gap-1.5">
                {presetTones.map((p, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => setTone(p.value)}
                    className={`text-left p-2 rounded border text-[11px] transition-colors ${
                      tone === p.value
                        ? "bg-[#a855f7]/20 border-[#a855f7]/60 text-white"
                        : "bg-[#080a0f]/60 border-[#1f242d] text-gray-400 hover:text-gray-200"
                    }`}
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="text-xs font-bold text-gray-300 flex items-center gap-1.5 mb-1">
                <Flame className="w-3.5 h-3.5 text-[#eab308]" /> Humor & Ironie
              </label>
              <input
                type="text"
                value={humor}
                onChange={(e) => setHumor(e.target.value)}
                placeholder="z.B. Trockener Witz, sarkastisch bei unnötigen Fragen..."
                className="w-full px-3 py-2 rounded-lg bg-[#080a0f] border border-[#1f242d] text-xs text-white focus:border-[#eab308] outline-none"
              />
            </div>
          </div>
        )}

        {/* Step 3: Grenzen & Custom Directives */}
        {step === 3 && (
          <div className="flex flex-col gap-4">
            <div>
              <label className="text-xs font-bold text-gray-300 flex items-center gap-1.5 mb-1">
                <Shield className="w-3.5 h-3.5 text-red-400" /> Ethische Grenzen & Sicherheitsrichtlinien
              </label>
              <textarea
                rows={2}
                value={boundaries}
                onChange={(e) => setBoundaries(e.target.value)}
                placeholder="z.B. Striktes Hardware-Confirmation-Gate, keine ungeprüften Systemlöschungen..."
                className="w-full px-3 py-2 rounded-lg bg-[#080a0f] border border-[#1f242d] text-xs text-white focus:border-red-400 outline-none resize-none"
              />
            </div>

            <div>
              <label className="text-xs font-bold text-gray-300 mb-1 block">
                Zusätzliche Direktiven (Custom Instructions)
              </label>
              <textarea
                rows={3}
                value={customPrompt}
                onChange={(e) => setCustomPrompt(e.target.value)}
                placeholder="Optionale spezifische Vorgaben für die System-Prompts..."
                className="w-full px-3 py-2 rounded-lg bg-[#080a0f] border border-[#1f242d] text-xs text-white focus:border-[#00d4ff] outline-none resize-none"
              />
            </div>
          </div>
        )}

        {/* Footer Buttons */}
        <div className="flex items-center justify-between border-t border-[#1f242d] pt-4 mt-6">
          <div>
            {step > 1 && (
              <button
                type="button"
                onClick={() => setStep(step - 1)}
                className="px-3 py-1.5 rounded-lg border border-[#1f242d] text-xs text-gray-400 hover:text-white"
              >
                Zurück
              </button>
            )}
          </div>

          <div className="flex items-center gap-2">
            {step < 3 ? (
              <button
                type="button"
                onClick={() => setStep(step + 1)}
                className="px-4 py-1.5 rounded-lg bg-[#00d4ff]/20 text-[#00d4ff] border border-[#00d4ff]/40 text-xs font-bold hover:bg-[#00d4ff]/30 transition-all"
              >
                Weiter
              </button>
            ) : (
              <button
                type="button"
                onClick={handleSave}
                disabled={savedSuccess}
                className={`px-4 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-all ${
                  savedSuccess
                    ? "bg-[#22c55e] text-black"
                    : "bg-[#00d4ff] text-black hover:bg-[#00d4ff]/90 shadow-lg shadow-[#00d4ff]/20"
                }`}
              >
                {savedSuccess ? (
                  <>
                    <Check className="w-3.5 h-3.5" /> Gespeichert!
                  </>
                ) : (
                  <>
                    <Save className="w-3.5 h-3.5" /> SOUL.md speichern & aktivieren
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
