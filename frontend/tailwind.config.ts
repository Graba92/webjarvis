import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#080a0f",
        surface: "rgba(13, 17, 23, 0.75)",
        borderDark: "#1f242d",
        primaryTeal: "#00d4ff",
        neonMint: "#22c55e",
        cyberPurple: "#a855f7",
        warnOrange: "#ff6b00",
      },
      fontFamily: {
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
