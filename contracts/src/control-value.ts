/**
 * ControlValue — one value crossing a control topic.
 *
 * Every value a panel sends, and every value an agent reports, answers four
 * questions: WHAT it is (`value`), WHAT IT MEANS (`unit`), WHEN it was produced
 * (`ts`), and WHO produced it (`origin`). The transmitter declares and scales;
 * the receiver accepts and scales.
 *
 * WHY A UNIT RATHER THAN A CONVERTER
 *
 * Today a widget names a converter — `"converter": "mhz_to_hz"` — which is a
 * guess by the sender about what the receiver wants. It is unverifiable and it
 * has already failed silently: `bool_to_int` appears on eleven controls and is
 * not in KNOWN_CONVERTERS, so it matched no branch in the YAK agent and passed
 * values through unconverted. A unit is not a guess. It is a fact about the
 * value, and any receiver can convert from it to whatever it needs — including
 * receivers the sender has never heard of.
 *
 * WHY A TIMESTAMP AND AN ORIGIN
 *
 * `origin` already exists in the wild as `full_id`, and it is load-bearing in
 * two places: suppressing a client's own echo, and telling a command apart from
 * retained state replayed at connect. `ts` is what lets a late or reordered
 * message be recognised as stale rather than applied as current.
 *
 * ⚠ `ts` AND `origin` ARE METADATA, NOT IDENTITY.
 *
 * Deduplication MUST use `controlIdentity()`, which hashes only value+unit. A
 * timestamp makes every payload byte-unique, so any dedupe that serialises the
 * whole envelope stops working the moment this contract lands — and the failure
 * is not a crash. It is one SCPI write per drag sample reaching real hardware
 * again, which is precisely the storm this system just got rid of.
 */
import { z } from 'zod'

/**
 * Units this contract can convert between, as ratios to each family's base.
 *
 * Conversion is defined WITHIN a family only. Hz→MHz is arithmetic; Hz→dBm is
 * not, and a contract that quietly returned a number for it would be lying.
 * Dimensionless quantities (a boolean, an enum, a trace index) carry no unit at
 * all rather than a placeholder one.
 */
export const UNIT_FAMILIES = {
  frequency: { base: 'Hz', units: { hz: 1, khz: 1e3, mhz: 1e6, ghz: 1e9 } },
  voltage: { base: 'V', units: { uv: 1e-6, mv: 1e-3, v: 1, kv: 1e3 } },
  time: { base: 's', units: { ns: 1e-9, us: 1e-6, ms: 1e-3, s: 1 } },
  power: { base: 'W', units: { uw: 1e-6, mw: 1e-3, w: 1, kw: 1e3 } },
} as const

/** Units with no ratio to anything: convertible only to themselves. */
export const ABSOLUTE_UNITS = ['dB', 'dBm', 'dBmV', 'dBuV', 'dBuA', '%'] as const

export type UnitFamilyName = keyof typeof UNIT_FAMILIES

const normUnit = (u: unknown): string => String(u ?? '').trim().toLowerCase().replace('μ', 'u')

/** Which family a unit belongs to, or undefined for unknown/absolute units. */
export function unitFamily(unit: unknown): UnitFamilyName | undefined {
  const u = normUnit(unit)
  for (const [name, fam] of Object.entries(UNIT_FAMILIES)) {
    if (Object.prototype.hasOwnProperty.call(fam.units, u)) return name as UnitFamilyName
  }
  return undefined
}

/**
 * Convert `value` from one unit to another.
 *
 * Returns the value UNCHANGED when the pair is not convertible — unknown unit,
 * different family, absolute unit, or a non-numeric value. Refusing to guess is
 * the point: a wrong number displayed confidently is worse than a raw one.
 */
export function convertUnit(value: unknown, from: unknown, to: unknown): unknown {
  const n = typeof value === 'number' ? value : Number(value)
  if (!Number.isFinite(n)) return value
  const f = normUnit(from)
  const t = normUnit(to)
  if (!f || !t || f === t) return n
  const famName = unitFamily(f)
  if (!famName || famName !== unitFamily(t)) return n
  const units = UNIT_FAMILIES[famName].units as Record<string, number>
  return n * (units[f] / units[t])
}

export const ControlValueSchema = z
  .object({
    schemaVersion: z.literal(1),
    /** Scalars only. A compound reading is several ControlValues, not one blob. */
    value: z.union([z.number(), z.string(), z.boolean()]),
    /** Omitted for dimensionless values; never `""`, which reads as "unknown". */
    unit: z.string().min(1).optional(),
    ts: z.iso.datetime(),
    /** Session or agent that produced this. Today's `full_id`. */
    origin: z.string().min(1),
  })
  .describe('ControlValue: one value on a control topic, with its unit, time and origin.')
export type ControlValue = z.infer<typeof ControlValueSchema>

/**
 * The envelope as it exists on the bus today: `{value, full_id}`, no unit, no
 * time. Readers must keep accepting it until every publisher has migrated —
 * a panel that stops rendering because a value predates the contract is a
 * regression, not enforcement.
 */
export const LegacyControlValueV0Schema = z
  .object({
    value: z.union([z.number(), z.string(), z.boolean()]),
    full_id: z.string().optional(),
  })
  .loose()
export type LegacyControlValueV0 = z.infer<typeof LegacyControlValueV0Schema>

/**
 * Lift a v0 payload into the contract.
 *
 * `unit` stays ABSENT rather than guessed. The old envelope genuinely does not
 * say what the number means, and inventing one here would launder an unknown
 * into an assertion — the same mistake `converter` made.
 */
export function mapLegacyControlValue(doc: LegacyControlValueV0, receivedAtIso: string): ControlValue {
  return {
    schemaVersion: 1,
    value: doc.value,
    ts: receivedAtIso,
    origin: doc.full_id && doc.full_id.length > 0 ? doc.full_id : 'unknown',
  }
}

/**
 * What makes two control messages "the same command".
 *
 * Value and unit only. Two messages with the same identity are interchangeable:
 * sending the second changes nothing an instrument or a panel would notice, so
 * a queue may drop it. `ts` and `origin` deliberately do NOT participate — see
 * the warning at the top of this file.
 *
 * Momentary controls are the documented exception: a trigger pressed twice is
 * two intended actions sharing one identity, and must never be collapsed.
 */
export function controlIdentity(cv: Pick<ControlValue, 'value' | 'unit'>): string {
  return `${typeof cv.value}:${String(cv.value)}|${normUnit(cv.unit)}`
}
