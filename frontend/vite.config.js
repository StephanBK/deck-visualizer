import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev: `npm run dev` serves the app on :5173 and proxies /api to the FastAPI
// backend on :8000 (same-origin from the browser's point of view, so no CORS).
// Prod: `npm run build` emits dist/, which FastAPI serves directly at /.
export default defineConfig({
  plugins: [react()],
  build: { outDir: "dist" },
  server: {
    proxy: { "/api": "http://localhost:8000" },
  },
});
