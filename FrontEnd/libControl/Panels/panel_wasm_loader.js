// frontEnd/libControl/Panels/panel_wasm_loader.js
// Author: Anthony Peter Kuzub
//
// Classic (non-Babel) bootstrap for the procedural panel/screw WASM engine.
// Loaded AFTER pkg/oa_panels.js (which defines the global `wasm_bindgen`
// no-modules init). It initialises the wasm once and bridges the exports to
// `window.OAPanels` so the Babel components only ever touch window.* globals.
//
// It also publishes `window.OA_PANEL_DEFAULT_CONFIG` — the single "global panel"
// used as the default background across the board. A page/container can override
// it by declaring its own panel config (see Panel.jsx / OcaBin.jsx).
(function () {
  "use strict";

  // The global default "cover": brushed steel with a faint paint wash, an edge
  // vignette, a soft global blur, and screws auto-fastened top & bottom. Mirrors
  // oaGuiElements/Constants/gui_constants.py:DEFAULT_PANEL_CONFIG, plus screws
  // (the desktop default leaves screws off; the web "global cover" wants them).
  window.OA_PANEL_DEFAULT_CONFIG = {
    type: "layered_industrial",
    parameters: {
      random_seed: 304,
      global_blur: 0.5,
      base_material: { color: "#2a2a2a", texture_type: "brushed", grain_intensity: 0.35 },
      paint_layer: { color: "#3a4a5a", opacity: 0.15, gradient_intensity: 0.2 },
      edge_wear: { enabled: true, fade_depth: 30, vignette_intensity: 0.5 },
      screws: { enabled: true, type: "fillister", finish: "chrome", size_px: 22, locations: ["top", "bottom"] }
    }
  };

  if (typeof wasm_bindgen === "undefined") {
    console.error("[OAPanels] pkg/oa_panels.js must be loaded before panel_wasm_loader.js");
    return;
  }

  // Kick off wasm init immediately (async). We pass an EXPLICIT wasm URL (with a
  // version query for cache-busting) rather than letting the glue auto-derive it
  // from its own <script src> — a "?v=" on the oa_panels.js tag would break the
  // glue's `.js -> _bg.wasm` path rewrite. Absolute path: server root = frontEnd/.
  var WASM_URL = "/libControl/Panels/wasm/pkg/oa_panels_bg.wasm?v=2";
  var readyResolve, readyReject;
  var ready = new Promise(function (res, rej) { readyResolve = res; readyReject = rej; });

  wasm_bindgen({ module_or_path: WASM_URL })
    .then(function () {
      window.OAPanels.isReady = true;
      readyResolve(window.OAPanels);
    })
    .catch(function (err) {
      console.error("[OAPanels] WASM init failed:", err);
      readyReject(err);
    });

  window.OAPanels = {
    isReady: false,
    ready: ready,
    // Returns a Uint8Array of RGBA bytes (width*height*4). config is a JS object.
    generatePanel: function (width, height, config) {
      return wasm_bindgen.generate_panel(width | 0, height | 0, JSON.stringify(config || {}));
    },
    // Returns RGBA bytes for a single screw on a square canvas (screwCanvasDim).
    generateScrew: function (size, config) {
      return wasm_bindgen.generate_screw(size | 0, JSON.stringify(config || {}));
    },
    screwCanvasDim: function (size) {
      return wasm_bindgen.screw_canvas_dim(size | 0);
    }
  };
})();
