import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

const DEFAULT_VERCEL_API_URL = "https://rolepbp-api.onrender.com";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const apiUrl =
    env.VITE_API_URL?.trim() ||
    (process.env.VERCEL === "1" ? DEFAULT_VERCEL_API_URL : "");

  if (process.env.VERCEL === "1" && !apiUrl) {
    throw new Error(
      "VITE_API_URL must be set for Vercel builds. " +
        `Add it in Vercel Environment Variables or commit frontend/.env.production. ` +
        `Example: ${DEFAULT_VERCEL_API_URL} — see docs/DEPLOY_FRIENDS.md`,
    );
  }

  return {
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
  };
});
