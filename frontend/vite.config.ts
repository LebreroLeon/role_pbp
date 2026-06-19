import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

// Vercel has no /api proxy; without VITE_API_URL the SPA rewrite answers POST with 405.
if (process.env.VERCEL === "1" && !process.env.VITE_API_URL?.trim()) {
  throw new Error(
    "VITE_API_URL must be set in Vercel Environment Variables (Production) before build. " +
      "Example: https://rolepbp-api.onrender.com — see docs/DEPLOY_FRIENDS.md",
  );
}

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      workbox: {
        cleanupOutdatedCaches: true,
        clientsClaim: true,
        skipWaiting: true,
        navigateFallback: "/index.html",
        navigateFallbackDenylist: [/^\/api\//],
      },
      devOptions: {
        enabled: false,
      },
      manifest: {
        name: "RolePBP",
        short_name: "RolePBP",
        description: "Play-by-Post campaign manager",
        theme_color: "#1a1a2e",
        background_color: "#0f0f1a",
        display: "standalone",
        start_url: "/",
        icons: [
          {
            src: "/icon.svg",
            sizes: "any",
            type: "image/svg+xml",
            purpose: "any maskable",
          },
        ],
      },
    }),
  ],
  server: {
    port: 5173,
    host: true,
    proxy: {
      "/api": {
        target: process.env.VITE_PROXY_TARGET ?? "http://localhost:8000",
        changeOrigin: true,
        ws: true,
      },
    },
  },
});
