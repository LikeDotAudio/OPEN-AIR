/**
 * Widget type vocabulary — guidelines L1. Seeded from the live dispatch code
 * on 2026-07-17 (WidgetFactory.jsx container registry + fuzzy gate,
 * FieldComponent.jsx exact matches + substring cascade) and a full scan of
 * Gui_Frames (477 files, 157 distinct `type` strings). In Phase 2 this
 * becomes GENERATED from the typed widget registry; until then it documents
 * what actually renders vs. what falls to the dashed fallback box.
 */

/** Exact container registry (WidgetFactory.jsx:26-39). */
export const CONTAINER_TYPES = [
  'OcaBin',
  'OcaBlock',
  'OcaArray',
  'OcaCollapsibleBlock',
  'OcaNotebook',
  'OcaSplit',
  'OcaTable',
  'Sampler',
  'AudioEditor',
  'Sequencer',
] as const
export type ContainerType = (typeof CONTAINER_TYPES)[number]

/** Exact leaf matches in FieldComponent.jsx (type === '...'). */
export const EXACT_LEAF_TYPES = new Set([
  'AnimationDisplay', '_AudioAnalyzerDemo', '_AudioDynamics', '_BarGraph', '_Checkbox',
  '_CMDP_Editor', '_CMDPEditor', '_DataJsonTree', 'DynamicBarGraph', 'DynamicGraph',
  '_DynamicsEnvelope', '_DynamicsPresets', '_Equalization', '_FaderWithBarGraph',
  '_GCA', 'GCA', '_GuiDropDownOption', '_GuiImage', '_GuiLabel',
  '_Horizontal_with_dial_Value', '_Listbox', '_Meter', '_Meter_Knob_With_Vu_Meter',
  '_MidiMessageLog', 'panel', 'Panel', 'plot_widget', '_ProgressBar', 'ProgressBar',
  'ProtocolConfigDisplay', '_Radar', '_Reverb', 'screw', 'Screw', 'SelectorSwitch',
  '_SliderValue', '_SmartFader', '_SmartIncDec', '_SmartInput', '_SmartLight',
  '_SmartList', '_SmartMeter', '_SmartNav', '_SmartProgress', 'Spacer', '_TextInput',
  'OcaTextInput',
])

/** FieldComponent.jsx substring cascade (first match wins), lowercase. */
export const LEAF_SUBSTRINGS = [
  'actuator', 'animation', 'bargraph', 'break_line', 'breakline', 'button', 'checkbox',
  'cmdp', 'composite', 'dial_value', 'directional', 'dropdown', 'dual', 'fader',
  'ganged', 'graph', 'highvis', 'image', 'image_display', 'inc_dec', 'incdec',
  'indicator', 'json', 'keyboard', 'knob', 'label', 'link', 'listbox', 'ltp', 'mdp',
  'meter', 'midi', 'needle', 'picture', 'progress', 'protocolconfig', 'radar',
  'separator', 'slider', 'status_light', 'table', 'toggle', 'toggler', 'trapezoid',
  'value', 'vu', 'wink',
  // WidgetFactory gate extras
  'selector', 'plot', 'panel', 'screw',
] as const

/**
 * The v0 widget generation the current renderer no longer speaks natively
 * (flattened via compatibility shims; `_GuiValue` is the legacy
 * discovered-frame variant — Phase 1 §2.3 marks it deprecated by name).
 */
export const LEGACY_WIDGET_TYPES = new Set(['_GuiValue'])

export type WidgetTypeClass =
  | 'container'
  | 'leaf' // renders via FieldComponent (exact, substring, or `_` convention)
  | 'legacy' // renders, but is a named deprecation (_GuiValue)
  | 'data-model' // AES70/data-set string living in the panel tree — relocate (guidelines §8)
  | 'unknown' // falls to the dashed fallback box — loud error

/** One classification rule set for the validate CLI, the editor, and Phase 2's registry. */
export function classifyWidgetType(type: string): WidgetTypeClass {
  if ((CONTAINER_TYPES as readonly string[]).includes(type)) return 'container'
  if (LEGACY_WIDGET_TYPES.has(type)) return 'legacy'
  if (EXACT_LEAF_TYPES.has(type)) return 'leaf'
  const lower = type.toLowerCase()
  if (LEAF_SUBSTRINGS.some((s) => lower.includes(s))) return 'leaf'
  if (type.startsWith('_')) return 'leaf' // WidgetFactory gate: any `_` type reaches FieldComponent
  if (type.startsWith('Oca')) return 'data-model'
  return 'unknown'
}
