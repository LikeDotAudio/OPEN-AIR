/**
 * AgentHeartbeat — guidelines H1/H2/H3. One liveness shape for every agent
 * AND every browser session (`agent: "web-{guid}"`), retained at
 * `OpenAir/System/Agents/{agent}`. The LWT helper is part of the contract:
 * a heartbeat without a registered will is how today's `active:true` ghost
 * happens (MqttProvider.jsx:53-63 registers none).
 */
import { z } from 'zod'

import { Topics } from './topics/builders.js'

export const AgentStatusSchema = z.enum(['starting', 'online', 'degraded', 'stub', 'stopping', 'offline'])
export type AgentStatus = z.infer<typeof AgentStatusSchema>

export const AgentHeartbeatSchema = z
  .object({
    schemaVersion: z.literal(1),
    agent: z.string().regex(/^[A-Za-z0-9_-]+$/),
    status: AgentStatusSchema,
    version: z.string().optional(),
    startedAt: z.iso.datetime(),
    lastBeat: z.iso.datetime(),
    /** browser-failover field — web sessions only (H1) */
    partition: z.string().optional(),
    host: z.string().optional(),
    pid: z.number().int().optional(),
  })
  .describe('AgentHeartbeat: retained liveness document for one agent or browser session.')
export type AgentHeartbeat = z.infer<typeof AgentHeartbeatSchema>

/**
 * H2 — the exact Last Will every connecting agent (and browser) registers.
 * `startedAt`/`lastBeat` are fixed at connect time; a delivered LWT means
 * "died no later than keepalive after lastBeat".
 */
export function heartbeatLwt(
  agent: string,
  connectedAtIso: string,
  partition?: string,
): { topic: string; payload: AgentHeartbeat } {
  const payload: AgentHeartbeat = {
    schemaVersion: 1,
    agent,
    status: 'offline',
    startedAt: connectedAtIso,
    lastBeat: connectedAtIso,
    ...(partition !== undefined ? { partition } : {}),
  }
  return { topic: Topics.agents.topic(agent), payload: AgentHeartbeatSchema.parse(payload) }
}

/**
 * v0 (the wild west): today's browser Failover payload
 * (MqttProvider.jsx:85-93) — schema'd so validators can NAME what they find
 * on the bus instead of just failing (Phase 1 §2.1). Never emitted by new
 * code; retires with the Failover channel in Phase 2.
 */
export const LegacyFailoverHeartbeatV0Schema = z
  .object({
    guid: z.string(),
    full_id: z.string(),
    partition: z.string(),
    active: z.boolean(),
    start_ts: z.number(),
    timestamp: z.number(),
  })
  .describe('v0 browser Failover heartbeat as emitted by MqttProvider.jsx today.')
export type LegacyFailoverHeartbeatV0 = z.infer<typeof LegacyFailoverHeartbeatV0Schema>
