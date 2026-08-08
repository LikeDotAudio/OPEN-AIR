/**
 * Payload-vector suite (step 3a/3e). Cases live in vectors/payloads/ and
 * vectors/identity.json — shared with contracts/rust. Add cases THERE.
 */
import { readFileSync, readdirSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

import { describe, expect, it } from 'vitest'
import type { z } from 'zod'

import {
  DeviceRecordSchema,
  LegacyVisaRecordV0Schema,
  mapV40VisaRecord,
} from './device-record.js'
import {
  ControlValueSchema,
  LegacyControlValueV0Schema,
  controlIdentity,
  convertUnit,
  mapLegacyControlValue,
} from './control-value.js'
import { AgentHeartbeatSchema, LegacyFailoverHeartbeatV0Schema } from './heartbeat.js'
import { deviceIdFor, fnv1a64 } from './identity.js'
import { fromUnixSeconds } from './time.js'

const VECTORS_DIR = join(dirname(fileURLToPath(import.meta.url)), '../vectors')

function docsIn(rel: string): Array<{ name: string; doc: unknown }> {
  const dir = join(VECTORS_DIR, 'payloads', rel)
  return readdirSync(dir)
    .filter((f) => f.endsWith('.json'))
    .map((f) => ({ name: `${rel}/${f}`, doc: JSON.parse(readFileSync(join(dir, f), 'utf8')) }))
}

function suite(schemaName: string, v1: z.ZodType, legacy: z.ZodType) {
  describe(`${schemaName} payload vectors`, () => {
    it.each(docsIn(`${schemaName}/valid`))('valid: $name', ({ doc }) => {
      expect(v1.safeParse(doc).success).toBe(true)
    })
    it.each(docsIn(`${schemaName}/invalid`))('invalid: $name', ({ doc }) => {
      expect(v1.safeParse(doc).success).toBe(false)
    })
    it.each(docsIn(`${schemaName}/legacy-v0`))('legacy v0 named, not v1: $name', ({ doc }) => {
      expect(legacy.safeParse(doc).success).toBe(true)
      expect(v1.safeParse(doc).success).toBe(false)
    })
  })
}

suite('AgentHeartbeat', AgentHeartbeatSchema, LegacyFailoverHeartbeatV0Schema)
suite('DeviceRecord', DeviceRecordSchema, LegacyVisaRecordV0Schema)
suite('ControlValue', ControlValueSchema, LegacyControlValueV0Schema)

describe('ControlValue units', () => {
  it('converts within a family', () => {
    expect(convertUnit(800_000_000, 'Hz', 'MHz')).toBe(800)
    expect(convertUnit(800, 'MHz', 'Hz')).toBe(800_000_000)
    expect(convertUnit(1.5, 'GHz', 'kHz')).toBe(1_500_000)
  })
  it('refuses to guess across families, absolutes or unknowns', () => {
    expect(convertUnit(800_000_000, 'Hz', 'dBm')).toBe(800_000_000)
    expect(convertUnit(-40, 'dBm', 'dBm')).toBe(-40)
    expect(convertUnit(470, 'MHz', 'furlong')).toBe(470)
    expect(convertUnit('Keysight,N9340B', 'Hz', 'MHz')).toBe('Keysight,N9340B')
  })
})

describe('ControlValue identity', () => {
  it('ignores ts and origin, so dedupe survives the envelope', () => {
    const a = { value: 800, unit: 'MHz', ts: '2026-08-07T19:42:00.000Z', origin: 'web-1' }
    const b = { value: 800, unit: 'MHz', ts: '2026-08-07T19:42:09.999Z', origin: 'web-2' }
    expect(controlIdentity(a)).toBe(controlIdentity(b))
  })
  it('separates values that differ only by unit', () => {
    expect(controlIdentity({ value: 800, unit: 'MHz' })).not.toBe(controlIdentity({ value: 800, unit: 'Hz' }))
  })
  it('separates a numeric 1 from the string "1"', () => {
    expect(controlIdentity({ value: 1 })).not.toBe(controlIdentity({ value: '1' }))
  })
})

describe('ControlValue legacy lift', () => {
  it('keeps the old full_id as origin and leaves unit ABSENT', () => {
    const lifted = mapLegacyControlValue({ value: -40, full_id: 'web-1' }, '2026-08-07T19:42:00.000Z')
    expect(ControlValueSchema.safeParse(lifted).success).toBe(true)
    expect(lifted.origin).toBe('web-1')
    expect(lifted.unit).toBeUndefined()
  })
  it('marks an originless legacy payload rather than inventing one', () => {
    expect(mapLegacyControlValue({ value: 'ON' }, '2026-08-07T19:42:00.000Z').origin).toBe('unknown')
  })
})

describe('mapV40VisaRecord (step 3e replay proof)', () => {
  it.each(docsIn('DeviceRecord/map'))('$name', ({ doc }) => {
    const { input, expected } = doc as { input: unknown; expected: unknown }
    const v0 = LegacyVisaRecordV0Schema.parse(input)
    expect(mapV40VisaRecord(v0)).toEqual(expected)
  })

  it('is lossless: the v0 schema types every field the agent emits', () => {
    for (const { name, doc } of docsIn('DeviceRecord/map')) {
      const input = (doc as { input: Record<string, unknown> }).input
      const typedKeys = Object.keys(LegacyVisaRecordV0Schema.shape).sort()
      expect(Object.keys(input).sort(), name).toEqual(typedKeys)
    }
  })
})

interface IdentityVectors {
  deviceId: Array<{ input: Parameters<typeof deviceIdFor>[0]; deviceId: string; why?: string }>
  fnv1a64: Array<{ input: string; hex: string }>
  fromUnixSeconds: Array<{ seconds: number; iso: string }>
}
const identity = JSON.parse(readFileSync(join(VECTORS_DIR, 'identity.json'), 'utf8')) as IdentityVectors

describe('identity + time vectors', () => {
  it.each(identity.deviceId)('deviceId $deviceId ($why)', (v) => {
    expect(deviceIdFor(v.input)).toBe(v.deviceId)
  })
  it.each(identity.fnv1a64)('fnv1a64 $input', (v) => {
    expect(fnv1a64(v.input)).toBe(v.hex)
  })
  it.each(identity.fromUnixSeconds)('fromUnixSeconds $seconds', (v) => {
    expect(fromUnixSeconds(v.seconds)).toBe(v.iso)
  })
})
