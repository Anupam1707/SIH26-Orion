import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// The API runs on :8000. The dev server proxies /api/* to it so the browser
// only ever talks to one origin (no CORS, nothing leaves the machine).
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
  test: { environment: "node", include: ["src/**/*.test.ts"] },
});
