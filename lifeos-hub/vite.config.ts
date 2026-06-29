import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "path";

// Single-page LifeOS Quest Hub. Imports the design system straight from source
// so the hub and the library stay in lockstep. `base: "/hub/"` matches where the
// site mounts it (public/hub) so assets resolve as /hub/assets/* — correct even
// when served at /hub with no trailing slash (Vercel trailingSlash:false).
export default defineConfig({
  base: "/hub/",
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
