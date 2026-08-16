import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Vite dev server proxies /api and /ws to the FastAPI backend so the frontend
// only ever talks to its own origin (no CORS friction in dev).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/ws": {
        target: "ws://localhost:8000",
        ws: true,
      },
    },
  },
});
