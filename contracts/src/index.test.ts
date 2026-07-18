import { describe, expect, it } from 'vitest'
import { z } from 'zod'

import { CONTRACTS_VERSION } from './index.js'

describe('contracts scaffold', () => {
  it('exposes the package version marker', () => {
    expect(CONTRACTS_VERSION).toBe('0.1.0')
  })

  it('zod v4 emits JSON Schema natively (the codegen pipeline precondition)', () => {
    const doc = z.object({ schemaVersion: z.literal(1) })
    expect(doc.safeParse({ schemaVersion: 1 }).success).toBe(true)
    expect(doc.safeParse({ v: 1 }).success).toBe(false)
    const jsonSchema = z.toJSONSchema(doc)
    expect(jsonSchema).toMatchObject({ type: 'object' })
  })
})
