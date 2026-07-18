# Phase 2 Step 1 — the `ui/` Scaffold: Deployment Checklist

*2026-07-18 · Companion to [Phase 2.md](Phase%202.md) §1. Scope: the isolated
`ui/` package exists, builds, and captures the legacy load order — **no
cutover**. `FrontEnd/index.html` is untouched; the legacy app remains the
only runtime until the overlap window (Phase 2 §4) opens deliberately.*

## Ground truth (2026-07-18)

- `FrontEnd/index.html` loads **152** script tags: 6 CDN + 146 local
  (141 of them `type="text/babel"`).
- CDN versions to pin: React/ReactDOM **18 via floating `@18` unpkg tag,
  development builds** (today resolves 18.3.1 — pin that exactly, and note
  the bundle switches to production builds at cutover: a behavior delta the
  overlap window exists to catch); Babel standalone 7.23.0 (dies with the
  bundle); **echarts 5.5.0 + echarts-gl 2.0.9** (gl was missed in the plan's
  dependency list); mqtt.js unpinned on CDN — pin current 5.x.
- `index.html` still references the deleted Sampler files — the tag scan
  must warn-and-skip missing targets rather than import 404s.
- wasm: `libControl/Panels/wasm/pkg/oa_panels.js` (wasm-bindgen output)
  loads as a plain script + `panel_wasm_loader.js`.

## Checklist

| # | Deliverable | Check |
|---|---|---|
| 1 | `ui/` package: exact-pinned deps (react 18.3.1, echarts 5.5.0, echarts-gl 2.0.9, mqtt, zod, `@openair/contracts` workspace:*), Vite + strict tsconfig (`allowJs` for the unconverted, per-file one-way strictness) | `pnpm install` clean; `tsc --noEmit` green |
| 2 | `vite.config.ts`: `base './'` (FTPS subpath), `server.fs.allow ['..']` (legacy imports cross the package boundary), `/api` proxy → orchestrator :8000, wasm plugin | config typechecks; dev server boots |
| 3 | `scripts/gen-legacy.ts`: parses `FrontEnd/index.html`, emits `src/legacy.ts` — side-effect imports of every local tag **in exact tag order** (the order IS the undocumented dependency graph), CDN tags dropped (npm now), missing files warned + skipped with a comment | generated file committed; regen is deterministic |
| 4 | `src/main.tsx`: exposes the npm singletons as the globals the unconverted files expect (`window.React`, `ReactDOM`, `mqtt`, `echarts`) BEFORE importing `legacy.ts` | build includes legacy graph |
| 5 | **Build green**: `pnpm --filter ui build` bundles main + the full legacy graph; files esbuild cannot parse get commented out of `legacy.ts` with a named reason (they keep working via the untouched legacy page — nothing breaks; the comment is the work list) | `vite build` exit 0; wasm chunk emitted |
| 6 | Ledger + changelog rows; `.env.example` with `VITE_MQTT_URL` | standing archive ruling |

## Non-goals (deliberate)

- No `index.html` cutover, no `index-legacy.html`, no SW work — that is the
  §4 overlap window, its own step with a browser in the loop.
- No file conversions, no `window.*` inventory burn-down (step 2+).
- The bundle does not need to RUN the app yet — it needs to BUILD it. Runtime
  parity is exactly what the overlap window verifies with human eyes.

## Risks

- **JSX in `.js` files / stray syntax** esbuild rejects → the legacy.ts
  comment-out mechanism names each one; the legacy page keeps serving them.
- **Automatic JSX runtime vs global React**: converted/bundled files get the
  npm React via the plugin; unconverted files reading `window.React` get the
  same instance from main.tsx. One React, two access paths — verified at
  overlap, pinned exact now.

---

## Cutover-prep addendum (2026-07-18, done after step 1 shipped)

- **`src/boot.tsx`**: the app boot half extracted from `index.html`'s inline
  `text/babel` block (gen-legacy can't capture inline scripts — without this
  the bundle loaded 142 files and booted nothing). Converted TSX; the splash
  minimum-timer is gone (no compile to hide). Legacy page keeps its inline
  copy until cutover, by design.
- **`src/globals.d.ts`**: generated inventory of the window.* surface —
  **182 globals** (audit estimated ~197), 3 hand-typed so far
  (`MqttProvider`, `WindowManager`, `oaGetMqttConfig`); hand-typed entries
  survive regeneration. `pnpm gen:globals`.
- **Ratchets armed**: eslint floor (no `window.*` outside the named bridge
  files: main/legacy/boot), CI `ui` job (freshness of generated files,
  one-module-one-tree collision check, no-js/jsx-in-src, typecheck, lint,
  build). ui pinned to TS 5.9 (typescript-eslint cannot parse TS 7 yet;
  contracts stays on 7).

### Headless smoke test (Chrome, virtual-time, dist staged like the FTPS host)

**The bundle boots and renders the real app** — same tab set as the legacy
page served identically (Console/Protocols/Samples/Setup), MQTT layer
initializes with the same default broker config. The bundle is *cleaner*:
the legacy page throws 3 uncaught errors loading the deleted Sampler files;
the bundle skipped those tags by name.

Known deltas for the human overlap window:
1. `[OAPanels] pkg/oa_panels.js must be loaded before panel_wasm_loader.js`
   — module-graph ordering differs from plain script tags for the wasm pair;
   fix lands with the Panels family conversion.
2. widget-wrapper counts differed in the headless run (11 vs 16) — likely
   lazy-load timing under virtual time, but it is exactly the kind of thing
   the §4 overlap window's human eyes must confirm.
