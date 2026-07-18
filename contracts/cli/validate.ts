/**
 * openair-validate — the walk-and-report CLI (guidelines §7).
 *
 *   pnpm validate [rootDir] [--report json|pretty|summary] [--strict]
 *
 * Walks FrontEnd/Gui_Frames (layout schema, legacy mode), applies the extra
 * YAK-tree rules under 5_Protocols/10_Yak, checks folder grammar, and lints
 * every BackEnd config.ini `topic*` value against the topic grammar.
 *
 * Exit code: nonzero on ERRORS only; --strict flips deprecations to errors.
 * Output is data first: --report json is the canonical debt inventory.
 */
import { createHash } from 'node:crypto'
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { basename, dirname, join, relative } from 'node:path'
import { fileURLToPath } from 'node:url'

import { validateLayoutDocument, type LayoutIssue } from '../src/layout/node.js'
import { findOrderCollisions, parseFolderName } from '../src/layout/folder-grammar.js'
import { Topics } from '../src/topics/builders.js'

interface FileReport {
  file: string
  issues: LayoutIssue[]
}

const args = process.argv.slice(2)
const strict = args.includes('--strict')
const reportMode = args[args.indexOf('--report') + 1] && args.includes('--report')
  ? (args[args.indexOf('--report') + 1] as 'json' | 'pretty' | 'summary')
  : 'pretty'
const REPO_ROOT = join(dirname(fileURLToPath(import.meta.url)), '../..')
const roots = args.filter((a) => !a.startsWith('--') && a !== reportMode)
const GUI_ROOT = roots[0] ?? join(REPO_ROOT, 'FrontEnd/Gui_Frames')
const BACKEND_ROOT = join(REPO_ROOT, 'BackEnd')
const YAK_SUBTREE = join(GUI_ROOT, '5_Protocols/10_Yak')

const reports: FileReport[] = []
const treeIssues: LayoutIssue[] = []

function push(file: string, issues: LayoutIssue[]) {
  if (issues.length) reports.push({ file, issues })
}

// ---------------------------------------------------------------- walkers

function* jsonFiles(dir: string): Generator<string> {
  for (const e of readdirSync(dir).sort()) {
    const p = join(dir, e)
    if (statSync(p).isDirectory()) yield* jsonFiles(p)
    else if (e.endsWith('.json') || e.endsWith('.json.old')) yield p
  }
}

function walkLayoutTree() {
  for (const file of jsonFiles(GUI_ROOT)) {
    const rel = relative(GUI_ROOT, file)
    if (file.endsWith('.json.old')) {
      // reported by the yak-tree rules below; skip schema walk
      continue
    }
    let doc: unknown
    try {
      doc = JSON.parse(readFileSync(file, 'utf8'))
    } catch (e) {
      push(rel, [{ level: 'error', code: 'parse-error', path: '', message: String(e) }])
      continue
    }
    push(rel, validateLayoutDocument(doc))
  }
}

function walkFolderGrammar(dir: string) {
  const entries = readdirSync(dir).sort()
  const dirs = entries.filter((e) => statSync(join(dir, e)).isDirectory())
  for (const c of findOrderCollisions(dirs)) {
    treeIssues.push({
      level: 'error',
      code: 'folder-order-collision',
      path: relative(GUI_ROOT, dir) || '.',
      message: `ordering prefix ${c.order}_ claimed by: ${c.names.join(', ')}`,
    })
  }
  for (const d of dirs) {
    const p = parseFolderName(d)
    if (!p.geometry && !p.split && p.base === '') {
      treeIssues.push({
        level: 'error',
        code: 'unparseable-folder-name',
        path: join(relative(GUI_ROOT, dir), d),
        message: `folder name "${d}" yields an empty topic segment`,
      })
    }
    walkFolderGrammar(join(dir, d))
  }
}

function walkYakTreeRules() {
  let files: string[]
  try {
    files = [...jsonFiles(YAK_SUBTREE)]
  } catch {
    treeIssues.push({ level: 'error', code: 'yak-tree-missing', path: YAK_SUBTREE, message: 'YAK subtree not found' })
    return
  }
  const byMd5 = new Map<string, string[]>()
  for (const file of files) {
    const rel = relative(GUI_ROOT, file)
    if (file.endsWith('.json.old')) {
      treeIssues.push({ level: 'deprecation', code: 'yak-legacy-file:json-old', path: rel, message: '*.json.old is still ingested by the v40 YAK loader' })
      continue
    }
    if (rel.includes('_Legacy_Commands')) {
      treeIssues.push({ level: 'deprecation', code: 'yak-legacy-file:legacy-commands', path: rel, message: '_Legacy_Commands/ content is still ingested by the v40 YAK loader' })
    }
    if (basename(file).startsWith('temp_norm_')) {
      treeIssues.push({ level: 'deprecation', code: 'yak-legacy-file:temp-norm', path: rel, message: 'temp_norm_* scratch file living in the definition tree' })
    }
    const md5 = createHash('md5').update(readFileSync(file)).digest('hex')
    byMd5.set(md5, [...(byMd5.get(md5) ?? []), rel])
  }
  for (const [, dupes] of byMd5) {
    if (dupes.length > 1) {
      treeIssues.push({
        level: 'deprecation',
        code: 'yak-duplicate-definition',
        path: dupes[0]!,
        message: `byte-identical definition in ${dupes.length} places: ${dupes.join(' | ')}`,
      })
    }
  }
  // duplicate model folders across classes (the two 34401As)
  const modelHomes = new Map<string, string[]>()
  for (const cls of readdirSync(YAK_SUBTREE).sort()) {
    const clsPath = join(YAK_SUBTREE, cls)
    if (!statSync(clsPath).isDirectory()) continue
    for (const model of readdirSync(clsPath).sort()) {
      if (!statSync(join(clsPath, model)).isDirectory()) continue
      const base = parseFolderName(model).base
      if (base && !base.startsWith('_')) {
        modelHomes.set(base, [...(modelHomes.get(base) ?? []), `${cls}/${model}`])
      }
    }
  }
  for (const [model, homes] of modelHomes) {
    if (homes.length > 1) {
      treeIssues.push({
        level: 'error',
        code: 'yak-duplicate-model',
        path: `5_Protocols/10_Yak`,
        message: `model "${model}" defined in ${homes.length} classes: ${homes.join(' | ')}`,
      })
    }
  }
}

function lintConfigInis() {
  const stack = [BACKEND_ROOT]
  while (stack.length) {
    const dir = stack.pop()!
    let entries: string[]
    try {
      entries = readdirSync(dir)
    } catch {
      continue
    }
    for (const e of entries) {
      const p = join(dir, e)
      const st = statSync(p)
      if (st.isDirectory() && e !== 'target' && e !== 'node_modules') stack.push(p)
      else if (e === 'config.ini') {
        const lines = readFileSync(p, 'utf8').split('\n')
        lines.forEach((line, i) => {
          const m = /^\s*(topic[A-Za-z_]*)\s*=\s*(.+?)\s*$/.exec(line)
          if (!m) return
          const value = m[2]!.replace(/\s*[;#].*$/, '')
          const bare = value.replace(/\/[#+]$/, '').replace(/\/$/, '')
          const parsed = Topics.parse(bare)
          if (parsed.kind === 'unknown') {
            treeIssues.push({ level: 'error', code: 'config-ini-topic', path: `${p}:${i + 1}`, message: `${m[1]} = "${value}" does not parse against the topic grammar` })
          } else if (parsed.kind === 'legacy') {
            treeIssues.push({ level: 'deprecation', code: 'config-ini-topic-legacy', path: `${p}:${i + 1}`, message: `${m[1]} = "${value}" targets the ${parsed.family} legacy namespace` })
          }
        })
      }
    }
  }
}

// ------------------------------------------------------------------ main

walkLayoutTree()
walkFolderGrammar(GUI_ROOT)
walkYakTreeRules()
lintConfigInis()

const allIssues = [...reports.flatMap((r) => r.issues.map((i) => ({ ...i, file: r.file }))), ...treeIssues.map((i) => ({ ...i, file: '(tree)' }))]
const errors = allIssues.filter((i) => i.level === 'error')
const deprecations = allIssues.filter((i) => i.level === 'deprecation')

const byCode = new Map<string, number>()
for (const i of allIssues) byCode.set(i.code, (byCode.get(i.code) ?? 0) + 1)
const summary = {
  generatedAt: new Date().toISOString(),
  filesScanned: reports.length,
  totals: { errors: errors.length, deprecations: deprecations.length },
  byCode: Object.fromEntries([...byCode.entries()].sort((a, b) => b[1] - a[1])),
}

if (reportMode === 'json') {
  console.log(JSON.stringify({ summary, files: reports, tree: treeIssues }, null, 2))
} else {
  console.log(`openair-validate — ${GUI_ROOT}`)
  console.log(`  errors: ${errors.length}   deprecations: ${deprecations.length}`)
  console.log('  by code:')
  for (const [code, n] of Object.entries(summary.byCode)) console.log(`    ${String(n).padStart(6)}  ${code}`)
  if (reportMode === 'pretty') {
    console.log('\n  errors (first 40):')
    for (const i of errors.slice(0, 40)) console.log(`    [${(i as { file: string }).file}${i.path}] ${i.code}: ${i.message}`)
  }
}

process.exit(errors.length > 0 || (strict && deprecations.length > 0) ? 1 : 0)
