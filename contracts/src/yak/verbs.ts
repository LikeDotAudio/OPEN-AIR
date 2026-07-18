/**
 * The RUNTIME yak contract — guidelines Y7 and finding #2: the verbs never
 * appear in the definition files; they arrive over MQTT as the `yak_handler`
 * block inside the GUI value envelope (openair-yak/src/models.rs:9). This is
 * the second of the two YAK contracts (the in-file binding block is
 * layout/yak-binding.ts).
 *
 * Note the wire shape is LOOSER than the authoring shape: the agent
 * deserializes every field with #[serde(default)], so absent fields become
 * ""/false rather than errors. Schema'd as it exists.
 */
import { z } from 'zod'

import { YAK_VERB_VALUES } from '../layout/yak-binding.js'

/** models.rs `YakHandler` — every field defaulted on the wire. */
export const YakHandlerWireSchema = z.object({
  enable: z.boolean().default(false),
  yak_type: z.string().default(''), // "set" | "rig" | "nab" | "do" by convention; agent lowercases
  sub_path: z.string().default(''),
  command: z.string().default(''),
  input_name: z.string().default(''),
  converter: z.string().default(''),
})
export type YakHandlerWire = z.infer<typeof YakHandlerWireSchema>

/** models.rs `IncomingMessage` — the envelope the YAK agent reads off OpenAir/Gui/#. */
export const YakIncomingMessageSchema = z.object({
  handler: z.string().default(''),
  yak_handler: YakHandlerWireSchema.nullable().optional(),
})
export type YakIncomingMessage = z.infer<typeof YakIncomingMessageSchema>

export { YAK_VERB_VALUES }
