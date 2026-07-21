import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// During `npm run dev` the Vite server proxies /api to the FastAPI backend
// (start it with `maintainer-agent serve`). `npm run build` emits to web/dist.
export default defineConfig({
  plugins: [react()],
  // Production assets use /static/ prefix to match the FastAPI StaticFiles mount.
  base: "/static/",
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8000",
      "/static": "http://127.0.0.1:8000",
    },
  },
  build: { outDir: "dist" },
});
