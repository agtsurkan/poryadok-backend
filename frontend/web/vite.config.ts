import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// API base is read at runtime (login screen / localStorage), so no dev proxy is
// required. Set VITE_API_BASE to change the build-time default.
export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
});
