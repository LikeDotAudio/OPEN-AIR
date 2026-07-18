/**
 * Panel path → GUI topic derivation — the canonized semantics of
 * `FrontEnd/comMQTT/topicMaker.jsx` (`buildGuiPrefix`), which is the variant
 * the YAK agent's expectations match (Phase 1 §3.2). `topicMaker.jsx` remains
 * the runtime copy until Phase 2 converts it; the vector suite pins the two
 * implementations together. `topicUtils.js` (the older, disagreeing variant)
 * is deleted in the same commit that lands this file.
 *
 *   /Window_1/left_50/top_100/0_Spectrum/10_YAK/1_N9340B/0_Frequency/yak_frequency.json
 *     → "OpenAir/Gui/Spectrum/YAK/N9340B/Frequency"
 *
 * Rules: `N_` ordering prefixes stripped; window/geometry folders (Window_n,
 * left/right/top/bottom/display) dropped; pure-numeric folders dropped;
 * trailing numbers on device folders (Channel_1) PRESERVED; spaces → `_`.
 */

import { GUI_ROOT } from './grammar.js'

const SKIP_TOKENS = new Set(['display', 'window', 'left', 'right', 'top', 'bottom'])

// WHY the oagui→GUI mapping survives: guidelines T4 flags it as a bug to
// outlaw, but step 2 pins today's behavior verbatim — panels depend on it
// until the validate CLI (step 4+) drives the rename through Gui_Frames.
function normalizePart(rawPart: string): string {
  if (!rawPart) return ''
  if (rawPart.toLowerCase() === 'oagui') return 'GUI'
  if (/^\d+$/.test(rawPart)) return ''
  const clean = rawPart.replace(/^\d+[_-]?/, '')
  const base = clean.replace(/[_-]?\d+$/, '').toLowerCase()
  if (!clean || SKIP_TOKENS.has(base)) return ''
  return clean.replace(/\s+/g, '_')
}

/** Folder path (trailing filename optional) → cleaned topic segments. */
export function guiSegmentsFromPanelPath(filePath: string): string[] {
  if (!filePath || typeof filePath !== 'string') return []
  let parts = filePath.split('/').filter(Boolean)
  const last = parts[parts.length - 1]
  if (last !== undefined && /\.[a-z0-9]+$/i.test(last)) {
    parts = parts.slice(0, -1)
  }
  return parts.map(normalizePart).filter(Boolean)
}

/** Full GUI prefix, or the bare root when no usable folder path exists. */
export function guiPrefixFromPanelPath(filePath: string): string {
  const segs = guiSegmentsFromPanelPath(filePath)
  return segs.length ? `${GUI_ROOT}/${segs.join('/')}` : GUI_ROOT
}
