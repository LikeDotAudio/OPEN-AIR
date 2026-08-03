# `ui/` — the typed frontend

The TypeScript + Vite package that is replacing the browser-Babel app. It
**builds the entire application today**; `FrontEnd/index.html` remains the
served runtime until the cutover.

```bash
pnpm --filter ui dev      # Vite dev server (:5173), proxies /api → orchestrator :8000
pnpm --filter ui build    # one bundle, content-hashed
pnpm --filter ui typecheck
pnpm --filter ui lint
```

## Why a separate package

UI code is isolated from data. `FrontEnd/` keeps the things that are *not*
code — `Gui_Frames/` (your panels) and `api/` — plus the shrinking pile of
unconverted legacy source. Converted modules live in `ui/src`.

**One module lives in exactly one tree.** Converting a file is a `git mv` into
`ui/src` (plus real types) in a single commit — never a copy, so there is
never a second source of truth, only a moving boundary. CI enforces it
(`scripts/check-collisions.ts`).

## How the legacy app is absorbed

| File | Role |
|---|---|
| `src/legacy.ts` | **Generated** by `pnpm gen:legacy` from `FrontEnd/index.html`: one side-effect import per script tag, *in exact tag order* — that order is the dependency graph nobody wrote down. Every conversion deletes one line; empty file = migration structurally done |
| `src/main.tsx` | Recreates the CDN-globals world (`window.React/ReactDOM/echarts/mqtt`) from npm singletons **before** the legacy graph loads, so converted imports and unconverted `window.*` readers share one React instance |
| `src/boot.tsx` | The app bootstrap (tree fetch → `MqttProvider` → `WindowManager`), converted from the inline `text/babel` block that no tag scan could capture |
| `src/globals.d.ts` | **Generated** by `pnpm gen:globals`: the inventory of the ~180 `window.*` globals that are the legacy module system. Hand-typed entries survive regeneration — the count of remaining `any` is the migration's progress bar |

## Ratchets

Progress is made visible and regression made impossible:

- ESLint forbids new `window.*` access in `.ts/.tsx` outside the named bridge
  files (`main`, `legacy`, `boot`).
- CI forbids `.js`/`.jsx` under `ui/src`, checks generated files are fresh,
  and fails if any module exists in both trees.
- Dependencies are exact-pinned (React 18.3.1 — the version the CDN tag
  resolves to today — echarts 5.5.0, echarts-gl 2.0.9, mqtt 5.10.1).

> `ui/` is pinned to TypeScript 5.9 because typescript-eslint cannot yet parse
> TS 7; `contracts/` runs TS 7.

## Cutover (pending)

The remaining work is deliberately human-supervised: deploy `index.html`
(bundle) beside a frozen `index-legacy.html` for one week, ship a
self-unregistering service worker *before* the PWA plugin, then delete the
splash, the `?v=N` cache-busters, and the legacy entry. Until that happens,
changes to legacy `.jsx` files must bump their `?v=` tag in `index.html` — the
bundle content-hashes, the legacy page does not.
