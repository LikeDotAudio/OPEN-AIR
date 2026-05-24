/**
 * NeedleMeter/Designer.jsx — bespoke "Artistic Properties" designer for the
 * _NeedleVUMeter (analog VU). Self-registers into window.OaDesignerRegistry so
 * the WYSIWYG pop-out designer uses it for this widget type. Every control
 * writes to the canonical nested paths NeedleMeter.jsx reads.
 */
(function () {
  const TYPES = ['_NeedleVUMeter', 'NeedleMeter'];

  // Picker option lists (kept here so they always match NeedleMeter.jsx).
  const BEZEL_SHAPES = ['default', 'gem', 'super_gem', 'octagon', 'triangle', 'pyramid', 'hex', 'hotdog', 'cylinder', 'squircle', 'squimonde', 'squectangle', 'trapezoid', 'badge', 'crest', 'shield', 'parking_meter', 'stereo_diamond', 'intersecting_overlay'];
  const FACE_STYLES = ['none', 'cream', 'new_old_stock', 'vintage_aged', 'bakelite', 'tungsten', 'wood'];

  const getAt = (obj, dot) => { let n = obj; for (const k of String(dot).split('.')) { if (n == null) return undefined; n = n[k]; } return n; };

  const Designer = ({ store, path, node, ctl }) => {
    const { Section, Slider, Color, Toggle, Enum, Text } = ctl;
    const ref = (window.OaEdComposite) ? window.OaEdComposite.referenceForType('_NeedleVUMeter') : null;
    const merged = ref ? window.OaEdComposite.merge(ref, node) : node;
    const set = (dot, v) => store.setProp(path, dot, v);
    const g = (dot) => getAt(merged, dot);

    return (
      <div>
        <div style={{ fontSize: 11, color: '#888', margin: '2px 0 6px' }}>
          Analog VU meter — sculpt the window, face, limits and motion live.
        </div>

        <Section title="📐 Domain & limits" defaultOpen>
          <Text label="min" value={g('domain.primary.min')} onChange={(v) => set('domain.primary.min', v)} />
          <Text label="max" value={g('domain.primary.max')} onChange={(v) => set('domain.primary.max', v)} />
          <Text label="default" value={g('domain.primary.value_default')} onChange={(v) => set('domain.primary.value_default', v)} />
          <Text label="yellow start (mid)" value={g('cosmetics.scale.mid_range_start')} onChange={(v) => set('cosmetics.scale.mid_range_start', v)} />
          <Text label="red start (upper)" value={g('cosmetics.scale.upper_range')} onChange={(v) => set('cosmetics.scale.upper_range', v)} />
        </Section>

        <Section title="🪟 Window (bezel)" defaultOpen>
          <Enum label="bezel shape" value={g('cosmetics.style_overrides.bezel_shape')} options={BEZEL_SHAPES} onChange={(v) => set('cosmetics.style_overrides.bezel_shape', v)} />
          <Color label="bezel color" value={g('cosmetics.colors.bezel')} onChange={(v) => set('cosmetics.colors.bezel', v)} />
          <Slider label="bezel width" min={1} max={30} step={1} value={g('cosmetics.style_overrides.bezel_width') ?? 6} onChange={(v) => set('cosmetics.style_overrides.bezel_width', v)} />
        </Section>

        <Section title="🎨 Face">
          <Enum label="face style" value={g('cosmetics.style_overrides.face_style')} options={FACE_STYLES} onChange={(v) => set('cosmetics.style_overrides.face_style', v)} />
          <Color label="faceplate color" value={g('cosmetics.colors.faceplate')} onChange={(v) => set('cosmetics.colors.faceplate', v)} />
          <Toggle label="glass sheen" value={g('cosmetics.style_overrides.enable_lighting') !== false} onChange={(v) => set('cosmetics.style_overrides.enable_lighting', v)} />
        </Section>

        <Section title="🎚 Limits (colors)">
          <Color label="green (lower)" value={g('cosmetics.colors.lower')} onChange={(v) => set('cosmetics.colors.lower', v)} />
          <Color label="yellow (middle)" value={g('cosmetics.colors.middle')} onChange={(v) => set('cosmetics.colors.middle', v)} />
          <Color label="red (upper)" value={g('cosmetics.colors.upper')} onChange={(v) => set('cosmetics.colors.upper', v)} />
        </Section>

        <Section title="🧭 Tilt & motion">
          <Slider label="center angle" min={0} max={360} step={1} value={g('cosmetics.style_overrides.Meter_center_angle') ?? 90} onChange={(v) => set('cosmetics.style_overrides.Meter_center_angle', v)} />
          <Slider label="viewable angle" min={10} max={359} step={1} value={g('cosmetics.style_overrides.Meter_viewable_angle') ?? 90} onChange={(v) => set('cosmetics.style_overrides.Meter_viewable_angle', v)} />
          <Toggle label="counter-clockwise" value={!!g('cosmetics.style_overrides.Counter_Clockwise')} onChange={(v) => set('cosmetics.style_overrides.Counter_Clockwise', v)} />
        </Section>

        <Section title="🪡 Needle & ticks">
          <Color label="needle color" value={g('cosmetics.colors.pointer')} onChange={(v) => set('cosmetics.colors.pointer', v)} />
          <Color label="pivot color" value={g('cosmetics.colors.pivot')} onChange={(v) => set('cosmetics.colors.pivot', v)} />
          <Slider label="pivot size" min={2} max={24} step={1} value={g('cosmetics.style_overrides.Pivot_size') ?? 10} onChange={(v) => set('cosmetics.style_overrides.Pivot_size', v)} />
          <Slider label="curve thickness" min={1} max={10} step={1} value={g('cosmetics.style_overrides.curve_thickness') ?? 3} onChange={(v) => set('cosmetics.style_overrides.curve_thickness', v)} />
          <Slider label="sub ticks" min={0} max={10} step={1} value={g('cosmetics.style_overrides.sub_ticks') ?? 5} onChange={(v) => set('cosmetics.style_overrides.sub_ticks', v)} />
          <Toggle label="scale numbers" value={g('cosmetics.style_overrides.Scale_numbers') !== false} onChange={(v) => set('cosmetics.style_overrides.Scale_numbers', v)} />
        </Section>
      </div>
    );
  };

  window.OaDesigner_NeedleMeter = Designer;
  window.OaDesignerRegistry = window.OaDesignerRegistry || {};
  TYPES.forEach((t) => { window.OaDesignerRegistry[t] = Designer; });
})();
