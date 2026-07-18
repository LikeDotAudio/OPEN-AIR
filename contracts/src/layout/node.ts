/**
 * Layout document validation — guidelines L1/L2/L5. Two modes in one walker:
 * every finding is an issue with a level; `strict` mode treats deprecations
 * as failures (the Phase 2 editor save-gate), `legacy` mode (the CLI default)
 * reports them BY NAME — the day-one counts ARE the technical-debt inventory.
 *
 * The walker is deliberately tolerant-reader shaped: unknown keys are fine
 * (that is policy), only *known-legacy* and *known-dead* keys are flagged,
 * plus structural errors the renderer would trip on.
 */
import { Topics } from '../topics/builders.js'
import { classifyWidgetType } from './widget-types.js'
import { YakBindingSchema, lintYakBinding } from './yak-binding.js'

export type LayoutIssueLevel = 'error' | 'deprecation'

export interface LayoutIssue {
  level: LayoutIssueLevel
  /** stable machine code — the ratchet baseline keys on (file, code, path) */
  code: string
  /** JSON-pointer-ish location inside the document */
  path: string
  message: string
}

/** v40 flat keys the renderer only accepts via compatibility shims (FieldComponent.jsx:16-66). */
const LEGACY_FLAT_KEYS = ['min', 'max', 'value_default', 'units', 'step', 'label_active', 'label_inactive'] as const

/** Keys NOTHING reads — errors even in legacy mode (guidelines L2). */
const DEAD_KEYS = ['subscribe', 'widget_type'] as const

const TOPIC_OVERRIDE_KEYS = ['topic', 'shared_topic'] as const

function isPlainObject(v: unknown): v is Record<string, unknown> {
  return typeof v === 'object' && v !== null && !Array.isArray(v)
}

/**
 * Validate one parsed panel document. Returns every issue found; empty array
 * means strict-valid. Root shape rule (LoaderOrchestrator.jsx:45): a document
 * is EITHER a single node (root has string `type`) or a map of named nodes.
 */
export function validateLayoutDocument(doc: unknown): LayoutIssue[] {
  const issues: LayoutIssue[] = []
  if (!isPlainObject(doc)) {
    issues.push({ level: 'error', code: 'root-not-object', path: '', message: 'document root must be an object' })
    return issues
  }
  if (typeof doc['type'] === 'string') {
    walkNode(doc, '', issues)
  } else {
    for (const [key, node] of Object.entries(doc)) {
      if (isPlainObject(node)) walkNode(node, `/${key}`, issues)
      else if (key !== '$comment') {
        issues.push({ level: 'error', code: 'root-entry-not-node', path: `/${key}`, message: 'top-level entry is not a node object' })
      }
    }
  }
  return issues
}

function walkNode(node: Record<string, unknown>, path: string, issues: LayoutIssue[]): void {
  const type = node['type']
  // Every per-node check is gated on the node being a WIDGET node (string
  // `type`): pillar sub-objects like domain/{min,max} are the accepted nested
  // form, not legacy flat keys, and must not be re-flagged during descent.
  if (typeof type === 'string') {
    switch (classifyWidgetType(type)) {
      case 'legacy':
        issues.push({ level: 'deprecation', code: 'legacy-widget-type', path, message: `legacy widget type "${type}" (v0 discovered-frame schema)` })
        break
      case 'data-model':
        issues.push({ level: 'deprecation', code: 'data-model-type', path, message: `data-model type "${type}" living in the panel tree — needs a data-set schema or relocation` })
        break
      case 'unknown':
        issues.push({ level: 'error', code: 'unknown-widget-type', path, message: `unknown widget type "${type}" — renders as the dashed fallback box` })
        break
      default:
        break
    }

    for (const key of LEGACY_FLAT_KEYS) {
      if (key in node) {
        issues.push({ level: 'deprecation', code: `legacy-flat-key:${key}`, path, message: `flat "${key}" — v41 shape nests it under domain/value/label pillars` })
      }
    }
    for (const key of DEAD_KEYS) {
      if (key in node) {
        issues.push({ level: 'error', code: `dead-key:${key}`, path, message: `"${key}" is read by nothing — remove it` })
      }
    }

    // Old third-generation label form from build_discovered_gui.py. NOTE:
    // plain `label:{En:...}` is a legitimate CURRENT form for group titles
    // (FieldComponent.jsx: "without disturbing a plain `label` group title"),
    // so this only fires on the legacy widget generation, where it marks the
    // discovered-frame schema.
    const label = node['label']
    if (
      classifyWidgetType(type) === 'legacy' &&
      isPlainObject(label) && !('active' in label) && !('inactive' in label) && ('En' in label)
    ) {
      issues.push({ level: 'deprecation', code: 'legacy-label-form', path: `${path}/label`, message: 'label:{En:...} on a legacy widget — v41 uses label.active/.inactive pillars' })
    }

    // L5: explicit topic overrides must parse against the grammar.
    for (const key of TOPIC_OVERRIDE_KEYS) {
      const t = node[key]
      if (typeof t === 'string' && t !== '') {
        const parsed = Topics.parse(t)
        if (parsed.kind === 'unknown') {
          issues.push({ level: 'error', code: 'invalid-topic-override', path: `${path}/${key}`, message: `"${t}" does not parse against the topic grammar` })
        } else if (parsed.kind === 'legacy') {
          issues.push({ level: 'deprecation', code: 'legacy-topic-override', path: `${path}/${key}`, message: `"${t}" targets the ${parsed.family} legacy namespace` })
        }
      }
    }

    // L3: the binding block, schema + lints.
    const yak = node['yak_handler']
    if (isPlainObject(yak)) {
      const res = YakBindingSchema.safeParse(yak)
      if (!res.success) {
        for (const issue of res.error.issues) {
          issues.push({ level: 'error', code: 'yak-binding-invalid', path: `${path}/yak_handler/${issue.path.join('/')}`, message: issue.message })
        }
      }
      for (const note of lintYakBinding(yak)) {
        issues.push({ level: 'deprecation', code: 'yak-binding-lint', path: `${path}/yak_handler`, message: note })
      }
    }
  }

  // Recurse — containers keep children under blocks/fields/tabs/panels maps,
  // but the renderer walks whatever it finds, so we do too.
  for (const [key, value] of Object.entries(node)) {
    if (key === 'yak_handler') continue
    if (isPlainObject(value)) {
      // only descend into subtrees that can contain nodes
      walkNode(value, `${path}/${key}`, issues)
    } else if (Array.isArray(value)) {
      value.forEach((item, i) => {
        if (isPlainObject(item)) walkNode(item, `${path}/${key}[${i}]`, issues)
      })
    }
  }
}

/** Phase 2 editor save-gate: strict mode — no errors AND no deprecations. */
export function isStrictValid(doc: unknown): boolean {
  return validateLayoutDocument(doc).length === 0
}
