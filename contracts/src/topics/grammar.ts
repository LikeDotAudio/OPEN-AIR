/**
 * Segment grammar for the OpenAir topic tree (guidelines T4).
 *
 * One rule set, enforced by every builder: explicit charsets, no spaces,
 * no empty segments, no MQTT wildcard/injection characters. The parser
 * rejects — it never guesses.
 */

export const ROOT = 'OpenAir'
export const GUI_ROOT = 'OpenAir/Gui'

/** Plain segment: protocol names, agent names, models, classes. */
const SEGMENT_RE = /^[A-Za-z0-9_-]+$/

/**
 * Device identity (guidelines D2): `{protocol}:{stableKey}`. The stable key
 * may carry VISA-resource characters (`.`, `:`), never `/`, `+`, `#`, spaces.
 */
const DEVICE_ID_RE = /^[a-z0-9]+:[A-Za-z0-9._:-]+$/

/** Capability id (guidelines Y3): dotted path, e.g. `frequency.center`. */
const CAPABILITY_RE = /^[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)*$/

export const YAK_VERBS = ['set', 'rig', 'nab', 'do'] as const
export type YakVerb = (typeof YAK_VERBS)[number]

export const MONITOR_DIRS = ['in', 'out'] as const
export type MonitorDir = (typeof MONITOR_DIRS)[number]

export const LOG_LEVELS = ['trace', 'debug', 'info', 'warn', 'error'] as const
export type LogLevel = (typeof LOG_LEVELS)[number]

export class TopicError extends Error {
  constructor(what: string, value: string) {
    super(`invalid topic ${what}: ${JSON.stringify(value)}`)
    this.name = 'TopicError'
  }
}

export function assertSegment(what: string, value: string): string {
  if (!SEGMENT_RE.test(value)) throw new TopicError(what, value)
  return value
}

export function assertDeviceId(value: string): string {
  if (!DEVICE_ID_RE.test(value)) throw new TopicError('deviceId', value)
  return value
}

export function assertCapability(value: string): string {
  if (!CAPABILITY_RE.test(value)) throw new TopicError('capability', value)
  return value
}

export function isSegment(value: string): boolean {
  return SEGMENT_RE.test(value)
}

export function isDeviceId(value: string): boolean {
  return DEVICE_ID_RE.test(value)
}
