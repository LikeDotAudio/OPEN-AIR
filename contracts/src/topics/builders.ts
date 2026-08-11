/**
 * Typed build + parse for the whole namespace (guidelines T2: no string
 * concatenation outside contracts). Builders throw `TopicError` on any
 * segment that violates the grammar; `parse` is a total function returning
 * a discriminated union — it classifies legacy traffic by name and returns
 * `{ kind: 'unknown' }` rather than guessing.
 */

import {
  GUI_ROOT,
  LOG_LEVELS,
  MONITOR_DIRS,
  ROOT,
  TopicError,
  YAK_VERBS,
  assertCapability,
  assertDeviceId,
  assertSegment,
  isDeviceId,
  isSegment,
  type LogLevel,
  type MonitorDir,
  type YakVerb,
} from './grammar.js'
import { guiPrefixFromPanelPath, guiSegmentsFromPanelPath } from './gui-path.js'
import { classifyLegacy, type LegacyParsed } from './legacy.js'

export type ParsedTopic =
  | { kind: 'discovery'; protocol: string; deviceId: string }
  | { kind: 'gui'; segments: string[] }
  | { kind: 'yakCmd'; verb: YakVerb; deviceClass: string; model: string }
  | { kind: 'yakState'; deviceClass: string; model: string; capability: string }
  | { kind: 'yakMonitor'; dir: MonitorDir }
  | { kind: 'tests'; suite: string; path: string[] }
  | { kind: 'agents'; agent: string }
  | { kind: 'config'; agent: string }
  | { kind: 'log'; source: string; level: LogLevel }
  | LegacyParsed
  | { kind: 'unknown'; raw: string }

export const Topics = {
  discovery(args: { protocol: string; deviceId: string }): string {
    return `${ROOT}/Discovery/${assertSegment('protocol', args.protocol)}/${assertDeviceId(args.deviceId)}`
  },
  discoveryWildcard(protocol?: string): string {
    return protocol === undefined
      ? `${ROOT}/Discovery/#`
      : `${ROOT}/Discovery/${assertSegment('protocol', protocol)}/+`
  },

  gui: {
    ROOT: GUI_ROOT,
    wildcard(): string {
      return `${GUI_ROOT}/#`
    },
    /** Canonized topicMaker.jsx semantics — see gui-path.ts. */
    fromPanelPath: guiPrefixFromPanelPath,
    segmentsFromPanelPath: guiSegmentsFromPanelPath,
  },

  yak: {
    cmd(args: { verb: YakVerb; deviceClass: string; model: string }): string {
      if (!YAK_VERBS.includes(args.verb)) throw rangeError('verb', args.verb)
      return `${ROOT}/Yak/cmd/${args.verb}/${assertSegment('deviceClass', args.deviceClass)}/${assertSegment('model', args.model)}`
    },
    state(args: { deviceClass: string; model: string; capability: string }): string {
      return `${ROOT}/Yak/state/${assertSegment('deviceClass', args.deviceClass)}/${assertSegment('model', args.model)}/${assertCapability(args.capability)}`
    },
    monitor(dir: MonitorDir): string {
      if (!MONITOR_DIRS.includes(dir)) throw rangeError('monitor dir', dir)
      return `${ROOT}/Yak/monitor/${dir}`
    },
  },

  /**
   * Test-suite bus. Each `mod.rs` under BackEnd/Core/TestOrchestrator owns one
   * `{suite}` via `topic_prefix()`; the panels under FrontEnd/Gui_Frames/2_Tests bind
   * to leaves below it. The suite name is NOT an enum here on purpose — a new
   * orchestrator module is the thing that mints one.
   */
  tests: {
    prefix(suite: string): string {
      return `${ROOT}/Tests/${assertSegment('suite', suite)}`
    },
    topic(args: { suite: string; path: string[] }): string {
      const segs = args.path.map((s) => assertSegment('path segment', s))
      return [Topics.tests.prefix(args.suite), ...segs].join('/')
    },
    wildcard(suite?: string): string {
      return suite === undefined ? `${ROOT}/Tests/#` : `${Topics.tests.prefix(suite)}/#`
    },
  },

  agents: {
    topic(agent: string): string {
      return `${ROOT}/System/Agents/${assertSegment('agent', agent)}`
    },
    wildcard(): string {
      return `${ROOT}/System/Agents/+`
    },
  },

  config(agent: string): string {
    return `${ROOT}/System/Config/${assertSegment('agent', agent)}`
  },

  log(args: { source: string; level: LogLevel }): string {
    if (!LOG_LEVELS.includes(args.level)) throw rangeError('log level', args.level)
    return `${ROOT}/System/Log/${assertSegment('source', args.source)}/${args.level}`
  },

  parse(raw: string): ParsedTopic {
    const segs = raw.split('/')
    const unknown = { kind: 'unknown', raw } as const
    if (segs[0] !== ROOT || segs.some((s) => s === '')) return unknown

    const legacy = classifyLegacy(segs)
    if (legacy) return legacy

    const [, s1, s2, s3, s4, s5, ...over] = segs
    switch (s1) {
      case 'Discovery':
        if (s2 !== undefined && s3 !== undefined && s4 === undefined && isSegment(s2) && isDeviceId(s3)) {
          return { kind: 'discovery', protocol: s2, deviceId: s3 }
        }
        return unknown
      case 'Gui':
        return { kind: 'gui', segments: segs.slice(2) }
      case 'Yak':
        if (s2 === 'monitor' && s3 !== undefined && s4 === undefined && isMonitorDir(s3)) {
          return { kind: 'yakMonitor', dir: s3 }
        }
        if (s2 === 'cmd' && s3 !== undefined && s4 !== undefined && s5 !== undefined && over.length === 0 && isYakVerb(s3) && isSegment(s4) && isSegment(s5)) {
          return { kind: 'yakCmd', verb: s3, deviceClass: s4, model: s5 }
        }
        if (s2 === 'state' && s3 !== undefined && s4 !== undefined && s5 !== undefined && over.length === 0 && isSegment(s3) && isSegment(s4)) {
          return { kind: 'yakState', deviceClass: s3, model: s4, capability: s5 }
        }
        return unknown
      case 'Tests':
        // `OpenAir/Tests/{suite}` alone is the orchestrator's prefix and parses
        // with an empty path; everything below it is suite-private structure.
        if (s2 !== undefined && isSegment(s2) && segs.slice(3).every(isSegment)) {
          return { kind: 'tests', suite: s2, path: segs.slice(3) }
        }
        return unknown
      case 'System':
        if (s2 === 'Agents' && s3 !== undefined && s4 === undefined && isSegment(s3)) {
          return { kind: 'agents', agent: s3 }
        }
        if (s2 === 'Config' && s3 !== undefined && s4 === undefined && isSegment(s3)) {
          return { kind: 'config', agent: s3 }
        }
        if (s2 === 'Log' && s3 !== undefined && s4 !== undefined && s5 === undefined && isSegment(s3) && isLogLevel(s4)) {
          return { kind: 'log', source: s3, level: s4 }
        }
        return unknown
      default:
        return unknown
    }
  },

  isLegacy(raw: string): boolean {
    return Topics.parse(raw).kind === 'legacy'
  },
} as const

function rangeError(what: string, value: string): Error {
  return new TopicError(what, value)
}

function isYakVerb(s: string): s is YakVerb {
  return (YAK_VERBS as readonly string[]).includes(s)
}
function isMonitorDir(s: string): s is MonitorDir {
  return (MONITOR_DIRS as readonly string[]).includes(s)
}
function isLogLevel(s: string): s is LogLevel {
  return (LOG_LEVELS as readonly string[]).includes(s)
}
