import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // paleta terminal financiera: fondo casi negro, acentos ámbar/verde
        terminal: {
          bg: "#0a0c10",
          panel: "#11141b",
          border: "#1f2430",
          text: "#c9d1d9",
          dim: "#6b7280",
          amber: "#f59e0b",
          green: "#22c55e",
          red: "#ef4444",
        },
      },
      fontFamily: {
        mono: [
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Consolas",
          "monospace",
        ],
      },
    },
  },
  plugins: [],
};

export default config;
