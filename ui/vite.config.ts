import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import wasm from 'vite-plugin-wasm'

// Phase 2 Step 1 (Documents/Strategies/Phase 2 Step 1.md).
export default defineConfig({
  plugins: [react(), wasm()],
  // Output must work from the FTPS static host's subpath, not a domain root.
  base: './',
  server: {
    fs: {
      // legacy.ts imports the unconverted ../FrontEnd files across the
      // package boundary — one module, one tree, a moving boundary.
      allow: ['..'],
    },
    proxy: {
      // GET /api/tree, POST /api/save → the orchestrator (axum), which also
      // serves FrontEnd/ statically — so its assets (splash gif) proxy too.
      '/api': 'http://localhost:8000',
      '/assets': 'http://localhost:8000',
    },
  },
  build: {
    outDir: 'dist',
    // wasm-bindgen output (oa_panels) needs ES2022 for top-level await
    // once the Panels family converts; harmless for the legacy graph.
    target: 'es2022',
    commonjsOptions: { transformMixedEsModules: true },
  },
})
