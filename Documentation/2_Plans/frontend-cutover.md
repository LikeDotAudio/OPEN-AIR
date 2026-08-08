# Plan — Blend `ui/` into the Front End and Cut Over

**Date:** 2026-08-07
**Goal:** one front end. No wrapper, no cross-tree imports, no Babel-in-browser. `ui/` becomes *the* app.

---

## Measured starting point

| | |
|---|---:|
| Legacy files in the graph | **142** (135 `.jsx`, 7 `.js`) |
| Lines | **20,111** |
| Files already using `import`/`export` | **0** |
| `window.X = …` assignments (de-facto exports) | **222** |
| `window.X` references (de-facto imports) | **995** |

The 20k lines are not the hard part. **995 global reads and 222 global writes are** — that is a dependency graph currently held together by `<script>` tag order, and it has to be rebuilt as real imports.

Two things are already true and verified:

- `vite build` transforms **1,018 modules** and produces a working bundle.
- **Step 1 below is done** — the trees are blended, `legacy.ts` has zero `../../FrontEnd` imports, build stays green.

---

## Step 1 — Blend the trees ✅ DONE

142 files **copied** to `ui/src/legacy/<original path>`; every `legacy.ts` import rewritten from `../../FrontEnd/…` to `./legacy/…`.

Copied, not moved, deliberately: `FrontEnd/index.html` is still the served runtime, so the originals must stay until Step 4. **The tree is therefore duplicated right now** — `ui/src/legacy/` is authoritative for the bundle, `FrontEnd/` for the running app. Edit both or neither until the cutover.

**Verify:** `cd ui && ./node_modules/.bin/vite build` → 1,018 modules, no errors.

## Step 2 — Prove the bundle actually runs

Building is not running. Before deleting anything, serve `ui/dist` and confirm the app boots against the live broker: panels render, MQTT connects, a bound control moves the N9340B, a reading hydrates a slider.

```bash
cd ui && ./node_modules/.bin/vite preview --port 8100
```

**Gate:** anything that fails here is a load-order or globals problem that Step 3 must fix. Do not proceed on a green build alone.

## Step 3 — Convert globals to modules, in dependency order

The mechanical core. For each file, `window.X = …` becomes `export const X`, and each `window.Y` read becomes an `import { Y }`.

**Do it with a generated symbol table, not by hand:**

1. Build `{symbol → defining file}` from all 222 assignments.
2. Build `{file → symbols it reads}` from the 995 references, **filtered to symbols in that table** — `window.requestIdleCallback`, `window.location`, `window.OA_MQTT_DEBUG` and other runtime/browser globals must stay untouched.
3. Topologically sort. Cycles are expected: convert those files as a group and keep function declarations (hoisted) rather than `const` at module scope.
4. Emit imports/exports file by file, rebuilding after each batch.

**Order matters** — convert leaves first. `libControl/faders/core/utils.js` is the natural start: top of the load order, no dependents.

**Keep `window.X = X` alongside the new `export`** until Step 4. Anything still unconverted reads the global, and removing it early breaks the file that has not been reached yet. Delete the window assignments only when the last consumer is converted.

## Step 4 — The cutover

One switch, not a slide:

1. Point the orchestrator's static root at `ui/dist` instead of `FrontEnd/` (`api.rs:296`).
2. Delete the `<script>` tags from `FrontEnd/index.html`.
3. **Delete `FrontEnd/` originals** for the 142 blended files — this is where the duplication from Step 1 ends.
4. Keep `FrontEnd/Gui_Frames/`, `FrontEnd/api/` and `FrontEnd/assets/`: they are data and assets the backend reads by path (`api.rs:93`, `:203`, `:368`), not part of the JS graph.

**Verify:** panels load, WYSIWYG save still writes to `Gui_Frames`, `/api/tree.json` still resolves.

## Step 5 — Strip the wrapper

`main.tsx` exists to recreate the CDN world — it assigns React, ReactDOM, echarts and mqtt onto `window` so unconverted files find them. Once Step 3 is complete, every file imports them directly:

- delete the `window.React = …` block from `main.tsx`
- delete `legacy.ts` entirely (its own header says: *"Empty file = done"*)
- delete `scripts/gen-legacy.ts`, which generated it from `index.html`

## Step 6 — Type it

Rename `.jsx` → `.tsx` in batches and run `pnpm typecheck`. This is where the migration pays: 995 globals that were unknowable become checked imports. Expect real bugs to surface — of the same family as the two found on 2026-08-07 (a converter that matched nothing, an option key sent where a value belonged).

---

## Risks

| Risk | Mitigation |
|---|---|
| **Duplicated tree between Steps 1 and 4** — an edit lands in one copy only | Finish the cutover promptly; until then treat `FrontEnd/*.jsx` as frozen |
| Circular globals that ES modules cannot express | Convert cycles as a group; prefer hoisted `function` over `const` |
| Load-order side effects (a file that registers into another at import time) | `legacy.ts` preserves exact script-tag order — keep that order until every file is converted |
| A `.js` file containing JSX | 7 `.js` files — Vite needs them renamed `.jsx` or configured, or the build fails on the first JSX token |
| Uncommitted work being lost | **Commit before starting.** An uncommitted reorg already destroyed three audit documents this session |

## Definition of done

- `ui/src/legacy/` is empty and deleted
- `legacy.ts` and `gen-legacy.ts` are gone
- `main.tsx` assigns nothing to `window`
- The orchestrator serves `ui/dist`
- `FrontEnd/` holds only `Gui_Frames/`, `api/`, `assets/`
- `pnpm typecheck` passes
