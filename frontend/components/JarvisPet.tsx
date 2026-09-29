"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import { 
  FRAME_WIDTH, 
  FRAME_HEIGHT, 
  PET_ANIMATIONS, 
  mapJarvisStateToPetAnimation, 
  calculateGazeCell, 
  PetSoundFX 
} from "@/lib/petEngine";
import { PetAnimationState, PetConfig } from "@/lib/petTypes";
import { socketManager } from "@/lib/websocket";
import { AssistantState, ChatMessage } from "@/lib/types";
import { 
  X, Settings2, Volume2, VolumeX, Eye, EyeOff, 
  Footprints, MessageSquare, Sparkles, Heart 
} from "lucide-react";

interface JarvisPetProps {
  isOpen: boolean;
  onClose: () => void;
}

const DEFAULT_CONFIG: PetConfig = {
  enabled: true,
  scale: 0.65,
  roamingEnabled: true,
  gazeEnabled: true,
  speechEnabled: true,
  soundEnabled: true,
  name: "Yuyu",
};

const RANDOM_DIALOGUES = [
  "Ich passe auf dein System auf! ✨",
  "CachyOS läuft geschmeidig wie Butter!",
  "Alles nominal, Operator!",
  "Brauchst du Hilfe bei einem Task? 💖",
  "PipeWire Audio & Neural-Cores aktiv!",
  "Yuyu ist stets einsatzbereit!",
  "Streichel mich gerne noch einmal!",
  "J.A.R.V.I.S. und ich sind ein unschlagbares Team.",
];

export const JarvisPet: React.FC<JarvisPetProps> = ({ isOpen, onClose }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const spritesheetRef = useRef<HTMLImageElement | null>(null);
  
  // Konfiguration & Settings
  const [config, setConfig] = useState<PetConfig>(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("jarvis_pet_config");
      if (saved) {
        try { return { ...DEFAULT_CONFIG, ...JSON.parse(saved) }; } catch (_) {}
      }
    }
    return DEFAULT_CONFIG;
  });

  const [showSettings, setShowSettings] = useState(false);
  const [speechText, setSpeechText] = useState<string | null>("Hallo! Ich bin Yuyu! 🐾");
  const speechTimeoutRef = useRef<any>(null);

  // Position & Physik
  const [position, setPosition] = useState<{ x: number; y: number }>({ x: 200, y: 500 });
  const [isDragging, setIsDragging] = useState(false);
  const dragOffset = useRef<{ x: number; y: number }>({ x: 0, y: 0 });

  // Animations-Zustand
  const animStateRef = useRef<PetAnimationState>("idle");
  const [currentAnimState, setCurrentAnimState] = useState<PetAnimationState>("idle");
  const animStartTimeRef = useRef<number>(Date.now());
  const oneShotActiveRef = useRef<boolean>(false);

  // Gaze Tracking
  const lastMouseMoveRef = useRef<number>(0);
  const mousePosRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const gazeCellRef = useRef<{ row: number; col: number } | null>(null);

  // Autonomes Roaming
  const roamingDirectionRef = useRef<"left" | "right" | "idle">("idle");
  const roamingEndRef = useRef<number>(0);
  const nextRoamDecisionRef = useRef<number>(Date.now() + 4000);

  // Speichere Konfiguration
  useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.setItem("jarvis_pet_config", JSON.stringify(config));
    }
  }, [config]);

  // Initialisiere Startposition (unten rechts über BottomDock)
  useEffect(() => {
    if (typeof window !== "undefined") {
      const startX = Math.max(50, window.innerWidth - 300);
      const startY = Math.max(50, window.innerHeight - 280);
      setPosition({ x: startX, y: startY });
    }
  }, []);

  // Zeige Sprechblase mit Timeout
  const triggerSpeech = useCallback((text: string, durationMs = 4500) => {
    if (!config.speechEnabled) return;
    setSpeechText(text);
    if (speechTimeoutRef.current) clearTimeout(speechTimeoutRef.current);
    speechTimeoutRef.current = setTimeout(() => {
      setSpeechText(null);
    }, durationMs);
  }, [config.speechEnabled]);

  // Setze gezielte One-Shot Animation (z.B. Winken, Springen)
  const playOneShotAnimation = useCallback((anim: PetAnimationState, speech?: string) => {
    animStateRef.current = anim;
    setCurrentAnimState(anim);
    animStartTimeRef.current = Date.now();
    oneShotActiveRef.current = true;

    if (speech) triggerSpeech(speech);

    const def = PET_ANIMATIONS[anim];
    const duration = def ? def.durationMs : 1000;

    setTimeout(() => {
      oneShotActiveRef.current = false;
      animStateRef.current = "idle";
      setCurrentAnimState("idle");
      animStartTimeRef.current = Date.now();
    }, duration);
  }, [triggerSpeech]);

  // Klick auf das Pet (Interaktion / Streicheln)
  const handlePetClick = (e: React.MouseEvent) => {
    if (isDragging) return;
    if (config.soundEnabled) PetSoundFX.playHappyChirp();
    const randomMsg = RANDOM_DIALOGUES[Math.floor(Math.random() * RANDOM_DIALOGUES.length)];
    playOneShotAnimation("jumping", randomMsg);
  };

  // Spritesheet laden
  useEffect(() => {
    const img = new Image();
    img.src = "/assets/pets/yuyu-chibi/spritesheet.webp";
    img.onload = () => {
      spritesheetRef.current = img;
    };
  }, []);

  // WebSocket Anbindung an WebJarvis
  useEffect(() => {
    if (!isOpen) return;

    const unsubState = socketManager.onState((state: AssistantState) => {
      if (oneShotActiveRef.current) return;
      const targetAnim = mapJarvisStateToPetAnimation(state);
      animStateRef.current = targetAnim;
      setCurrentAnimState(targetAnim);
      animStartTimeRef.current = Date.now();

      if (state === "THINKING") {
        triggerSpeech("J.A.R.V.I.S. überlegt angestrengt... 🧠", 3500);
      } else if (state === "SPEAKING") {
        triggerSpeech("J.A.R.V.I.S. antwortet! 🎙️", 3000);
      } else if (state === "ERROR") {
        if (config.soundEnabled) PetSoundFX.playCurious();
        triggerSpeech("Uff, ein Systemfehler wurde gemeldet! ⚠️", 4000);
      }
    });

    const unsubChat = socketManager.onChat((chat: ChatMessage) => {
      if (chat.speaker === "JARVIS" && chat.text) {
        const snippet = chat.text.length > 70 ? chat.text.substring(0, 67) + "..." : chat.text;
        triggerSpeech(`💬 ${snippet}`, 5000);
      }
    });

    return () => {
      unsubState();
      unsubChat();
    };
  }, [isOpen, triggerSpeech, config.soundEnabled]);

  // Mauszeiger-Verfolgung (Gaze Tracking)
  useEffect(() => {
    if (!isOpen || !config.gazeEnabled) return;

    const handleMouseMove = (e: MouseEvent) => {
      mousePosRef.current = { x: e.clientX, y: e.clientY };
      lastMouseMoveRef.current = Date.now();
    };

    window.addEventListener("mousemove", handleMouseMove, { passive: true });
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, [isOpen, config.gazeEnabled]);

  // Drag & Drop Handler
  const handleMouseDown = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest(".pet-ui-control")) return;
    setIsDragging(true);
    dragOffset.current = {
      x: e.clientX - position.x,
      y: e.clientY - position.y,
    };
  };

  useEffect(() => {
    const handleMouseMoveGlobal = (e: MouseEvent) => {
      if (!isDragging) return;
      const newX = Math.max(10, Math.min(window.innerWidth - FRAME_WIDTH * config.scale - 10, e.clientX - dragOffset.current.x));
      const newY = Math.max(10, Math.min(window.innerHeight - FRAME_HEIGHT * config.scale - 10, e.clientY - dragOffset.current.y));
      setPosition({ x: newX, y: newY });
    };

    const handleMouseUpGlobal = () => {
      if (isDragging) {
        setIsDragging(false);
      }
    };

    if (isDragging) {
      window.addEventListener("mousemove", handleMouseMoveGlobal);
      window.addEventListener("mouseup", handleMouseUpGlobal);
    }

    return () => {
      window.removeEventListener("mousemove", handleMouseMoveGlobal);
      window.removeEventListener("mouseup", handleMouseUpGlobal);
    };
  }, [isDragging, config.scale]);

  // Animations- & Roaming-Loop (60 FPS Canvas)
  useEffect(() => {
    if (!isOpen) return;
    let animFrameId: number;

    const tick = () => {
      const now = Date.now();
      const canvas = canvasRef.current;
      const ctx = canvas?.getContext("2d");
      const img = spritesheetRef.current;

      // 1. Autonomes Roaming & Physik (wenn aktiv und nicht im Drag/One-Shot)
      if (config.roamingEnabled && !isDragging && !oneShotActiveRef.current && animStateRef.current === "idle") {
        if (now > nextRoamDecisionRef.current) {
          // Treffe eine Entscheidung: Stehen bleiben oder wandern
          const choice = Math.random();
          if (choice < 0.45) {
            roamingDirectionRef.current = "left";
            roamingEndRef.current = now + 1500 + Math.random() * 2000;
          } else if (choice < 0.9) {
            roamingDirectionRef.current = "right";
            roamingEndRef.current = now + 1500 + Math.random() * 2000;
          } else {
            roamingDirectionRef.current = "idle";
            roamingEndRef.current = now + 2000 + Math.random() * 3000;
          }
          nextRoamDecisionRef.current = roamingEndRef.current + 3000 + Math.random() * 5000;
        }

        // Bewegen, falls Richtung aktiv
        if (now < roamingEndRef.current && roamingDirectionRef.current !== "idle") {
          const speed = 1.4;
          setPosition((prev) => {
            let nextX = prev.x;
            const minX = 20;
            const maxX = window.innerWidth - FRAME_WIDTH * config.scale - 20;

            if (roamingDirectionRef.current === "left") {
              nextX -= speed;
              if (nextX <= minX) {
                roamingDirectionRef.current = "right";
              }
            } else if (roamingDirectionRef.current === "right") {
              nextX += speed;
              if (nextX >= maxX) {
                roamingDirectionRef.current = "left";
              }
            }
            return { ...prev, x: nextX };
          });
        }
      }

      // 2. Bestimme Sprite-Zeile und Frame
      let animState = animStateRef.current;

      // Wenn gerodelt wird, zeige running-left oder running-right
      if (config.roamingEnabled && !isDragging && !oneShotActiveRef.current && now < roamingEndRef.current && roamingDirectionRef.current !== "idle") {
        animState = roamingDirectionRef.current === "left" ? "running-left" : "running-right";
      }

      // Prüfe Cursor Gaze (nur wenn im Idle-Zustand und Cursor aktiv)
      let activeGazeCell: { row: number; col: number } | null = null;
      if (
        config.gazeEnabled &&
        animState === "idle" &&
        !isDragging &&
        now - lastMouseMoveRef.current < 2000
      ) {
        const petCenter = {
          x: position.x + (FRAME_WIDTH * config.scale) / 2,
          y: position.y + (FRAME_HEIGHT * config.scale) / 2,
        };
        activeGazeCell = calculateGazeCell(mousePosRef.current, petCenter);
        gazeCellRef.current = activeGazeCell;
      } else {
        gazeCellRef.current = null;
      }

      // 3. Canvas Rendern
      if (canvas && ctx && img) {
        ctx.clearRect(0, 0, FRAME_WIDTH, FRAME_HEIGHT);

        let sourceRow = 0;
        let sourceCol = 0;

        if (activeGazeCell) {
          // Gaze Frame aus Row 9 oder 10
          sourceRow = activeGazeCell.row;
          sourceCol = activeGazeCell.col;
        } else {
          // Reguläre Animation
          const animDef = PET_ANIMATIONS[animState] || PET_ANIMATIONS.idle;
          const elapsed = now - animStartTimeRef.current;
          const frameIndex = animDef.loop 
            ? Math.floor((elapsed % animDef.durationMs) / (animDef.durationMs / animDef.frames))
            : Math.min(animDef.frames - 1, Math.floor(elapsed / (animDef.durationMs / animDef.frames)));

          sourceRow = animDef.row;
          sourceCol = Math.min(animDef.frames - 1, frameIndex);
        }

        const sx = sourceCol * FRAME_WIDTH;
        const sy = sourceRow * FRAME_HEIGHT;

        ctx.imageSmoothingEnabled = false; // Pixel-Perfect & Crisp Rendering
        ctx.drawImage(
          img,
          sx, sy, FRAME_WIDTH, FRAME_HEIGHT,
          0, 0, FRAME_WIDTH, FRAME_HEIGHT
        );
      }

      animFrameId = requestAnimationFrame(tick);
    };

    animFrameId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(animFrameId);
  }, [isOpen, config, isDragging, position]);

  if (!isOpen) return null;

  return (
    <div
      style={{
        transform: `translate3d(${position.x}px, ${position.y}px, 0)`,
        width: FRAME_WIDTH * config.scale,
        height: FRAME_HEIGHT * config.scale,
      }}
      className={`fixed top-0 left-0 z-40 select-none touch-none ${
        isDragging ? "cursor-grabbing" : "cursor-grab"
      }`}
      onMouseDown={handleMouseDown}
    >
      {/* Sprechblase über dem Pet */}
      {speechText && config.speechEnabled && (
        <div 
          className="absolute -top-16 left-1/2 -translate-x-1/2 z-50 pointer-events-none min-w-[140px] max-w-[260px] bg-black/85 backdrop-blur-md border border-[#00d4ff]/40 text-cyan-200 text-xs px-3 py-1.5 rounded-xl shadow-[0_0_15px_rgba(0,212,255,0.25)] animate-fade-in flex items-center gap-1.5"
        >
          <Sparkles className="w-3.5 h-3.5 text-[#00d4ff] shrink-0 animate-pulse" />
          <span className="leading-tight font-sans break-words">{speechText}</span>
          <div className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 w-3 h-3 bg-black/85 border-r border-b border-[#00d4ff]/40 rotate-45" />
        </div>
      )}

      {/* Floating Hover Controls (Settings & Close) */}
      <div className="pet-ui-control absolute -top-7 right-0 flex items-center gap-1 opacity-0 hover:opacity-100 transition-opacity bg-black/70 backdrop-blur-md rounded-full px-2 py-0.5 border border-white/10 z-50">
        <button
          type="button"
          onClick={() => {
            if (config.soundEnabled) PetSoundFX.playPurr();
            playOneShotAnimation("waving", "Hallo Meister! Schön dich zu sehen! 💖");
          }}
          className="text-pink-400 hover:text-pink-300 transition-colors p-0.5"
          title="Yuyu streicheln"
        >
          <Heart className="w-3.5 h-3.5" />
        </button>
        <button
          type="button"
          onClick={() => setShowSettings((prev) => !prev)}
          className="text-gray-300 hover:text-[#00d4ff] transition-colors p-0.5"
          title="Pet Einstellungen"
        >
          <Settings2 className="w-3.5 h-3.5" />
        </button>
        <button
          type="button"
          onClick={onClose}
          className="text-gray-400 hover:text-red-400 transition-colors p-0.5"
          title="Pet deaktivieren"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Settings Flyout */}
      {showSettings && (
        <div className="pet-ui-control absolute top-full left-0 mt-2 w-56 bg-black/90 backdrop-blur-xl border border-[#00d4ff]/30 rounded-xl p-3 shadow-2xl z-50 text-xs text-gray-200">
          <div className="flex items-center justify-between pb-2 border-b border-white/10 font-semibold text-[#00d4ff]">
            <span>🐾 Yuyu Chibi Settings</span>
            <button onClick={() => setShowSettings(false)} className="text-gray-400 hover:text-white">
              <X className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-2.5 mt-2.5">
            {/* Größe */}
            <div>
              <div className="flex justify-between text-[10px] text-gray-400 mb-1">
                <span>Skalierung</span>
                <span>{Math.round(config.scale * 100)}%</span>
              </div>
              <input
                type="range"
                min="0.4"
                max="1.2"
                step="0.05"
                value={config.scale}
                onChange={(e) => setConfig({ ...config, scale: parseFloat(e.target.value) })}
                className="w-full accent-[#00d4ff] h-1 bg-white/10 rounded-lg cursor-pointer"
              />
            </div>

            {/* Toggles */}
            <div className="grid grid-cols-2 gap-1.5 pt-1">
              <button
                type="button"
                onClick={() => setConfig({ ...config, roamingEnabled: !config.roamingEnabled })}
                className={`flex items-center gap-1.5 px-2 py-1 rounded-md border text-[11px] transition-colors ${
                  config.roamingEnabled
                    ? "bg-[#00d4ff]/15 border-[#00d4ff]/50 text-cyan-300"
                    : "bg-white/5 border-white/10 text-gray-400"
                }`}
              >
                <Footprints className="w-3 h-3" />
                <span>Wandern</span>
              </button>

              <button
                type="button"
                onClick={() => setConfig({ ...config, gazeEnabled: !config.gazeEnabled })}
                className={`flex items-center gap-1.5 px-2 py-1 rounded-md border text-[11px] transition-colors ${
                  config.gazeEnabled
                    ? "bg-[#00d4ff]/15 border-[#00d4ff]/50 text-cyan-300"
                    : "bg-white/5 border-white/10 text-gray-400"
                }`}
              >
                {config.gazeEnabled ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
                <span>Blick</span>
              </button>

              <button
                type="button"
                onClick={() => setConfig({ ...config, soundEnabled: !config.soundEnabled })}
                className={`flex items-center gap-1.5 px-2 py-1 rounded-md border text-[11px] transition-colors ${
                  config.soundEnabled
                    ? "bg-[#00d4ff]/15 border-[#00d4ff]/50 text-cyan-300"
                    : "bg-white/5 border-white/10 text-gray-400"
                }`}
              >
                {config.soundEnabled ? <Volume2 className="w-3 h-3" /> : <VolumeX className="w-3 h-3" />}
                <span>Sound</span>
              </button>

              <button
                type="button"
                onClick={() => setConfig({ ...config, speechEnabled: !config.speechEnabled })}
                className={`flex items-center gap-1.5 px-2 py-1 rounded-md border text-[11px] transition-colors ${
                  config.speechEnabled
                    ? "bg-[#00d4ff]/15 border-[#00d4ff]/50 text-cyan-300"
                    : "bg-white/5 border-white/10 text-gray-400"
                }`}
              >
                <MessageSquare className="w-3 h-3" />
                <span>Dialoge</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Pet Canvas */}
      <canvas
        ref={canvasRef}
        width={FRAME_WIDTH}
        height={FRAME_HEIGHT}
        onClick={handlePetClick}
        style={{
          width: FRAME_WIDTH * config.scale,
          height: FRAME_HEIGHT * config.scale,
          imageRendering: "pixelated",
        }}
        className="transition-transform active:scale-95 drop-shadow-[0_4px_12px_rgba(0,0,0,0.5)]"
      />
    </div>
  );
};
