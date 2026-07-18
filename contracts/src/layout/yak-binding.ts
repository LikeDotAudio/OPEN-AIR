/**
 * The in-file yak binding block — guidelines L3, schema'd AS IT EXISTS
 * (62 occurrences, keys: enable, yak_type, sub_path, command, input_name,
 * converter, + occasional marker_number, trace_number, trigger_only).
 * Cross-field rule: set/rig require input_name.
 */
import { z } from 'zod'

export const YAK_VERB_VALUES = ['set', 'rig', 'nab', 'do'] as const

/**
 * Converters the YAK agent actually implements (converters.rs) — anything
 * else silently passes through today, which is exactly what the validate
 * CLI names. The live panel scan (2026-07-17) found 45 uses of converters
 * OUTSIDE this set: int(25), bool_to_int(11), float(5), string(4).
 */
export const KNOWN_CONVERTERS = new Set([
  'mhz_to_hz', 'hz_to_mhz', 'khz_to_hz', 'hz_to_khz', 'v_to_mv', 'mv_to_v',
])

export const YakBindingSchema = z
  .object({
    enable: z.boolean(),
    yak_type: z.enum(YAK_VERB_VALUES),
    sub_path: z.string(),
    command: z.string().min(1),
    input_name: z.string().optional(),
    converter: z.string().optional(),
    marker_number: z.union([z.number(), z.string()]).optional(),
    trace_number: z.union([z.number(), z.string()]).optional(),
    trigger_only: z.boolean().optional(),
  })
  .check((ctx) => {
    const v = ctx.value
    if ((v.yak_type === 'set' || v.yak_type === 'rig') && !v.input_name) {
      ctx.issues.push({
        code: 'custom',
        message: `yak_type "${v.yak_type}" requires input_name`,
        input: v,
        path: ['input_name'],
      })
    }
  })
export type YakBinding = z.infer<typeof YakBindingSchema>

/** Non-fatal binding lints the CLI reports beyond schema validity. */
export function lintYakBinding(binding: Record<string, unknown>): string[] {
  const notes: string[] = []
  const conv = binding['converter']
  if (typeof conv === 'string' && conv !== '' && !KNOWN_CONVERTERS.has(conv.toLowerCase())) {
    notes.push(`converter "${conv}" is unknown to the YAK agent (silent passthrough today)`)
  }
  const KNOWN_KEYS = new Set([
    'enable', 'yak_type', 'sub_path', 'command', 'input_name', 'converter',
    'marker_number', 'trace_number', 'trigger_only',
  ])
  for (const k of Object.keys(binding)) {
    if (!KNOWN_KEYS.has(k)) notes.push(`unknown yak_handler key "${k}"`)
  }
  return notes
}
