/**
 * The one-module-one-tree check (Phase 2 §1.1/§2.5, CI-enforced): a module
 * may live in FrontEnd/ (unconverted) or ui/src (converted) — NEVER both.
 * Conversion is `git mv`, not copy; a stem present in both trees means a
 * copy happened and there are now two sources of truth. Exit 1, name them.
 */
import { readdirSync, statSync } from 'node:fs'
import { dirname, join, relative } from 'node:path'
import { fileURLToPath } from 'node:url'

const UI_DIR = join(dirname(fileURLToPath(import.meta.url)), '..')
const FRONTEND = join(UI_DIR, '../FrontEnd')
const SKIP = new Set(['Gui_Frames', 'api', 'node_modules', 'wasm', 'dist'])

function stems(root: string, sub: string): Map<string, string> {
  const out = new Map<string, string>()
  const walk = (dir: string) => {
    let entries: string[]
    try {
      entries = readdirSync(dir)
    } catch {
      return
    }
    for (const e of entries) {
      if (SKIP.has(e)) continue
      const p = join(dir, e)
      if (statSync(p).isDirectory()) walk(p)
      else if (/\.(jsx?|tsx?)$/.test(e)) {
        const rel = relative(join(root, sub), p)
        out.set(rel.replace(/\.(jsx?|tsx?)$/, ''), rel)
      }
    }
  }
  walk(join(root, sub))
  return out
}

const legacy = stems(FRONTEND, '.')
const converted = stems(UI_DIR, 'src')

const collisions: string[] = []
for (const [stem, rel] of converted) {
  if (stem === 'main' || stem === 'legacy' || stem === 'globals.d' || stem === 'vite-env.d') continue
  if (legacy.has(stem)) collisions.push(`${stem}  (FrontEnd/${legacy.get(stem)} AND ui/src/${rel})`)
}

if (collisions.length) {
  console.error(`COLLISION — module in both trees (copy instead of git mv):\n  ${collisions.join('\n  ')}`)
  process.exit(1)
}
console.log(`collision check OK — ${converted.size} converted, ${legacy.size} legacy, 0 overlaps`)
