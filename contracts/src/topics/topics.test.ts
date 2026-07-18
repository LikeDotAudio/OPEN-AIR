/**
 * Vector-driven suite: every case comes from ../../vectors/topics.json, the
 * language-neutral contract shared with contracts/rust. Add cases THERE, not
 * here — a vector added on one side fails the other side's CI until
 * implemented.
 */
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

import { describe, expect, it } from 'vitest'

import { Topics } from './builders.js'
import { guiPrefixFromPanelPath } from './gui-path.js'

interface BuildVector {
  family: string
  args: Record<string, string>
  topic?: string
  why?: string
}
interface ParseVector {
  topic: string
  parsed: Record<string, unknown>
}
interface GuiVector {
  filePath: string
  topic: string
}
interface Vectors {
  build: BuildVector[]
  buildInvalid: BuildVector[]
  parse: ParseVector[]
  guiFromPanelPath: GuiVector[]
}

const vectorsPath = join(dirname(fileURLToPath(import.meta.url)), '../../vectors/topics.json')
const vectors = JSON.parse(readFileSync(vectorsPath, 'utf8')) as Vectors

function build(family: string, args: Record<string, string>): string {
  switch (family) {
    case 'discovery':
      return Topics.discovery(args as { protocol: string; deviceId: string })
    case 'discoveryWildcard':
      return Topics.discoveryWildcard(args['protocol'])
    case 'guiWildcard':
      return Topics.gui.wildcard()
    case 'yakCmd':
      return Topics.yak.cmd(args as Parameters<typeof Topics.yak.cmd>[0])
    case 'yakState':
      return Topics.yak.state(args as Parameters<typeof Topics.yak.state>[0])
    case 'yakMonitor':
      return Topics.yak.monitor(args['dir'] as Parameters<typeof Topics.yak.monitor>[0])
    case 'agents':
      return Topics.agents.topic(args['agent'] as string)
    case 'agentsWildcard':
      return Topics.agents.wildcard()
    case 'config':
      return Topics.config(args['agent'] as string)
    case 'log':
      return Topics.log(args as Parameters<typeof Topics.log>[0])
    default:
      throw new Error(`vector family not implemented in TS: ${family}`)
  }
}

describe('topic vectors — build', () => {
  it.each(vectors.build)('$family → $topic', (v) => {
    expect(build(v.family, v.args)).toBe(v.topic)
  })
})

describe('topic vectors — build rejects grammar violations', () => {
  it.each(vectors.buildInvalid)('$family: $why', (v) => {
    expect(() => build(v.family, v.args)).toThrow()
  })
})

describe('topic vectors — parse', () => {
  it.each(vectors.parse)('$topic', (v) => {
    expect(Topics.parse(v.topic)).toEqual(v.parsed)
  })
})

describe('topic vectors — guiFromPanelPath (canonized topicMaker.jsx semantics)', () => {
  it.each(vectors.guiFromPanelPath)('$filePath → $topic', (v) => {
    expect(guiPrefixFromPanelPath(v.filePath)).toBe(v.topic)
  })
})

describe('isLegacy', () => {
  it('classifies every legacy parse vector as legacy, and nothing else', () => {
    for (const v of vectors.parse) {
      expect(Topics.isLegacy(v.topic)).toBe(v.parsed['kind'] === 'legacy')
    }
  })
})
