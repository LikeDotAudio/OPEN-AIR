/**
 * DeviceRecord — guidelines D1–D5. ONE JSON document per device, retained at
 * `OpenAir/Discovery/{protocol}/{deviceId}`, replacing v40's
 * field-per-retained-topic explosion (orchestrator main.rs:297-304).
 * Liveness is `lastSeen` plus documented TTL semantics (D4): the registry
 * (Phase 4) marks `stale` after 3 missed refresh windows, `removed` after
 * 10. Boolean liveness flags that go stale themselves (`connected: 0|1`)
 * are banned.
 */
import { z } from 'zod'

import { deviceIdFor } from './identity.js'
import { fromUnixSeconds } from './time.js'

export const DeviceStatusSchema = z.enum(['discovered', 'identified', 'unresponsive', 'stale', 'removed'])
export type DeviceStatus = z.infer<typeof DeviceStatusSchema>

/** D1: per-protocol specifics live HERE, never in the core field set. */
export const DeviceExtraSchema = z.object({
  visa: z.object({ resource: z.string() }).optional(),
  midi: z
    .object({ direction: z.enum(['input', 'output']), portIndex: z.number().int() })
    .optional(),
})
export type DeviceExtra = z.infer<typeof DeviceExtraSchema>

export const DeviceRecordSchema = z
  .object({
    schemaVersion: z.literal(1),
    protocol: z.string().regex(/^[A-Za-z0-9_-]+$/),
    deviceId: z.string().regex(/^[a-z0-9]+:[A-Za-z0-9._:-]+$/),
    deviceClass: z.string(),
    make: z.string(),
    model: z.string(),
    serial: z.string().optional(),
    firmware: z.string().optional(),
    address: z.string(),
    rawIdn: z.string().optional(),
    status: DeviceStatusSchema,
    firstSeen: z.iso.datetime(),
    lastSeen: z.iso.datetime(),
    notes: z.string().optional(),
    extra: DeviceExtraSchema.optional(),
  })
  .describe('DeviceRecord: the canonical discovered-device document in OPEN-AIR.')
export type DeviceRecord = z.infer<typeof DeviceRecordSchema>

/**
 * v0: the VISA agent's merge object (orchestrator main.rs:267-295) — what the
 * exploded per-field topics reassemble to. Schema'd for extraction.
 */
export const LegacyVisaRecordV0Schema = z.object({
  manufacturer: z.string(),
  model: z.string(),
  serial: z.string(),
  firmware: z.string(),
  raw_idn: z.string(),
  resource: z.string(),
  status: z.enum(['found', 'identified']),
  device_type: z.string(),
  notes: z.string(),
  last_online: z.number(),
  connected: z.union([z.literal(0), z.literal(1)]),
})
export type LegacyVisaRecordV0 = z.infer<typeof LegacyVisaRecordV0Schema>

/**
 * The step-3e replay proof: today's VISA fields map losslessly into a valid
 * DeviceRecord. `Dev{n}` scan-order identity is deliberately DISCARDED in
 * favor of the D2 derivation. Status rule: `found` → `discovered`;
 * `identified` + `connected:1` → `identified`; `identified` + `connected:0`
 * → `unresponsive`. Empty-string optionals are omitted, not carried.
 */
export function mapV40VisaRecord(v0: LegacyVisaRecordV0): DeviceRecord {
  const lastSeen = fromUnixSeconds(v0.last_online)
  const status: DeviceStatus =
    v0.status === 'found' ? 'discovered' : v0.connected === 1 ? 'identified' : 'unresponsive'
  const record: DeviceRecord = {
    schemaVersion: 1,
    protocol: 'visa',
    deviceId: deviceIdFor({
      protocol: 'visa',
      serial: v0.serial,
      address: v0.resource,
      make: v0.manufacturer,
      model: v0.model,
    }),
    deviceClass: v0.device_type,
    make: v0.manufacturer,
    model: v0.model,
    ...(v0.serial !== '' ? { serial: v0.serial } : {}),
    ...(v0.firmware !== '' ? { firmware: v0.firmware } : {}),
    address: v0.resource,
    ...(v0.raw_idn !== '' ? { rawIdn: v0.raw_idn } : {}),
    status,
    firstSeen: lastSeen,
    lastSeen,
    ...(v0.notes !== '' ? { notes: v0.notes } : {}),
    extra: { visa: { resource: v0.resource } },
  }
  return DeviceRecordSchema.parse(record)
}
