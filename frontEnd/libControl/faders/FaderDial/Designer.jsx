/**
 * FaderDial/Designer.jsx — BESPOKE "Artistic Properties" designer for the
 * _Horizontal_with_dial_Value composite (fader + knob + readout).
 *
 * Self-registers into window.OaDesignerRegistry so the WYSIWYG's pop-out designer
 * (editorWYSIWYG/Interface/PropertyEditor/artistic_designer.jsx) uses it for this
 * widget type. Reuses the shared artistic controls passed in as `ctl`
 * (= window.OaEdArtisticCtl). Every edit writes through store.setProp at the
 * canonical NESTED sub-config paths (cosmetics.* / readout.* / interaction.*),
 * matching what FaderDial.jsx → Fader.jsx / Knob.jsx read.
 *
 * Props: { store, path, node, type, ctl }. When run standalone (Designer.html)
 * a shim store + a synthesized node are provided.
 */
(function () {
  const TYPE = '_Horizontal_with_dial_Value';

  const getAt = (obj, dot) => {
    let n = obj;
    for (const k of String(dot).split('.')) { if (n == null) return undefined; n = n[k]; }
    return n;
  };

  const Designer = ({ store, path, node, ctl }) => {
    const { Section, Slider, Color, Toggle, Enum, Text, Auto } = ctl;

    // Pre-fill controls with the library reference defaults so every knob shows a
    // value even before the instance saves one; editing materializes it.
    const ref = (window.OaEdComposite) ? window.OaEdComposite.referenceForType(TYPE) : null;
    const merged = ref ? window.OaEdComposite.merge(ref, node) : node;

    const set = (dot, v) => store.setProp(path, dot, v);
    const g = (dot) => getAt(merged, dot);

    // knob_style / shape / pointer.style / scale.style enum option lists.
    const opt = (kp) => (window.OaEdEnum ? (window.OaEdEnum.optionsFor(kp) || []) : []);

    return (
      <div>
        <div style={{ fontSize: 11, color: '#888', margin: '2px 0 6px' }}>
          Sculpt the composite live. Sliders & swatches write straight back to the element.
        </div>

        <Section title="Domain & Value" defaultOpen>
          <Auto label="min" keyPath="domain.min" value={g('domain.min')} onChange={(v) => set('domain.min', v)} />
          <Auto label="max" keyPath="domain.max" value={g('domain.max')} onChange={(v) => set('domain.max', v)} />
          <Text label="units" value={g('domain.units')} onChange={(v) => set('domain.units', v)} />
          <Auto label="step_coarse" keyPath="domain.step_coarse" value={g('domain.step_coarse')} onChange={(v) => set('domain.step_coarse', v)} />
          <Auto label="step_fine" keyPath="domain.step_fine" value={g('domain.step_fine')} onChange={(v) => set('domain.step_fine', v)} />
          <Text label="precision" value={g('domain.precision')} onChange={(v) => set('domain.precision', v)} />
          <Auto label="default_value" keyPath="value.default_value" value={g('value.default_value')} onChange={(v) => set('value.default_value', v)} />
          <Toggle label="locked" value={!!g('domain.locked')} onChange={(v) => set('domain.locked', v)} />
          <Toggle label="show_label" value={g('label.show_label') !== false} onChange={(v) => set('label.show_label', v)} />
        </Section>

        <Section title="Column spacing  [fader · knob · value]" defaultOpen={false}>
          <Slider label="fader gap" min={0} max={120} step={1} value={g('layout.column_spacing.0') ?? 0} onChange={(v) => set('layout.column_spacing.0', v)} />
          <Slider label="knob gap" min={0} max={120} step={1} value={g('layout.column_spacing.1') ?? 0} onChange={(v) => set('layout.column_spacing.1', v)} />
          <Slider label="value gap" min={0} max={120} step={1} value={g('layout.column_spacing.2') ?? 0} onChange={(v) => set('layout.column_spacing.2', v)} />
        </Section>

        <Section title="🎚 Fader (coarse)">
          <Color label="cap color" value={g('fader_config.cosmetics.colors.cap')} onChange={(v) => set('fader_config.cosmetics.colors.cap', v)} />
          <Color label="cap highlight" value={g('fader_config.cosmetics.colors.cap_highlight')} onChange={(v) => set('fader_config.cosmetics.colors.cap_highlight', v)} />
          <Color label="value highlight" value={g('fader_config.cosmetics.colors.highlight')} onChange={(v) => set('fader_config.cosmetics.colors.highlight', v)} />
          <Color label="tick color" value={g('fader_config.cosmetics.colors.tick_color')} onChange={(v) => set('fader_config.cosmetics.colors.tick_color', v)} />
          <Color label="sub-tick color" value={g('fader_config.cosmetics.colors.sub_tick_color')} onChange={(v) => set('fader_config.cosmetics.colors.sub_tick_color', v)} />
          <Color label="bar color" value={g('fader_config.bar_color')} onChange={(v) => set('fader_config.bar_color', v)} />
          <Slider label="glow" min={0} max={3} step={0.1} value={g('fader_config.cosmetics.styling.glow_intensity') ?? 0} onChange={(v) => set('fader_config.cosmetics.styling.glow_intensity', v)} />
          <Slider label="cap width" min={10} max={120} step={1} value={g('fader_config.cap_width') ?? 40} onChange={(v) => set('fader_config.cap_width', v)} />
          <Slider label="cap height" min={10} max={120} step={1} value={g('fader_config.cap_height') ?? 50} onChange={(v) => set('fader_config.cap_height', v)} />
          <Toggle label="show ticks" value={g('fader_config.cosmetics.scale.show') !== false} onChange={(v) => set('fader_config.cosmetics.scale.show', v)} />
        </Section>

        <Section title="🎛 Knob (fine)">
          <Enum label="knob style" value={g('dial_config.cosmetics.style_overrides.knob_style')} options={opt('cosmetics.style_overrides.knob_style')} onChange={(v) => set('dial_config.cosmetics.style_overrides.knob_style', v)} />
          <Enum label="shape" value={g('dial_config.cosmetics.style_overrides.shape')} options={opt('cosmetics.style_overrides.shape')} onChange={(v) => set('dial_config.cosmetics.style_overrides.shape', v)} />
          <Slider label="teeth" min={0} max={24} step={1} value={g('dial_config.cosmetics.styling.teeth') ?? 8} onChange={(v) => set('dial_config.cosmetics.styling.teeth', v)} />
          <Color label="active color" value={g('dial_config.cosmetics.colors.active')} onChange={(v) => set('dial_config.cosmetics.colors.active', v)} />
          <Color label="indicator color" value={g('dial_config.indicator_color')} onChange={(v) => set('dial_config.indicator_color', v)} />
          <Color label="fill color" value={g('dial_config.cosmetics.styling.fill_color')} onChange={(v) => set('dial_config.cosmetics.styling.fill_color', v)} />
          <Color label="outline color" value={g('dial_config.cosmetics.styling.outline_color')} onChange={(v) => set('dial_config.cosmetics.styling.outline_color', v)} />
          <Slider label="arc width" min={1} max={16} step={1} value={g('dial_config.cosmetics.styling.arc_width') ?? 5} onChange={(v) => set('dial_config.cosmetics.styling.arc_width', v)} />
          <Enum label="pointer style" value={g('dial_config.cosmetics.pointer.style')} options={opt('cosmetics.pointer.style')} onChange={(v) => set('dial_config.cosmetics.pointer.style', v)} />
          <Slider label="pointer length" min={0} max={60} step={1} value={g('dial_config.cosmetics.pointer.length') ?? 25} onChange={(v) => set('dial_config.cosmetics.pointer.length', v)} />
          <Slider label="pointer offset" min={0} max={40} step={1} value={g('dial_config.cosmetics.pointer.offset') ?? 0} onChange={(v) => set('dial_config.cosmetics.pointer.offset', v)} />
          <Toggle label="show ticks" value={g('dial_config.cosmetics.scale.show') !== false} onChange={(v) => set('dial_config.cosmetics.scale.show', v)} />
          <Enum label="tick style" value={g('dial_config.cosmetics.scale.style')} options={opt('scale.style')} onChange={(v) => set('dial_config.cosmetics.scale.style', v)} />
          <Toggle label="no center" value={!!g('dial_config.cosmetics.styling.no_center')} onChange={(v) => set('dial_config.cosmetics.styling.no_center', v)} />
          <Toggle label="infinity" value={!!g('dial_config.interaction.infinity')} onChange={(v) => set('dial_config.interaction.infinity', v)} />
          <Toggle label="fine pitch" value={!!g('dial_config.interaction.fine_pitch')} onChange={(v) => set('dial_config.interaction.fine_pitch', v)} />
        </Section>

        <Section title="🔢 Value readout" defaultOpen={false}>
          <Color label="text color" value={g('value_config.colour')} onChange={(v) => set('value_config.colour', v)} />
          <Color label="background" value={g('value_config.bg_color')} onChange={(v) => set('value_config.bg_color', v)} />
          <Slider label="font" min={8} max={48} step={1} value={g('value_config.font') ?? 18} onChange={(v) => set('value_config.font', v)} />
          <Slider label="width" min={4} max={30} step={1} value={g('value_config.width') ?? 12} onChange={(v) => set('value_config.width', v)} />
          <Slider label="height" min={16} max={80} step={1} value={g('value_config.height') ?? 35} onChange={(v) => set('value_config.height', v)} />
        </Section>
      </div>
    );
  };

  window.OaDesigner_FaderDial = Designer;
  window.OaDesignerRegistry = window.OaDesignerRegistry || {};
  window.OaDesignerRegistry[TYPE] = Designer;
})();
