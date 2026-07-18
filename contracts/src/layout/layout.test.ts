import { describe, expect, it } from 'vitest'

import { findOrderCollisions, parseFolderName } from './folder-grammar.js'
import { validateLayoutDocument } from './node.js'
import { classifyWidgetType } from './widget-types.js'
import { YakBindingSchema, lintYakBinding } from './yak-binding.js'
import { YakIncomingMessageSchema } from '../yak/verbs.js'

describe('classifyWidgetType', () => {
  it.each([
    ['OcaBin', 'container'],
    ['OcaBlock', 'container'],
    ['_SmartKnob', 'leaf'],
    ['SelectorSwitch', 'leaf'],
    ['OcaTextInput', 'leaf'],
    ['Spacer', 'leaf'],
    ['_GuiValue', 'legacy'],
    ['OcaMap<OcaONo, OcaList<OcaMediaClockRate>>', 'data-model'],
    ['OcaProperty', 'data-model'],
    ['tv', 'unknown'],
  ] as const)('%s → %s', (type, expected) => {
    expect(classifyWidgetType(type)).toBe(expected)
  })
})

describe('validateLayoutDocument', () => {
  const strictLeaf = {
    type: '_SmartKnob',
    label: { active: { text: { En: 'Freq' } } },
    domain: { units: 'Hz', primary: { min: 0, max: 100 } },
    yak_handler: { enable: true, yak_type: 'set', sub_path: 'freq', command: 'SetCenter', input_name: 'hz_value', converter: 'mhz_to_hz' },
  }

  it('strict-valid node produces zero issues', () => {
    expect(validateLayoutDocument({ Panel: { type: 'OcaBlock', fields: { k: strictLeaf } } })).toEqual([])
  })

  it('names legacy flat keys as deprecations', () => {
    const issues = validateLayoutDocument({ type: '_SmartKnob', min: 0, max: 10, label_active: 'On' })
    const codes = issues.map((i) => i.code).sort()
    expect(codes).toEqual(['legacy-flat-key:label_active', 'legacy-flat-key:max', 'legacy-flat-key:min'])
    expect(issues.every((i) => i.level === 'deprecation')).toBe(true)
  })

  it('dead keys are errors even in legacy mode', () => {
    const issues = validateLayoutDocument({ type: '_GuiValue', subscribe: 'x' })
    expect(issues.find((i) => i.code === 'dead-key:subscribe')?.level).toBe('error')
    expect(issues.find((i) => i.code === 'legacy-widget-type')?.level).toBe('deprecation')
  })

  it('unknown widget types are loud errors', () => {
    const issues = validateLayoutDocument({ type: 'FluxCapacitor' })
    expect(issues).toHaveLength(1)
    expect(issues[0]).toMatchObject({ level: 'error', code: 'unknown-widget-type' })
  })

  it('topic overrides must parse (catches OPEN-AIR casing)', () => {
    const issues = validateLayoutDocument({ type: '_GuiLabel', topic: 'OPEN-AIR/Fleet/Status' })
    expect(issues[0]).toMatchObject({ level: 'error', code: 'invalid-topic-override' })
    const legacy = validateLayoutDocument({ type: '_GuiLabel', topic: 'OpenAir/System/Protocols/yak/monitor/in' })
    expect(legacy[0]).toMatchObject({ level: 'deprecation', code: 'legacy-topic-override' })
  })

  it('nested pillar min/max are NOT flagged', () => {
    expect(validateLayoutDocument({ type: '_SmartKnob', domain: { min: 0, max: 10, primary: { min: 0 } } })).toEqual([])
  })
})

describe('YakBindingSchema (L3)', () => {
  it('set without input_name fails', () => {
    const r = YakBindingSchema.safeParse({ enable: true, yak_type: 'set', sub_path: 'x', command: 'C' })
    expect(r.success).toBe(false)
  })
  it('nab without input_name is fine', () => {
    const r = YakBindingSchema.safeParse({ enable: true, yak_type: 'nab', sub_path: 'x', command: 'C' })
    expect(r.success).toBe(true)
  })
  it('lint names converters the agent does not implement', () => {
    expect(lintYakBinding({ converter: 'bool_to_int' })[0]).toMatch(/unknown to the YAK agent/)
    expect(lintYakBinding({ converter: 'mhz_to_hz' })).toEqual([])
  })
})

describe('YakIncomingMessageSchema (Y7 wire shape)', () => {
  it('defaults every field like the agent serde does', () => {
    const msg = YakIncomingMessageSchema.parse({ yak_handler: { enable: true, yak_type: 'set' } })
    expect(msg.yak_handler).toMatchObject({ enable: true, yak_type: 'set', command: '', input_name: '' })
  })
})

describe('folder grammar (L4)', () => {
  it.each([
    ['0_Spectrum', { order: 0, base: 'Spectrum', geometry: false }],
    ['left_50', { base: 'left_50', geometry: true }],
    ['Window_1', { base: 'Window_1', geometry: true }],
    ['Channel_1', { base: 'Channel_1', geometry: false }],
    ['42', { geometry: true }],
  ])('%s', (name, expected) => {
    expect(parseFolderName(name)).toMatchObject(expected)
  })

  it('parses split names', () => {
    expect(parseFolderName('left_50').split).toEqual({ direction: 'left', percent: 50 })
    expect(parseFolderName('top_100').split).toEqual({ direction: 'top', percent: 100 })
  })

  it('finds the 4_DMM/4_Load collision', () => {
    expect(findOrderCollisions(['4_DMM_YAK', '4_Load_YAK', '1_Spectrum_YAK'])).toEqual([
      { order: 4, names: ['4_DMM_YAK', '4_Load_YAK'] },
    ])
  })
})
