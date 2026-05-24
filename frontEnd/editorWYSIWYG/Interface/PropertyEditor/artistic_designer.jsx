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

  // ---- reusable artistic inputs -------------------------------------------
  const row = { display: 'flex', alignItems: 'center', gap: 8, margin: '5px 0' };
  const lab = { flex: '0 0 38%', fontSize: 11, color: '#bbb', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' };
  const numBox = { width: 56, background: '#111', color: '#eee', border: '1px solid #333', borderRadius: 3, fontSize: 11, padding: '2px 4px', textAlign: 'right' };

  const Color = ({ label, value, onChange }) => (
    <div style={row}>
      <span style={lab} title={label}>{label}</span>
      <input type="color" value={(value || '#000000').slice(0, 7)}
        onChange={(e) => onChange(e.target.value)}
        style={{ width: 30, height: 24, padding: 0, border: '1px solid #333', background: '#111', cursor: 'pointer', borderRadius: 3 }} />
      <input type="text" value={value == null ? '' : value} onChange={(e) => onChange(e.target.value)}
        style={{ flex: 1, minWidth: 0, ...numBox, textAlign: 'left', width: 'auto' }} />
    </div>
  );

  const Slider = ({ label, value, min, max, step, onChange }) => {
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
        <span style={lab} title={label}>{label}</span>
        <input type="range" min={lo} max={hi} step={st} value={safe}
          onChange={(e) => onChange(parseFloat(e.target.value))}
          style={{ flex: 1, minWidth: 0, accentColor: A }} />
        <input type="number" value={safe} step={st}
          onChange={(e) => { const n = parseFloat(e.target.value); if (!Number.isNaN(n)) onChange(n); }}
          style={numBox} />
      </div>
    );
  };

  const Toggle = ({ label, value, onChange }) => (
    <div style={row}>
      <span style={lab} title={label}>{label}</span>
      <button onClick={() => onChange(!value)}
        style={{ width: 42, height: 22, borderRadius: 11, border: '1px solid #444', cursor: 'pointer',
          background: value ? A : '#333', position: 'relative', transition: 'background .15s' }}>
        <span style={{ position: 'absolute', top: 2, left: value ? 22 : 2, width: 16, height: 16,
          borderRadius: '50%', background: '#fff', transition: 'left .15s' }} />
      </button>
    </div>
  );

  const Enum = ({ label, value, options, onChange }) => {
    const list = options.includes(value) ? options : [value, ...options];
    return (
      <div style={row}>
        <span style={lab} title={label}>{label}</span>
        <select value={value == null ? '' : value} onChange={(e) => onChange(e.target.value)}
          style={{ flex: 1, minWidth: 0, background: '#111', color: '#eee', border: '1px solid #333', borderRadius: 3, fontSize: 11, padding: '3px 4px', cursor: 'pointer' }}>
          {list.map((o) => <option key={String(o)} value={o}>{String(o)}</option>)}
        </select>
      </div>
    );
  };

  const Text = ({ label, value, onChange }) => (
    <div style={row}>
      <span style={lab} title={label}>{label}</span>
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
  const Auto = ({ label, keyPath, value, onChange }) => {
    const opts = window.OaEdEnum ? window.OaEdEnum.optionsFor(keyPath) : null;
    if (typeof value === 'boolean') return <Toggle label={label} value={value} onChange={onChange} />;
    if (opts && opts.length && typeof value !== 'number') return <Enum label={label} value={value} options={opts} onChange={onChange} />;
    if (isHex(value) || /colou?r$/i.test(label)) return <Color label={label} value={value} onChange={onChange} />;
    if (typeof value === 'number') return <Slider label={label} value={value} onChange={onChange} />;
    return <Text label={label} value={value} onChange={onChange} />;
  };

  window.OaEdArtisticCtl = { Color, Slider, Toggle, Enum, Text, Section, Auto, isHex, ACCENT: A };

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

  const Group = ({ obj, basePath, setProp, depth }) => {
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
          <Auto key={path} label={k} keyPath={path} value={v} onChange={(nv) => setProp(path, nv)} />
        ))}
        {groups.map(([k, v, path]) => (
          <Section key={path} title={k} defaultOpen={depth < 1}>
            <Group obj={v} basePath={path} setProp={setProp} depth={depth + 1} />
          </Section>
        ))}
      </>
    );
  };

  window.OaEdArtisticGeneric = ({ store, path, node, type }) => {
    // Full param set: library reference for this type, merged UNDER the instance
    // (instance values win, reference adds the rest) so every supported knob is
    // editable — pre-filled with the library default.
    const ref = (window.OaEdComposite && type) ? window.OaEdComposite.referenceForType(type) : null;
    const merged = ref ? window.OaEdComposite.merge(ref, node) : node;
    const setProp = (dotKey, value) => store.setProp(path, dotKey, value);
    return <Group obj={merged} basePath="" setProp={setProp} depth={0} />;
  };

  // ---- pop-out host (modal) ------------------------------------------------
  const hdrBtn = (extra) => ({ border: '1px solid #444', borderRadius: 4, fontSize: 12, padding: '5px 12px', cursor: 'pointer', fontWeight: 'bold', ...extra });

  window.OaEdArtisticDesigner = ({ store, path, node, type, onClose }) => {
    const Bespoke = (type && window.OaDesignerRegistry[type]) || null;
    const nodeKey = String(path || '').split('.').pop();
    // Snapshot the node ONCE on open so "Abort changes" can revert the session.
    const [original] = React.useState(() => { try { return JSON.parse(JSON.stringify(node)); } catch (e) { return node; } });
    const [msg, setMsg] = React.useState(null);

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
        <div style={{ width: '100%', height: '100%', background: '#161616',
          borderTop: `3px solid ${A}`, display: 'flex', flexDirection: 'column', overflow: 'hidden', boxShadow: '0 0 48px #000' }}>
          {/* header */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', borderBottom: '1px solid #333', flexShrink: 0 }}>
            <span style={{ fontSize: 13, fontWeight: 'bold', color: A, letterSpacing: 1 }}>⚡ ARTISTIC PROPERTIES</span>
            <span style={{ fontSize: 13, color: '#fff', fontWeight: 'bold' }}>{type}</span>
            <span style={{ fontSize: 10, color: '#666' }}>{Bespoke ? 'bespoke designer' : 'auto-generated from README'}</span>
            <span style={{ flex: 1 }} />
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
            <div style={{ flex: '1 1 55%', minWidth: 0, borderRight: '1px solid #333', background: '#0d0d0d', display: 'flex' }}>
              <Preview nodeKey={nodeKey} node={node} />
            </div>
            <div style={{ flex: '1 1 45%', minWidth: 320, overflow: 'auto', padding: '4px 12px 16px' }}>
              {Bespoke
                ? <Bespoke store={store} path={path} node={node} type={type} ctl={window.OaEdArtisticCtl} />
                : <window.OaEdArtisticGeneric store={store} path={path} node={node} type={type} />}
            </div>
          </div>
        </div>
      </div>
    );
  };
})();
