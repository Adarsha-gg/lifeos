import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "path";

// Single-page LifeOS Quest Hub. Imports the design system straight from source
// so the hub and the library stay in lockstep. `base: "./"` keeps the built
// output portable (drop dist/ anywhere static — Vercel-friendly).
export default defineConfig({
  base: "./",
  plugins: [react()],
  resolve: {
    // Import the design system straight from source. Force react/react-dom to
    // THIS app's node_modules so the lifeos-ds source files resolve them even
    // though lifeos-ds/node_modules isn't installed in CI (it's gitignored).
    alias: {
      "lifeos-ds": resolve(__dirname, "../lifeos-ds/src/index.ts"),
      react: resolve(__dirname, "node_modules/react"),
      "react-dom": resolve(__dirname, "node_modules/react-dom"),
    },
    dedupe: ["react", "react-dom"],
  },
});
