/**
 * Folder grammar — guidelines L4. The filesystem IS parsed syntax:
 * `N_` prefixes order tabs, `left_50`-style names split panes
 * (WindowManager.jsx:12-16), geometry folders are dropped from topics
 * (topicMaker.jsx / topics/gui-path.ts). This file makes those rules a
 * contract surface the tab engine, the editor save path, and the validate
 * CLI all share.
 */

export interface ParsedFolderName {
  raw: string
  /** numeric ordering prefix, when present (`0_Spectrum` → 0) */
  order?: number
  /** name with the ordering prefix stripped */
  base: string
  /** split-pane folders: `left_50` → { direction:'left', percent:50 } */
  split?: { direction: 'left' | 'right' | 'top' | 'bottom'; percent: number }
  /** window/screen-geometry folder — dropped from topic derivation */
  geometry: boolean
}

const SPLIT_RE = /^(left|right|top|bottom)_(\d+)$/i
const GEOMETRY_TOKENS = new Set(['display', 'window', 'left', 'right', 'top', 'bottom'])

export function parseFolderName(raw: string): ParsedFolderName {
  const split = SPLIT_RE.exec(raw)
  const orderMatch = /^(\d+)[_-]?/.exec(raw)
  const base = raw.replace(/^\d+[_-]?/, '')
  const geomBase = base.replace(/[_-]?\d+$/, '').toLowerCase()
  const parsed: ParsedFolderName = {
    raw,
    base,
    geometry: GEOMETRY_TOKENS.has(geomBase) || /^\d+$/.test(raw),
  }
  if (orderMatch?.[1] !== undefined && !/^\d+$/.test(raw)) parsed.order = parseInt(orderMatch[1], 10)
  if (split) {
    parsed.split = {
      direction: split[1]!.toLowerCase() as 'left' | 'right' | 'top' | 'bottom',
      percent: parseInt(split[2]!, 10),
    }
  }
  return parsed
}

export interface FolderCollision {
  order: number
  names: string[]
}

/**
 * The `4_DMM_YAK` vs `4_Load_YAK` disease: two sibling folders claiming the
 * same ordering prefix. The loader derives identity from these names, so a
 * collision is ambiguity, not style.
 */
export function findOrderCollisions(siblingNames: string[]): FolderCollision[] {
  const byOrder = new Map<number, string[]>()
  for (const name of siblingNames) {
    const p = parseFolderName(name)
    if (p.order !== undefined && !p.geometry && p.base) {
      byOrder.set(p.order, [...(byOrder.get(p.order) ?? []), name])
    }
  }
  return [...byOrder.entries()]
    .filter(([, names]) => names.length > 1)
    .map(([order, names]) => ({ order, names }))
}
