import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-instrument-sans)", "Instrument Sans", "-apple-system", "BlinkMacSystemFont", "sans-serif"],
        mono: ["var(--font-jetbrains-mono)", "JetBrains Mono", "monospace"],
      },
      colors: {
        brand: {
          cyan: "#0891B2",
          darkCyan: "#0E7490",
          navy: "#0F172A",
          slate: "#334155",
          muted: "#64748B",
          subtle: "#94A3B8",
          border: "#E2E4E8",
          subtleBorder: "#EEF1F4",
          surface: "#FFFFFF",
          bg: "#F4F5F7",
          lightTrack: "#F1F4F7",
        },
      },
      keyframes: {
        zbreathe: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.35" },
        },
        zsweep: {
          from: { transform: "rotate(0deg)" },
          to: { transform: "rotate(360deg)" },
        },
      },
      animation: {
        zbreathe: "zbreathe 2s ease-in-out infinite",
        zsweep: "zsweep 4s linear infinite",
      },
    },
  },
  plugins: [],
};

export default config;
