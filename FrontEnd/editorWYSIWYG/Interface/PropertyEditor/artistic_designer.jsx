/**
 * Interface/PropertyEditor/artistic_designer.jsx — the "ARTISTIC PROPERTIES"
 * builder: a pop-out, interactive widget designer that complements the flat
 * property tree. Toggled from the top of the Properties tab.
 *
 * Three pieces (all attach to window.*):
 *   - OaEdArtisticCtl  : reusable "artistic" inputs (color/slider/toggle/enum/text)
 *                        + Section, so BESPOKE per-widget designers can reuse them.
 *   - OaEdArtisticGeneric : README-driven auto-editor that works for ANY widget —
 *                        builds the full param set from the library reference
 *                        (OaEdComposite.referenceForType) merged with the instance,
 *                        and renders grouped artistic controls.
 *   - OaEdArtisticDesigner : the pop-out host (modal). Renders a LIVE preview of the
 *                        widget beside the controls. If a bespoke designer is
 *                        registered for the widget type in window.OaDesignerRegistry
 *                        (e.g. libControl/.../Designer.jsx), it is used; otherwise
 *                        the generic auto-editor is the fallback.
 *
 * Bespoke designers live PER WIDGET in libControl/<cat>/<Widget>/Designer.jsx and
 * self-register:  window.OaDesignerRegistry['<type>'] = MyDesignerComponent.
 * Every edit writes through the same store the property panel uses (store.setProp),
 * so the canvas + JSON + preview all stay in sync ("feeds back to the properties").
 */
(function () {
  // Per-type bespoke designer registry. Designer.jsx files self-register here.
  window.OaDesignerRegistry = window.OaDesignerRegistry || {};

  const A = '#FF9900';                      // accent
  const isHex = (v) => typeof v === 'string' && /^#([0-9a-f]{3,8})$/i.test(v);

  // What KIND of preview-overlay should clicking a property label trigger?
  //   'color' — flash the preview with the colour swatch
  //   'ruler' — overlay a px ruler matched to the value
  //   'flash' — generic pulsing accent border (everything else)
  const LEN_RE = /^(width|height|length|thickness|size|radius|offset|padx|pady|pad|gap|spacing|count|cap_scale|teeth|arc_width|sweep|outline_thickness)$/i;
  const classifyParam = (label, value) => {
    if (isHex(value) || /colou?r$/i.test(label || '')) return 'color';
    if (typeof value === 'number' && LEN_RE.test(label || '')) return 'ruler';
    return 'flash';
  };

  // ---- reusable artistic inputs -------------------------------------------
  const row = { display: 'flex', alignItems: 'center', gap: 8, margin: '5px 0' };
  const lab = { flex: '0 0 38%', fontSize: 11, color: '#bbb', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' };

  // Clickable label wrapper — invokes onLabelClick so the preview pane can
  // highlight, ruler, or flash the corresponding element.
  const Lab = ({ label, value, onLabelClick }) => (
    <span
      style={{ ...lab, cursor: onLabelClick ? 'pointer' : 'default', userSelect: 'none',
        textDecoration: onLabelClick ? 'underline dotted transparent' : 'none',
        textUnderlineOffset: 3, transition: 'color 0.15s, text-decoration-color 0.15s' }}
      onMouseEnter={(e) => onLabelClick && (e.currentTarget.style.color = A, e.currentTarget.style.textDecorationColor = A)}
      onMouseLeave={(e) => onLabelClick && (e.currentTarget.style.color = '#bbb', e.currentTarget.style.textDecorationColor = 'transparent')}
      onClick={onLabelClick ? () => onLabelClick(label, value) : undefined}
      title={onLabelClick ? `${label} — click to highlight in preview` : label}
    >{label}</span>
  );
  const numBox = { width: 56, background: '#111', color: '#eee', border: '1px solid #333', borderRadius: 3, fontSize: 11, padding: '2px 4px', textAlign: 'right' };

  const Color = ({ label, value, onChange, onLabelClick }) => (
    <div style={row}>
      <Lab label={label} value={value} onLabelClick={onLabelClick} />
      <input type="color" value={(value || '#000000').slice(0, 7)}
        onChange={(e) => onChange(e.target.value)}
        style={{ width: 30, height: 24, padding: 0, border: '1px solid #333', background: '#111', cursor: 'pointer', borderRadius: 3 }} />
      <input type="text" value={value == null ? '' : value} onChange={(e) => onChange(e.target.value)}
        style={{ flex: 1, minWidth: 0, ...numBox, textAlign: 'left', width: 'auto' }} />
    </div>
  );

  const Slider = ({ label, value, min, max, step, onChange, onLabelClick }) => {
    const v = Number(value);
    const safe = Number.isFinite(v) ? v : 0;
    // Heuristic range when none provided.
    let lo = min, hi = max;
    if (lo == null || hi == null) {
      if (safe >= 0 && safe <= 1) { lo = 0; hi = 1; }
      else { lo = safe < 0 ? safe * 2 : 0; hi = safe === 0 ? 100 : Math.abs(safe) * 3; }
    }
    const st = step != null ? step : ((hi - lo) / 100 || 1);
    return (
      <div style={row}>
        <Lab label={label} value={safe} onLabelClick={onLabelClick} />
        <input type="range" min={lo} max={hi} step={st} value={safe}
          onChange={(e) => onChange(parseFloat(e.target.value))}
          style={{ flex: 1, minWidth: 0, accentColor: A }} />
        <input type="number" value={safe} step={st}
          onChange={(e) => { const n = parseFloat(e.target.value); if (!Number.isNaN(n)) onChange(n); }}
          style={numBox} />
      </div>
    );
  };

  const Toggle = ({ label, value, onChange, onLabelClick }) => (
    <div style={row}>
      <Lab label={label} value={value} onLabelClick={onLabelClick} />
      <button onClick={() => onChange(!value)}
        style={{ width: 42, height: 22, borderRadius: 11, border: '1px solid #444', cursor: 'pointer',
          background: value ? A : '#333', position: 'relative', transition: 'background .15s' }}>
        <span style={{ position: 'absolute', top: 2, left: value ? 22 : 2, width: 16, height: 16,
          borderRadius: '50%', background: '#fff', transition: 'left .15s' }} />
      </button>
    </div>
  );

  const Enum = ({ label, value, options, onChange, onLabelClick }) => {
    const list = options.includes(value) ? options : [value, ...options];
    return (
      <div style={row}>
        <Lab label={label} value={value} onLabelClick={onLabelClick} />
        <select value={value == null ? '' : value} onChange={(e) => onChange(e.target.value)}
          style={{ flex: 1, minWidth: 0, background: '#111', color: '#eee', border: '1px solid #333', borderRadius: 3, fontSize: 11, padding: '3px 4px', cursor: 'pointer' }}>
          {list.map((o) => <option key={String(o)} value={o}>{String(o)}</option>)}
        </select>
      </div>
    );
  };

  const Text = ({ label, value, onChange, onLabelClick }) => (
    <div style={row}>
      <Lab label={label} value={value} onLabelClick={onLabelClick} />
      <input type="text" value={value == null ? '' : value} onChange={(e) => onChange(e.target.value)}
        style={{ flex: 1, minWidth: 0, background: '#111', color: '#eee', border: '1px solid #333', borderRadius: 3, fontSize: 11, padding: '2px 4px' }} />
    </div>
  );

  const Section = ({ title, accent, children, defaultOpen = true }) => {
    const [open, setOpen] = React.useState(defaultOpen);
    return (
      <div style={{ border: '1px solid #2c2c2c', borderRadius: 5, margin: '8px 0', overflow: 'hidden' }}>
        <div onClick={() => setOpen(!open)}
          style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '6px 8px', cursor: 'pointer',
            background: '#1d1d1d', color: accent || A, fontSize: 11, fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: 0.5 }}>
          <span style={{ fontSize: 9 }}>{open ? '▼' : '▶'}</span>{title}
        </div>
        {open && <div style={{ padding: '4px 8px 8px' }}>{children}</div>}
      </div>
    );
  };

  // One control, dispatched by value type + key name. `onChange` receives the value.
  const Auto = ({ label, keyPath, value, onChange, onLabelClick }) => {
    const opts = window.OaEdEnum ? window.OaEdEnum.optionsFor(keyPath) : null;
    if (typeof value === 'boolean') return <Toggle label={label} value={value} onChange={onChange} onLabelClick={onLabelClick} />;
    if (opts && opts.length && typeof value !== 'number') return <Enum label={label} value={value} options={opts} onChange={onChange} onLabelClick={onLabelClick} />;
    if (isHex(value) || /colou?r$/i.test(label)) return <Color label={label} value={value} onChange={onChange} onLabelClick={onLabelClick} />;
    if (typeof value === 'number') return <Slider label={label} value={value} onChange={onChange} onLabelClick={onLabelClick} />;
    return <Text label={label} value={value} onChange={onChange} onLabelClick={onLabelClick} />;
  };

  window.OaEdArtisticCtl = { Color, Slider, Toggle, Enum, Text, Section, Auto, Lab, isHex, classifyParam, ACCENT: A };

  // ---- live preview --------------------------------------------------------
  // Renders the actual widget from its (live-edited) node, like the palette does.
  const Preview = ({ nodeKey, node }) => {
    const layoutJson = React.useMemo(() => ({ [nodeKey || 'preview']: node }), [nodeKey, node]);
    return (
      <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'auto', padding: 16, boxSizing: 'border-box' }}>
        <div style={{ width: '100%', maxWidth: 700 }}>
          {window.LoaderOrchestrator
            ? <window.LoaderOrchestrator layoutJson={layoutJson} />
            : <div style={{ color: '#777' }}>preview unavailable</div>}
        </div>
      </div>
    );
  };
  window.OaEdArtisticPreview = Preview;

  // ---- generic README-driven auto-editor ----------------------------------
  // Walks the merged param tree and renders grouped artistic controls.
  const SKIP = new Set(['type', 'id', '_README', '_LEGEND', 'blocks', 'fields', 'options',
    'handler', 'yak_handler', 'AES70', 'identity', 'label', 'description', 'notes', 'column_spacing']);

  const Group = ({ obj, basePath, setProp, depth, onLabelClick }) => {
    const leaves = [], groups = [];
    for (const k of Object.keys(obj || {})) {
      if (SKIP.has(k)) continue;
      const v = obj[k];
      const path = basePath ? `${basePath}.${k}` : k;
      if (v && typeof v === 'object' && !Array.isArray(v)) groups.push([k, v, path]);
      else if (!Array.isArray(v)) leaves.push([k, v, path]);
    }
    return (
      <>
        {leaves.map(([k, v, path]) => (
          <Auto key={path} label={k} keyPath={path} value={v}
            onChange={(nv) => setProp(path, nv)}
            onLabelClick={onLabelClick ? (lbl, val) => onLabelClick(lbl, val, path) : undefined} />
        ))}
        {groups.map(([k, v, path]) => (
          <Section key={path} title={k} defaultOpen={depth < 1}>
            <Group obj={v} basePath={path} setProp={setProp} depth={depth + 1} onLabelClick={onLabelClick} />
          </Section>
        ))}
      </>
    );
  };

  window.OaEdArtisticGeneric = ({ store, path, node, type, onLabelClick }) => {
    // Full param set: library reference for this type, merged UNDER the instance
    // (instance values win, reference adds the rest) so every supported knob is
    // editable — pre-filled with the library default.
    const ref = (window.OaEdComposite && type) ? window.OaEdComposite.referenceForType(type) : null;
    const merged = ref ? window.OaEdComposite.merge(ref, node) : node;
    const setProp = (dotKey, value) => store.setProp(path, dotKey, value);
    return <Group obj={merged} basePath="" setProp={setProp} depth={0} onLabelClick={onLabelClick} />;
  };

  // Universal transparency control shown for EVERY element (bespoke or generic),
  // so any widget can be made see-through over the panel. Writes the keys the
  // transparency manager (window.OaTransparency) reads.
  window.OaEdTransparencyControls = ({ store, path, node, onLabelClick }) => {
    const ctl = window.OaEdArtisticCtl || {};
    const { Section, Toggle, Slider } = ctl;
    if (!Section || !Toggle || !Slider) return null;
    const getAt = (o, dot) => { let n = o; for (const k of String(dot).split('.')) { if (n == null) return undefined; n = n[k]; } return n; };
    const set = (dot, v) => store.setProp(path, dot, v);
    const op = getAt(node, 'cosmetics.bg_opacity');
    const lc = (dot) => onLabelClick ? (lbl, val) => onLabelClick(lbl, val, dot) : undefined;
    return (
      <Section title="🫥 Transparency" defaultOpen={false}>
        <Toggle label="transparent" value={!!getAt(node, 'cosmetics.transparent')} onChange={(v) => set('cosmetics.transparent', v)} onLabelClick={lc('cosmetics.transparent')} />
        <Slider label="bg opacity" min={0} max={1} step={0.05} value={op != null ? op : 1} onChange={(v) => set('cosmetics.bg_opacity', v)} onLabelClick={lc('cosmetics.bg_opacity')} />
      </Section>
    );
  };

  // ---- highlight overlay (click a property label → flash/ruler/colour) -----
  // Renders absolutely over the preview pane. `kind` decides the shape:
  //   'color' → big colour bloom + label badge
  //   'ruler' → top-edge ruler with the value tick called out
  //   'flash' → pulsing accent border + value badge
  const HighlightOverlay = ({ highlight }) => {
    if (!highlight) return null;
    const { kind, label, value, path, nonce } = highlight;
    const colour = kind === 'color' && typeof value === 'string' ? value : A;
    const valTxt = value == null ? '' : (typeof value === 'number' ? Math.round(value * 1000) / 1000 : String(value));
    const badge = (
      <div key={`badge-${nonce}`} style={{
        position: 'absolute', top: 12, left: 12, padding: '6px 10px', borderRadius: 6,
        background: 'rgba(0,0,0,0.78)', border: `2px solid ${colour}`, color: '#fff',
        fontSize: 11, fontFamily: 'monospace', letterSpacing: 0.5, pointerEvents: 'none',
        boxShadow: `0 0 24px ${colour}`, animation: 'oa-hl-pop 0.4s ease-out',
      }}>
        <div style={{ color: colour, fontWeight: 'bold', textTransform: 'uppercase', fontSize: 10 }}>
          {kind === 'color' ? '🎨 colour' : kind === 'ruler' ? '📏 length' : '⚡ property'}
        </div>
        <div>{path || label}</div>
        <div style={{ color: '#aaa' }}>= {valTxt}</div>
      </div>
    );

    if (kind === 'color') {
      return (
        <div key={`hl-${nonce}`} style={{ position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 10 }}>
          <div style={{ position: 'absolute', inset: 0, border: `4px solid ${colour}`,
            boxShadow: `inset 0 0 80px ${colour}`, animation: 'oa-hl-flash 1.4s ease-in-out 2' }} />
          <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
            width: 96, height: 96, borderRadius: '50%', background: colour, border: '3px solid #fff',
            boxShadow: '0 8px 32px rgba(0,0,0,0.6)', animation: 'oa-hl-flash 1.4s ease-in-out 2' }} />
          {badge}
        </div>
      );
    }
    if (kind === 'ruler') {
      // Map value visually onto the ruler: if 0-1 use that, else fit value within a 0..max range.
      const v = Number(value) || 0;
      const max = v <= 1 ? 1 : (v <= 100 ? 100 : v * 1.2);
      const pct = Math.max(0, Math.min(1, v / max)) * 100;
      const ticks = [];
      for (let i = 0; i <= 10; i++) ticks.push(i * 10);
      return (
        <div key={`hl-${nonce}`} style={{ position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 10 }}>
          {/* Top ruler */}
          <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 28,
            background: 'rgba(20,20,20,0.92)', borderBottom: `2px solid ${colour}`,
            animation: 'oa-hl-slide-down 0.3s ease-out' }}>
            {ticks.map((t) => (
              <div key={t} style={{ position: 'absolute', left: `${t}%`, top: 0, bottom: 0,
                borderLeft: '1px solid #666', width: 1 }}>
                <span style={{ position: 'absolute', top: 2, left: 3, fontSize: 9, color: '#999', fontFamily: 'monospace' }}>{t}</span>
              </div>
            ))}
            {/* The value tick */}
            <div style={{ position: 'absolute', left: `${pct}%`, top: 0, bottom: -8, width: 2,
              background: colour, boxShadow: `0 0 8px ${colour}` }} />
            <div style={{ position: 'absolute', left: `${pct}%`, bottom: -28, transform: 'translateX(-50%)',
              padding: '2px 6px', background: colour, color: '#000', fontSize: 10, fontWeight: 'bold',
              fontFamily: 'monospace', borderRadius: 2 }}>{valTxt}</div>
          </div>
          {/* Pulsing target ring centred on preview */}
          <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
            width: 220, height: 220, border: `3px dashed ${colour}`, borderRadius: '50%',
            animation: 'oa-hl-pulse 1.2s ease-in-out 2' }} />
          {badge}
        </div>
      );
    }
    // 'flash' — generic blink
    return (
      <div key={`hl-${nonce}`} style={{ position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 10 }}>
        <div style={{ position: 'absolute', inset: 8, border: `3px solid ${colour}`, borderRadius: 6,
          animation: 'oa-hl-flash 0.7s ease-in-out 3' }} />
        <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
          fontSize: 56, animation: 'oa-hl-pulse 0.8s ease-in-out 2' }}>👇</div>
        {badge}
      </div>
    );
  };

  // ---- pop-out host (modal) ------------------------------------------------
  const hdrBtn = (extra) => ({ border: '1px solid #444', borderRadius: 4, fontSize: 12, padding: '5px 12px', cursor: 'pointer', fontWeight: 'bold', ...extra });

  // Inject CSS keyframes once.
  const KEYFRAMES = `
    @keyframes oa-hl-flash { 0%, 100% { opacity: 1; } 50% { opacity: 0.25; } }
    @keyframes oa-hl-pulse { 0% { transform: translate(-50%, -50%) scale(0.85); opacity: 0; }
                             40% { transform: translate(-50%, -50%) scale(1); opacity: 1; }
                             100% { transform: translate(-50%, -50%) scale(1.25); opacity: 0; } }
    @keyframes oa-hl-pop { 0% { transform: translateY(-8px); opacity: 0; } 100% { transform: translateY(0); opacity: 1; } }
    @keyframes oa-hl-slide-down { from { transform: translateY(-100%); } to { transform: translateY(0); } }
  `;

  window.OaEdArtisticDesigner = ({ store, path, node, type, onClose }) => {
    const Bespoke = (type && window.OaDesignerRegistry[type]) || null;
    const nodeKey = String(path || '').split('.').pop();
    // Snapshot the node ONCE on open so "Abort changes" can revert the session.
    const [original] = React.useState(() => { try { return JSON.parse(JSON.stringify(node)); } catch (e) { return node; } });
    const [msg, setMsg] = React.useState(null);

    // ---- click-to-highlight state ------------------------------------------
    // A label click sets this; the overlay watches it and auto-clears after 2.5s.
    const [highlight, setHighlight] = React.useState(null);
    const hlTimerRef = React.useRef(null);
    const triggerHighlight = (label, value, pathDot) => {
      const kind = classifyParam(label, value);
      if (hlTimerRef.current) clearTimeout(hlTimerRef.current);
      // Bump a nonce so identical-payload re-clicks still restart the animation.
      setHighlight({ kind, label, value, path: pathDot, nonce: Date.now() });
      hlTimerRef.current = setTimeout(() => setHighlight(null), 2500);
    };
    React.useEffect(() => () => { if (hlTimerRef.current) clearTimeout(hlTimerRef.current); }, []);

    const abort = () => { store.setNode(path, original); onClose && onClose(); };

    const saveFile = async () => {
      try {
        const fp = store.getState ? store.getState().filePath : null;
        if (!window.OaEdFileWriter) { setMsg({ ok: false, text: 'No file writer' }); }
        else if (fp) {
          const r = await window.OaEdFileWriter.save(fp, store.getData());
          if (r.ok) { store.markSaved && store.markSaved(); setMsg({ ok: true, text: 'Saved' + (r.backup ? ` · backup ${r.backup}` : '') }); }
          else setMsg({ ok: false, text: r.error || 'Save failed' });
        } else {
          window.OaEdFileWriter.download((nodeKey || 'widget') + '.json', store.getData());
          setMsg({ ok: true, text: 'Downloaded' });
        }
      } catch (e) { setMsg({ ok: false, text: String((e && e.message) || e) }); }
      setTimeout(() => setMsg(null), 4000);
    };

    return (
      <div style={{ position: 'fixed', inset: 0, zIndex: 4000, background: 'rgba(0,0,0,0.78)', display: 'flex', boxSizing: 'border-box' }}>
        <style>{KEYFRAMES}</style>
        <div style={{ width: '100%', height: '100%', background: '#161616',
          borderTop: `3px solid ${A}`, display: 'flex', flexDirection: 'column', overflow: 'hidden', boxShadow: '0 0 48px #000' }}>
          {/* header */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', borderBottom: '1px solid #333', flexShrink: 0 }}>
            <span style={{ fontSize: 13, fontWeight: 'bold', color: A, letterSpacing: 1 }}>⚡ ARTISTIC PROPERTIES</span>
            <span style={{ fontSize: 13, color: '#fff', fontWeight: 'bold' }}>{type}</span>
            <span style={{ fontSize: 10, color: '#666' }}>{Bespoke ? 'bespoke designer' : 'auto-generated from README'}</span>
            <span style={{ flex: 1 }} />
            <span style={{ fontSize: 10, color: '#888', fontStyle: 'italic' }}>💡 click any property name to flash it in the preview</span>
            {msg && <span style={{ fontSize: 11, color: msg.ok ? '#6c6' : '#f66' }}>{msg.ok ? '✓ ' : '⚠ '}{msg.text}</span>}
            <button onClick={abort} title="Discard all changes made in this session and close"
              style={hdrBtn({ background: '#2a1414', color: '#f88', borderColor: '#a33' })}>⟲ Abort changes</button>
            <button onClick={saveFile} title="Write the current document to its file (with backup)"
              style={hdrBtn({ background: 'linear-gradient(180deg,#39b54a,#2a8a39)', color: '#fff', borderColor: '#2a8a39' })}>💾 Save changes as file</button>
            <button onClick={onClose} title="Keep changes in the editor and close"
              style={hdrBtn({ background: '#2a2a2a', color: '#ddd' })}>✓ Done</button>
          </div>
          {/* body: preview | controls */}
          <div style={{ flex: 1, minHeight: 0, display: 'flex' }}>
            <div style={{ flex: '1 1 55%', minWidth: 0, borderRight: '1px solid #333', background: '#0d0d0d', display: 'flex', position: 'relative' }}>
              <Preview nodeKey={nodeKey} node={node} />
              <HighlightOverlay highlight={highlight} />
            </div>
            <div style={{ flex: '1 1 45%', minWidth: 320, overflow: 'auto', padding: '4px 12px 16px' }}>
              <window.OaEdTransparencyControls store={store} path={path} node={node} onLabelClick={triggerHighlight} />
              {Bespoke
                ? <Bespoke store={store} path={path} node={node} type={type} ctl={window.OaEdArtisticCtl} onLabelClick={triggerHighlight} />
                : <window.OaEdArtisticGeneric store={store} path={path} node={node} type={type} onLabelClick={triggerHighlight} />}
            </div>
          </div>
        </div>
      </div>
    );
  };
})();
