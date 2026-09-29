export type PetAnimationState =
  | "idle"
  | "running-left"
  | "running-right"
  | "waving"
  | "jumping"
  | "failed"
  | "waiting"
  | "running"
  | "review"
  | "gaze";

export interface PetAnimationDefinition {
  row: number;
  frames: number;
  durationMs: number;
  loop: boolean;
}

export interface PetConfig {
  enabled: boolean;
  scale: number; // 0.4 bis 1.2, default 0.65
  roamingEnabled: boolean;
  gazeEnabled: boolean;
  speechEnabled: boolean;
  soundEnabled: boolean;
  name: string;
}

export interface GazeTarget {
  x: number;
  y: number;
}
