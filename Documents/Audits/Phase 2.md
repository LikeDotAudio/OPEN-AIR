# Phase 2 Deep Dive — Frontend to TypeScript: Best Practices, Scaffolding, Setup

*2026-07-17 · Companion to [3_TypeScript_Migration_Plan.md](3_TypeScript_Migration_Plan.md)
Phase 2 and [Phase 1.md](Phase%201.md) (contracts — the dependency this phase
types against). Objective restated: **the user sees nothing change**; the
platform under them goes from Babel-in-browser + 160 script tags to one typed,
bundled, tree-shaken artifact.*

---

## 0. Ground truth

What Phase 2 is actually migrating, from the repo as it stands:

- **No build system exists.** React and Babel come from CDNs; 142 `.jsx`
  files are compiled *in the browser on every load*; `index.html` loads ~160
  ordered `<script>` tags with hand-edited `?v=N` cache busters; the 2.5 s
  splash exists to hide compile time.
- **~197 `window.*` globals** are the module system (`window.OaTopicMaker`,
  `window.generateTopicPathFromFilepath`, widget registrations, providers).
  This is the real migration surface — the JSX→TSX conversion is mechanical;
  untangling implicit global load-order dependencies is the work.
- **Deploys are FTPS uploads of the raw tree**
  (`.github/workflows/deploy-{sandbox,production}.yml` →
  `FrontEnd/deploy_FTP_to_like_dot_audio.py`), and the deploy script is what
  regenerates `FrontEnd/api/tree.json` — the stale snapshot `index.html:244`
  reads. The deploy pipeline must learn to build before it uploads.
- **A PWA shell exists** (`manifest.json`, hand-written `sw.js`) — a service
  worker caching hand-versioned files is exactly what will serve users a
  stale bundle after the switch unless it's migrated deliberately.
- **One WASM package is already in-tree**:
  `FrontEnd/libControl/Panels/wasm/` (`oa_panels`, wasm-bindgen, committed
  `pkg/` output) — the bundler choice must load wasm-pack output cleanly,
  because Phase 3's YAK core arrives the same way.
- Known dispatch/typing debts this phase deletes:
  `WidgetFactory.jsx:110-130` substring-match widget dispatch,
  `WindowManager.jsx` at 708 lines doing four jobs, dead `TabManager.jsx`,
  `js/app.js`, `css/style.css`, duplicate splash JSX in `index.html`.

---

## 1. Scaffolding

### 1.1 Placement: a new `ui/` package — UI code isolated from data

**Ruling (2026-07-17, Anthony): UI work lives in its own folder.** The typed
app is a new `ui/` package at the repo root, joining the pnpm workspace from
Phase 1 (whose scaffold already reserved the slot). `FrontEnd/` keeps two
roles during migration: the *data* neighbors (`Gui_Frames/`, `api/`) and the
shrinking pile of unconverted legacy source.

The two-sources-of-truth risk that made in-place conversion tempting is
answered by one hard rule instead: **every module lives in exactly one
tree.** Converting a file means `git mv FrontEnd/.../X.jsx ui/src/.../X.tsx`
(plus real types) in a single commit — nothing is ever copied, so there is
never a second source of truth, only a moving boundary. `ui/src/legacy.ts`
imports the *unconverted* files across that boundary by relative path (Vite
bundles outside its root via `server.fs.allow`).

Endgame: `FrontEnd/` contains only data (`Gui_Frames/`, `api/`), and the
Phase 5 reshape is a rename of data folders (`panels/`) touching no code.

```
ui/
├── package.json            # deps: react@18 (pin exactly), mqtt, echarts, zod,
│                           #       @openair/contracts (workspace:*)
├── vite.config.ts          # fs.allow: ['..'] so legacy.ts can reach ../FrontEnd
├── tsconfig.json           # allowJs: true — the migration switch;
│                           #   includes ../FrontEnd/**/*.jsx
├── index.html              # Vite-owned entry; loses 160 tags, splash, ?v=N
└── src/
    ├── main.tsx            # single entry; explicit import graph starts here
    ├── globals.d.ts        # typed window.* inventory (§2)
    ├── legacy.ts           # ordered imports of ../FrontEnd files not yet converted
    └── comMQTT/ libControl/ tabManager/ frameLayout/ editorWYSIWYG/
                            # converted files land here, mirroring their old family

FrontEnd/
├── Gui_Frames/ api/        # data, not code — served and deployed alongside ui/dist
└── comMQTT/ libControl/ ...# unconverted legacy source; every conversion shrinks it
```

### 1.2 Vite config essentials

- `plugins: [react()]`; `base: './'` — output must work from the FTPS static
  host's subpath, not assume a domain root.
- Dev server proxy: `/api` → the orchestrator (axum, port 8000) so
  `GET /api/tree` and `POST /api/save` work under `vite dev`. MQTT needs no
  proxy — the browser speaks WebSocket to the broker (9001) directly; put the
  broker URL in `import.meta.env.VITE_MQTT_URL` (a real `.env` file already
  exists — formalize it with an `.env.example`).
- WASM: wasm-pack `pkg/` output imports as a normal ES module under Vite
  (`vite-plugin-wasm` + `topLevelAwait` if needed). Prove it with `oa_panels`
  in week one — it de-risks Phase 3's WASM core landing here. It imports from
  `../FrontEnd/libControl/Panels/wasm/pkg` until the Panels widget family
  converts, at which point the crate moves under `ui/` with its consumers.
- Real dependencies replace CDNs: **pin `react`/`react-dom` to the exact
  version the CDN serves today** (check the `<script src>` URLs before
  deleting them — behavior differences between React 18 minors are rare but
  real), `mqtt` (MQTT.js), `echarts`. Lockfile committed; no CDN fallbacks.

### 1.3 tsconfig for an incremental migration

```jsonc
{
  "compilerOptions": {
    "strict": true,                // full strength for every NEW .ts/.tsx file
    "allowJs": true,               // old .jsx compiles as-is, unchecked
    "checkJs": false,              // do NOT lint the legacy — convert instead
    "jsx": "react-jsx",
    "module": "ESNext", "moduleResolution": "bundler",
    "noUncheckedIndexedAccess": true,
    "paths": { "@contracts/*": ["../contracts/src/*"] }
  }
}
```

The rule that makes this work: **strictness is per-file and one-way.** A file
converted to `.tsx` is fully strict from that moment; there is no
`// @ts-nocheck` era, no "convert now, type later" era. `allowJs` is the
bridge for the *unconverted*, not a looser mode for the converted.

---

## 2. The `window.*` problem — the actual migration mechanic

The ~197 globals are an implicit, load-order-sensitive module graph. The
migration mechanic, file by file:

1. **Inventory first.** One grep session produces `src/globals.d.ts`: every
   `window.Oa*` (and friends) declared with its real type — `any` allowed
   *here and only here*, burned down as conversion proceeds. This file is the
   migration's progress bar: `grep -c any src/globals.d.ts` is the metric.
2. **Leaf-first conversion, dual-export during transition.** A converted
   module gains real `export`s *and* keeps its `window.X = ...` assignment,
   marked `/** @deprecated window bridge — remove when last consumer imports */`.
   Converted consumers import; unconverted consumers keep reading the global.
   When the last consumer converts, the bridge line dies.
3. **`src/legacy.ts` replaces the 160 script tags**: side-effect imports of
   every unconverted `../FrontEnd` file *in the exact current tag order* (the
   order encodes the dependency graph nobody wrote down). Every conversion
   `git mv`s one file into `ui/src` and deletes one line. Empty file =
   migration structurally done, and `FrontEnd/` is data-only.
4. **Ratchet by lint** (same philosophy as the Phase 1 validate baseline):
   ESLint `no-restricted-properties` forbids *new* `window.*` reads/writes in
   `.ts/.tsx`, with the shrinking bridge list as exceptions; a repo rule
   forbids new `.jsx` files outright. The numbers only go down.
5. **Archive markers + checks, every step** (ruling 2026-07-17, Anthony):
   every move, conversion, deletion, or retirement is recorded as an
   append-only line in `Documents/Audits/Migration_Ledger.md`
   (`date | action | old path | new path/— | commit | note`), and `CHANGELOG.md`
   gets an entry per shipped step. CI enforces the trail: a **collision
   check** fails if any module exists in both `FrontEnd/` and `ui/src`
   (copy instead of move), and a **ledger check** fails if `legacy.ts`
   shrank without a matching ledger line. Nothing disappears silently —
   the ledger is the archive marker; git history is the archive.

Conversion order (leaf-first, per the migration plan, now with the mechanics
above): `topicMaker.jsx` (delegates to `@openair/contracts` `Topics` — Phase 1
already pinned its behavior with vectors) and `oaCssLen` → `MqttProvider.jsx`
→ `WidgetFactory` + `FieldComponent` → widget batches by `libControl/` family
→ `tabManager/WindowManager.jsx` last — split into tab engine / split-pane /
MQTT lazy-publisher / editor bridge as it converts → `editorWYSIWYG/` very
last (it gains the zod save-gate: saves must pass the contracts layout schema
before `POST /api/save`).

---

## 3. Typed patterns that replace today's fuzzy ones

### 3.1 Widget registry kills substring dispatch

```ts
// libControl/registry.ts
const registry = new Map<string, WidgetDef>()
export function register<S extends z.ZodType>(def: {
  type: string                      // exact, unique — collisions throw at import time
  component: React.ComponentType<z.infer<S>>
  schema: S                         // props validated at mount in dev builds
}) { ... }
```

Each widget module registers itself; `WidgetFactory` becomes a lookup —
unknown `type` renders a loud error widget (visible red box naming the type
and the panel file), never a silent dashed fallback. This deletes
`WidgetFactory.jsx:110-130`'s `type.includes('fader')` roulette, and the
`schema` field is what Phase 3's editor dry-run validates panels against.

### 3.2 MQTT layer: contracts in, hooks out

`MqttProvider` converts early because everything sits on it, and it's where
the contracts topic grammar becomes load-bearing in the app:

```ts
useMqttValue(Topics.gui.fromPanelPath(panelPath, field))   // subscribe, typed
usePublish()   // strict writer: retain=false by default (Phase 0 item 5 lands
               // here permanently); retained ONLY via an explicit, documented
               // publishRetained() for config/state topics
```

The heartbeat publisher moves onto the `AgentHeartbeat` contract schema
(already seeded from this exact payload in Phase 1, step 3).

### 3.3 Lint/format floor

`eslint` flat config + `typescript-eslint` (strict) + `eslint-plugin-react-hooks`,
`prettier` — with only three custom rules that matter, all ratchets:
no new `window.*` (§2.4), no new `.jsx`, no `z.any()` without a `WHY` comment
(inherited from contracts). CI runs lint + `tsc --noEmit` + `vitest` on every
PR; keep it under a couple of minutes or it gets bypassed.

Testing floor (not a testing program — a floor): vitest + Testing Library
smoke tests for the registry (`every registered type mounts with its schema's
sample props`) and for `Topics` round-trips; the contracts vector suite
already covers the grammar. Deeper e2e (Playwright against a live broker) is
worth it only after the bundle is the only runtime.

---

## 4. Cutover, deploy, and the PWA trap

The riskiest hour of Phase 2 is not a conversion — it's the moment the bundle
replaces the script tags, and the deploy/caching machinery around it.

1. **Two-entry overlap window.** Keep `index.html` (bundle) and a temporary
   `index-legacy.html` (the old 160-tag page, unchanged) deployed side by side
   for the first cutover week. Any "the bundle broke X" report gets a
   30-second A/B answer instead of a revert.
2. **Deploy learns to build.** The GitHub workflows gain a Node step:
   `pnpm install --frozen-lockfile && pnpm --filter ui build`, then the
   FTPS script uploads `ui/dist/` + `FrontEnd/Gui_Frames/` + `FrontEnd/api/`
   instead of the raw source tree. The deploy script's `tree.json` regeneration survives only
   until Phase 0 item 2 / Phase 5 make the live tree real — don't entangle
   that fix with this phase.
3. **Service worker, handled deliberately.** The hand-written `sw.js` +
   `?v=N` era ends: Vite emits content-hashed filenames, so caching becomes
   trivial *if* the old SW doesn't keep serving the old app. Ship, in order:
   (a) a one-deploy SW that self-unregisters and clears caches, then (b)
   `vite-plugin-pwa` with `registerType: 'autoUpdate'`, precaching the hashed
   bundle but **never** `api/` or `Gui_Frames/` (network-first — panels are
   data, and stale panels are this project's signature failure mode).
4. **Delete on the way out**: the splash (`index.html` inline JSX duplicate
   included — with browser-Babel gone, there is no compile to hide),
   `TabManager.jsx`, `js/app.js`, `css/style.css`, empty `comDatabase/` and
   `Core/Launch/`, and every `?v=` string in the repo. Each deletion is one
   ledger line (§2.5) — nothing leaves the tree without its archive marker.

---

## 5. Definition of done

- [ ] `index.html` loads exactly one JS entry; zero CDN scripts, zero Babel,
      zero `?v=N`; splash removed; `index-legacy.html` deleted after the
      overlap window
- [ ] `src/legacy.ts` is empty and deleted; zero `.jsx` files remain;
      `globals.d.ts` contains zero `any`
- [ ] `FrontEnd/` contains no executable code — only `Gui_Frames/` and `api/`
      remain; all source lives under `ui/src`
- [ ] Every move/deletion has a `Migration_Ledger.md` line; the CI collision
      and ledger checks are green (no module in both trees, no silent removals)
- [ ] Widget registry: every widget registered with exact type + props schema;
      unknown types render the loud error widget (proven by a test)
- [ ] All topic construction goes through `@openair/contracts` `Topics`;
      `topicUtils.js` long gone (Phase 1), `topicMaker.jsx` now a re-export
- [ ] Editor save-gate: invalid layout JSON cannot reach `POST /api/save`
- [ ] CI: lint + typecheck + vitest green; deploy workflows build then upload
      `dist/`; SW serves hashed assets, network-first for data
- [ ] `retain: false` is the publish default; retained publishes are explicit
      call-sites you can grep

## 6. Risks

- **The bundle changes load *timing*, not just load *order*** — code that
  worked because script tag #83 ran before #84 may hide races that ESM's
  stricter graph exposes. Counter: `legacy.ts` preserves order exactly;
  conversions move one file at a time so the bisect is always one commit.
- **Dual-runtime drift during the overlap window** (a fix lands in the bundle
  but not legacy or vice versa). Counter: the window is one week, time-boxed,
  and legacy is frozen — fixes land in the bundle only.
- **React CDN/npm version mismatch** producing subtle hook/StrictMode
  differences. Counter: pin npm React to the CDN's exact version first; any
  React upgrade is its own later commit.
- **SW serves the old app forever** on some user's machine. Counter: step
  4.3(a) — the self-destructing SW deploy *precedes* the PWA plugin.
- **Conversion fatigue** — 142 files invites a stall at 60%. Counter: the
  ratchets (lint rules, shrinking `legacy.ts`, `any`-count in `globals.d.ts`)
  make progress visible and regress impossible; widget batches are
  parallelizable and mechanical by design.
