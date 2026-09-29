import { PetAnimationState, PetAnimationDefinition, GazeTarget } from "./petTypes";
import { AssistantState } from "./types";

export const FRAME_WIDTH = 192;
export const FRAME_HEIGHT = 208;
export const SPRITE_COLUMNS = 8;
export const SPRITE_ROWS = 11;

export const PET_ANIMATIONS: Record<PetAnimationState, PetAnimationDefinition> = {
  idle: { row: 0, frames: 6, durationMs: 4000, loop: true },
  "running-right": { row: 1, frames: 8, durationMs: 950, loop: true },
  "running-left": { row: 2, frames: 8, durationMs: 950, loop: true },
  waving: { row: 3, frames: 4, durationMs: 700, loop: false },
  jumping: { row: 4, frames: 5, durationMs: 840, loop: false },
  failed: { row: 5, frames: 8, durationMs: 1220, loop: false },
  waiting: { row: 6, frames: 6, durationMs: 1010, loop: true },
  running: { row: 7, frames: 6, durationMs: 800, loop: true },
  review: { row: 8, frames: 6, durationMs: 1030, loop: true },
  gaze: { row: 9, frames: 1, durationMs: 1000, loop: true },
};

/**
 * Wandelt AssistantState von Jarvis in eine passende Pet-Reaktion um
 */
export function mapJarvisStateToPetAnimation(state: AssistantState): PetAnimationState {
  switch (state) {
    case "THINKING":
      return "review";
    case "SPEAKING":
      return "waving";
    case "LISTENING":
      return "waiting";
    case "ERROR":
      return "failed";
    case "CONFIRM":
      return "waiting";
    case "IDLE":
    case "OFFLINE":
    default:
      return "idle";
  }
}

/**
 * Berechnet Zeile und Spalte für Cursor-Gaze (16 Sektoren, Rows 9 & 10)
 */
export function calculateGazeCell(
  cursor: GazeTarget,
  petAnchor: { x: number; y: number }
): { row: number; col: number } | null {
  const dx = cursor.x - petAnchor.x;
  const dy = cursor.y - petAnchor.y;
  const dist = Math.hypot(dx, dy);

  // Deadzone um das Pet herum (wenn Maus zu nah ist, kein Gaze)
  if (dist < 40) return null;

  // 0 rad ist Norden/oben, mathematischer Winkel im Uhrzeigersinn
  const angle = Math.atan2(dx, -dy);
  const sectorCount = 16;
  const sectorAngle = (Math.PI * 2) / sectorCount;
  const sector = Math.floor((angle + sectorAngle / 2) / sectorAngle);
  const normalizedSector = (sector + sectorCount) % sectorCount;

  if (normalizedSector < 8) {
    return { row: 9, col: normalizedSector };
  } else {
    return { row: 10, col: normalizedSector - 8 };
  }
}

/**
 * Sanfter WebAudio Sound-Synthesizer für Pet-Effekte (ohne externe MP3s)
 */
export class PetSoundFX {
  private static ctx: AudioContext | null = null;

  private static getContext(): AudioContext | null {
    if (typeof window === "undefined") return null;
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      if (AudioCtx) this.ctx = new AudioCtx();
    }
    if (this.ctx && this.ctx.state === "suspended") {
      this.ctx.resume().catch(() => {});
    }
    return this.ctx;
  }

  public static playHappyChirp() {
    const ctx = this.getContext();
    if (!ctx) return;
    try {
      const now = ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = "sine";
      osc.frequency.setValueAtTime(580, now);
      osc.frequency.exponentialRampToValueAtTime(880, now + 0.08);
      osc.frequency.exponentialRampToValueAtTime(1174, now + 0.18);

      gain.gain.setValueAtTime(0.01, now);
      gain.gain.linearRampToValueAtTime(0.12, now + 0.04);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start(now);
      osc.stop(now + 0.26);
    } catch (_) {}
  }

  public static playPurr() {
    const ctx = this.getContext();
    if (!ctx) return;
    try {
      const now = ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = "triangle";
      osc.frequency.setValueAtTime(140, now);
      osc.frequency.linearRampToValueAtTime(180, now + 0.1);
      osc.frequency.linearRampToValueAtTime(120, now + 0.2);

      gain.gain.setValueAtTime(0.01, now);
      gain.gain.linearRampToValueAtTime(0.08, now + 0.05);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.3);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start(now);
      osc.stop(now + 0.3);
    } catch (_) {}
  }

  public static playCurious() {
    const ctx = this.getContext();
    if (!ctx) return;
    try {
      const now = ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = "sine";
      osc.frequency.setValueAtTime(440, now);
      osc.frequency.exponentialRampToValueAtTime(660, now + 0.12);

      gain.gain.setValueAtTime(0.01, now);
      gain.gain.linearRampToValueAtTime(0.1, now + 0.03);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.18);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start(now);
      osc.stop(now + 0.19);
    } catch (_) {}
  }
}
