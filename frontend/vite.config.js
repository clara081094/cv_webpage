import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev: Flask runs on the host at :5001 (see backend/README.md). Proxying keeps
// the frontend same-origin, so no CORS setup is needed.
const API_TARGET = "http://localhost:5001";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": API_TARGET,
      "/static/uploads": {
        target: API_TARGET,
        rewrite: (path) => path.replace(/^\/static\/uploads/, "/api/v1/files"),
      },
    },
  },
});
