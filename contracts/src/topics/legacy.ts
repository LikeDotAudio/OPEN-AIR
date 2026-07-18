/**
 * The v40 namespace map (guidelines T7): every topic family the current
 * system emits, as a classifier + alias table, so bridges and the validate
 * CLI can *name* old traffic instead of failing on it. New code never builds
 * these; they retire per-agent (VISA in Phase 4, YAK in Phase 3).
 */

export type LegacyFamily =
  /** `OpenAir/System/Protocols/visa/Device/{type}/{model}/Dev{n}/{key}` — field-per-topic explosion (orchestrator main.rs:284) */
  | 'visaDeviceTree'
  /** `OpenAir/System/Protocols/midi/Device/{Input|Output}/Dev{n}/{key}` */
  | 'midiDeviceTree'
  /** `OpenAir/System/Protocols/yak/{pub|sub|ignore|monitor/in|monitor/out}` */
  | 'yakAgent'
  /** `OpenAir/System/Protocols/{proto}` — boot-time retained status string (mqtt.rs:80) */
  | 'protocolStatus'
  /** `OpenAir/System/Protocols/{proto}/config` — orchestrator-side config channel (mqtt.rs:90) */
  | 'protocolConfig'
  /** `OpenAir/System/Failover/WEB/Heartbeat/{guid}` — browser 1 Hz beat, no LWT (MqttProvider.jsx:77) */
  | 'failoverWebHeartbeat'
  /** `OpenAir/Protocol/{MidiIn|GuiOsc|AES70}/...` — the /ws SystemState side-bus; never on MQTT (guidelines finding #5) */
  | 'wsSideBus'

export interface LegacyParsed {
  kind: 'legacy'
  family: LegacyFamily
  /** family-specific detail — see per-family docs above */
  protocol?: string
  channel?: string
  guid?: string
  segments?: string[]
}

/** Where each v40 family lands in the v41 tree (Phase 1 §3.1 migration map). */
export const V40_ALIASES: Record<LegacyFamily, string> = {
  visaDeviceTree: 'OpenAir/Discovery/visa/{deviceId} (one DeviceRecord doc)',
  midiDeviceTree: 'OpenAir/Discovery/midi/{deviceId} (one DeviceRecord doc)',
  yakAgent: 'OpenAir/Yak/{cmd|monitor}/...',
  protocolStatus: 'OpenAir/System/Agents/{agent} (AgentHeartbeat doc)',
  protocolConfig: 'OpenAir/System/Config/{agent}',
  failoverWebHeartbeat: 'OpenAir/System/Agents/web-{guid} (AgentHeartbeat doc)',
  wsSideBus: 'OpenAir/{Discovery|Gui|System}/... per role (side-bus retires)',
}

/** Classify segments already known to start with `OpenAir`. Returns null when not legacy. */
export function classifyLegacy(segs: string[]): LegacyParsed | null {
  const [, s1, s2, s3, ...rest] = segs
  if (s1 === 'Protocol' && s2 !== undefined) {
    return { kind: 'legacy', family: 'wsSideBus', channel: s2, segments: [...(s3 !== undefined ? [s3] : []), ...rest] }
  }
  if (s1 !== 'System') return null
  if (s2 === 'Failover' && s3 === 'WEB' && rest[0] === 'Heartbeat' && rest.length === 2 && rest[1] !== undefined) {
    return { kind: 'legacy', family: 'failoverWebHeartbeat', guid: rest[1] }
  }
  if (s2 !== 'Protocols' || s3 === undefined) return null
  if (s3 === 'visa' && rest[0] === 'Device') {
    return { kind: 'legacy', family: 'visaDeviceTree', segments: rest.slice(1) }
  }
  if (s3 === 'midi' && rest[0] === 'Device') {
    return { kind: 'legacy', family: 'midiDeviceTree', segments: rest.slice(1) }
  }
  if (s3 === 'yak') {
    return { kind: 'legacy', family: 'yakAgent', channel: rest.join('/') }
  }
  if (rest.length === 0) return { kind: 'legacy', family: 'protocolStatus', protocol: s3 }
  if (rest.length === 1 && rest[0] === 'config') {
    return { kind: 'legacy', family: 'protocolConfig', protocol: s3 }
  }
  if (rest.length === 1 && rest[0] === 'status') {
    return { kind: 'legacy', family: 'protocolStatus', protocol: s3 }
  }
  return null
}
