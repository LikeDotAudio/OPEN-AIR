/**
 * NeedleMeter/Designer.jsx — bespoke "Artistic Properties" designer for the
 * _NeedleVUMeter (analog VU). Self-registers into window.OaDesignerRegistry.
 * Sections mirror the meter's anatomy: Window (bezel) · Face · NEEDLE (pointer +
 * pivot) · SCALE (rule + ticks + numbers) · Tilt · Geometry/offsets. Every
 * control writes the canonical nested path NeedleMeter.jsx reads.
 */
(function () {
  const TYPES = ['_NeedleVUMeter', 'NeedleMeter'];

  const BEZEL_SHAPES = ['default', 'gem', 'super_gem', 'octagon', 'triangle', 'pyramid', 'hex', 'hotdog', 'cylinder', 'squircle', 'squimonde', 'squectangle', 'trapezoid', 'badge', 'crest', 'shield', 'parking_meter', 'stereo_diamond', 'intersecting_overlay'];
  const FACE_STYLES = ['none', 'cream', 'new_old_stock', 'vintage_aged', 'bakelite', 'tungsten', 'wood'];
  const NEEDLE_STYLES = ['line', 'spade', 'knife', 'baton', 'diamond'];
  const NEEDLE_SIZES = ['thin', 'small', 'medium', 'large', 'xlarge'];

  const getAt = (obj, dot) => { let n = obj; for (const k of String(dot).split('.')) { if (n == null) return undefined; n = n[k]; } return n; };

  const Designer = ({ store, path, node, ctl }) => {
    const { Section, Slider, Color, Toggle, Enum, Text } = ctl;
    const ref = (window.OaEdComposite) ? window.OaEdComposite.referenceForType('_NeedleVUMeter') : null;
    const merged = ref ? window.OaEdComposite.merge(ref, node) : node;
    const set = (dot, v) => store.setProp(path, dot, v);
    const g = (dot) => getAt(merged, dot);
    const SO = 'cosmetics.style_overrides.';

    return (
      <div>
        <div style={{ fontSize: 11, color: '#888', margin: '2px 0 6px' }}>
          Analog VU meter — window, face, needle, and scale, each its own group.
        </div>

        <Section title="📐 Domain" defaultOpen>
          <Text label="min" value={g('domain.primary.min')} onChange={(v) => set('domain.primary.min', v)} />
          <Text label="max" value={g('domain.primary.max')} onChange={(v) => set('domain.primary.max', v)} />
          <Text label="default" value={g('domain.primary.value_default')} onChange={(v) => set('domain.primary.value_default', v)} />
        </Section>

        <Section title="🪟 Window (bezel)" defaultOpen>
          <Enum label="bezel shape" value={g(SO + 'bezel_shape')} options={BEZEL_SHAPES} onChange={(v) => set(SO + 'bezel_shape', v)} />
          <Color label="bezel color" value={g('cosmetics.colors.bezel')} onChange={(v) => set('cosmetics.colors.bezel', v)} />
          <Slider label="bezel width" min={1} max={30} step={1} value={g(SO + 'bezel_width') ?? 6} onChange={(v) => set(SO + 'bezel_width', v)} />
        </Section>

        <Section title="🎨 Face">
          <Enum label="face style" value={g(SO + 'face_style')} options={FACE_STYLES} onChange={(v) => set(SO + 'face_style', v)} />
          <Color label="faceplate color" value={g('cosmetics.colors.faceplate')} onChange={(v) => set('cosmetics.colors.faceplate', v)} />
          <Toggle label="glass sheen" value={g(SO + 'enable_lighting') !== false} onChange={(v) => set(SO + 'enable_lighting', v)} />
        </Section>

        <Section title="🪡 Needle" defaultOpen>
          <Enum label="needle style" value={g(SO + 'Pointer_Style')} options={NEEDLE_STYLES} onChange={(v) => set(SO + 'Pointer_Style', v)} />
          <Enum label="needle size" value={g(SO + 'needle_size')} options={NEEDLE_SIZES} onChange={(v) => set(SO + 'needle_size', v)} />
          <Slider label="needle length" min={0.3} max={1.2} step={0.05} value={g(SO + 'needle_length_factor') ?? 0.95} onChange={(v) => set(SO + 'needle_length_factor', v)} />
          <Slider label="needle thickness" min={1} max={12} step={1} value={g(SO + 'Needle_thickness') ?? 2} onChange={(v) => set(SO + 'Needle_thickness', v)} />
          <Color label="needle color" value={g('cosmetics.colors.pointer')} onChange={(v) => set('cosmetics.colors.pointer', v)} />
          <Color label="pivot color" value={g('cosmetics.colors.pivot')} onChange={(v) => set('cosmetics.colors.pivot', v)} />
          <Slider label="pivot size" min={2} max={24} step={1} value={g(SO + 'Pivot_size') ?? 10} onChange={(v) => set(SO + 'Pivot_size', v)} />
        </Section>

        <Section title="📏 Scale" defaultOpen>
          <div style={{ fontSize: 10, color: '#777', margin: '2px 0' }}>— rule (the curved arc & limits) —</div>
          <Toggle label="show curved rule" value={g(SO + 'show_rule') !== false} onChange={(v) => set(SO + 'show_rule', v)} />
          <Slider label="rule thickness" min={1} max={10} step={1} value={g(SO + 'curve_thickness') ?? 3} onChange={(v) => set(SO + 'curve_thickness', v)} />
          <Slider label="rule radius offset" min={-30} max={30} step={1} value={g(SO + 'rule_radius_offset') ?? 0} onChange={(v) => set(SO + 'rule_radius_offset', v)} />
          <Color label="green (lower)" value={g('cosmetics.colors.lower')} onChange={(v) => set('cosmetics.colors.lower', v)} />
          <Color label="yellow (middle)" value={g('cosmetics.colors.middle')} onChange={(v) => set('cosmetics.colors.middle', v)} />
          <Color label="red (upper)" value={g('cosmetics.colors.upper')} onChange={(v) => set('cosmetics.colors.upper', v)} />
          <Text label="yellow start (mid)" value={g('cosmetics.scale.mid_range_start')} onChange={(v) => set('cosmetics.scale.mid_range_start', v)} />
          <Text label="red start (upper)" value={g('cosmetics.scale.upper_range')} onChange={(v) => set('cosmetics.scale.upper_range', v)} />
          <div style={{ fontSize: 10, color: '#777', margin: '6px 0 2px' }}>— ticks —</div>
          <Slider label="sub ticks" min={0} max={10} step={1} value={g(SO + 'sub_ticks') ?? 5} onChange={(v) => set(SO + 'sub_ticks', v)} />
          <Slider label="tick length" min={0} max={30} step={1} value={g(SO + 'tick_length') ?? 8} onChange={(v) => set(SO + 'tick_length', v)} />
          <Slider label="sub-tick length" min={0} max={20} step={1} value={g(SO + 'sub_tick_length') ?? 4} onChange={(v) => set(SO + 'sub_tick_length', v)} />
          <Slider label="tick radius offset" min={-30} max={30} step={1} value={g(SO + 'tick_radius_offset') ?? 0} onChange={(v) => set(SO + 'tick_radius_offset', v)} />
          <div style={{ fontSize: 10, color: '#777', margin: '6px 0 2px' }}>— numbers —</div>
          <Toggle label="scale numbers" value={g(SO + 'Scale_numbers') !== false} onChange={(v) => set(SO + 'Scale_numbers', v)} />
          <Slider label="number radius offset" min={0} max={50} step={1} value={g(SO + 'label_radius_offset') ?? 20} onChange={(v) => set(SO + 'label_radius_offset', v)} />
        </Section>

        <Section title="🧭 Tilt & motion">
          <Slider label="center angle" min={0} max={360} step={1} value={g(SO + 'Meter_center_angle') ?? 90} onChange={(v) => set(SO + 'Meter_center_angle', v)} />
          <Slider label="viewable angle" min={10} max={359} step={1} value={g(SO + 'Meter_viewable_angle') ?? 90} onChange={(v) => set(SO + 'Meter_viewable_angle', v)} />
          <Toggle label="counter-clockwise" value={!!g(SO + 'Counter_Clockwise')} onChange={(v) => set(SO + 'Counter_Clockwise', v)} />
        </Section>

        <Section title="📐 Geometry & offsets">
          <Slider label="scootch ←→ (pivot x)" min={-100} max={100} step={1} value={g(SO + 'pivot_offset_x') ?? 0} onChange={(v) => set(SO + 'pivot_offset_x', v)} />
          <Slider label="scootch ↑↓ (pivot y)" min={-100} max={100} step={1} value={g(SO + 'pivot_offset_y') ?? 0} onChange={(v) => set(SO + 'pivot_offset_y', v)} />
          <Slider label="meter scale (vs bezel)" min={0.2} max={3} step={0.05} value={g(SO + 'meter_scale') ?? 1} onChange={(v) => set(SO + 'meter_scale', v)} />
          <Slider label="arc radius offset" min={-60} max={60} step={1} value={g(SO + 'arc_radius_offset') ?? 0} onChange={(v) => set(SO + 'arc_radius_offset', v)} />
          <Slider label="pivot crop % (push down)" min={0} max={200} step={5} value={g(SO + 'pivot_crop') ?? 0} onChange={(v) => set(SO + 'pivot_crop', v)} />
        </Section>
      </div>
    );
  };

  window.OaDesigner_NeedleMeter = Designer;
  window.OaDesignerRegistry = window.OaDesignerRegistry || {};
  TYPES.forEach((t) => { window.OaDesignerRegistry[t] = Designer; });
})();
