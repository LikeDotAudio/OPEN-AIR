/**
 * The declared v41 topic tree (guidelines T1): every family as data —
 * pattern, retain class, payload, roles. This table IS the namespace
 * documentation, and T5 hangs off it: retain policy belongs to the family,
 * never to the publish call-site.
 */

export type RetainClass = 'retained-state' | 'live-event'

export interface TopicFamily {
  pattern: string
  retain: RetainClass
  /** contracts schema name of the payload, once it lands ('-' = free-form during transition) */
  payload: string
  producer: string
  consumers: string[]
}

export const TOPIC_FAMILIES = {
  discovery: {
    pattern: 'OpenAir/Discovery/{protocol}/{deviceId}',
    retain: 'retained-state',
    payload: 'DeviceRecord',
    producer: 'device-registry (Phase 4)',
    consumers: ['discovered-tab'],
  },
  gui: {
    pattern: 'OpenAir/Gui/{...panelPath}/{field}',
    retain: 'live-event',
    payload: 'Envelope',
    producer: 'browser widgets',
    consumers: ['browser widgets', 'yak-agent'],
  },
  yakCmd: {
    pattern: 'OpenAir/Yak/cmd/{verb}/{deviceClass}/{model}',
    retain: 'live-event',
    payload: 'YakHandlerMsg (Phase 3)',
    producer: 'browser widgets',
    consumers: ['yak-agent'],
  },
  yakState: {
    pattern: 'OpenAir/Yak/state/{deviceClass}/{model}/{capability}',
    retain: 'retained-state',
    payload: 'YakStateDoc (Phase 3)',
    producer: 'yak-agent',
    consumers: ['browser widgets'],
  },
  yakMonitor: {
    pattern: 'OpenAir/Yak/monitor/{in|out}',
    retain: 'live-event',
    payload: '-',
    producer: 'yak-agent',
    consumers: ['CommandRouter'],
  },
  tests: {
    // live-event, not retained: the family mixes setpoints with one-shot
    // commands (JumpCommand, RunSequence, TriggerSweep), and a retained command
    // re-fires the test on every reconnect. State is re-emitted by execute_step.
    pattern: 'OpenAir/Tests/{suite}/{...path}',
    retain: 'live-event',
    payload: '-',
    producer: 'test-orchestrator + browser widgets',
    consumers: ['test-orchestrator', '2_Tests panels'],
  },
  agents: {
    pattern: 'OpenAir/System/Agents/{agent}',
    retain: 'retained-state',
    payload: 'AgentHeartbeat',
    producer: 'every agent + browser sessions',
    consumers: ['system-panels', 'supervisor'],
  },
  config: {
    pattern: 'OpenAir/System/Config/{agent}',
    retain: 'retained-state',
    payload: '-',
    producer: 'orchestrator',
    consumers: ['agents', 'ProtocolConfigDisplay'],
  },
  log: {
    pattern: 'OpenAir/System/Log/{source}/{level}',
    retain: 'live-event',
    payload: 'LogEvent',
    producer: 'every agent',
    consumers: ['system console (Phase 4)'],
  },
} as const satisfies Record<string, TopicFamily>

export type FamilyKind = keyof typeof TOPIC_FAMILIES

/** T5: the MQTT layer reads the retain flag from here, not from call-sites. */
export function retainClassOf(kind: FamilyKind): RetainClass {
  return TOPIC_FAMILIES[kind].retain
}
