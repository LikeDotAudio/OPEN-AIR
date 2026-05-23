/**
 * Interface/Tabs/GrabBagView/grab_bag_view.jsx — categorized widget palette
 * with LIVE widget previews. Mirrors oaGuiEditorWYSIWYG/.../grab_bag_view.py.
 *
 * Each template is rendered through the runtime renderer (LoaderOrchestrator),
 * scaled into a thumbnail. Previews are lazy-mounted (IntersectionObserver) and
 * wrapped in an error boundary so a heavy/broken widget can't stall or crash the
 * palette. Drag a chip onto the canvas, or click to insert into the selection.
 */
(function () {
  const CHIP_W = 150;
  const PREV_H = 86;
  const SCALE = 0.5;

  // Render error isolation — a bad template falls back to a type badge.
  class PreviewBoundary extends React.Component {
    constructor(p) { super(p); this.state = { err: false }; }
    static getDerivedStateFromError() { return { err: true }; }
    componentDidCatch() { /* swallow — fallback shown */ }
    render() { return this.state.err ? this.props.fallback : this.props.children; }
  }

  const useInView = (ref) => {
    const [inView, setInView] = React.useState(false);
    React.useEffect(() => {
      const el = ref.current;
      if (!el || typeof IntersectionObserver === 'undefined') { setInView(true); return; }
      const obs = new IntersectionObserver(([e]) => {
        if (e.isIntersecting) { setInView(true); obs.disconnect(); }
      }, { rootMargin: '120px' });
      obs.observe(el);
      return () => obs.disconnect();
    }, [ref]);
    return inView;
  };

  const TypeBadge = ({ type }) => (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#666', fontSize: 10, fontFamily: 'monospace', padding: 4, textAlign: 'center' }}>
      {type}
    </div>
  );

  const WidgetPreview = ({ comp }) => {
    const ref = React.useRef(null);
    const inView = useInView(ref);
    const layoutJson = React.useMemo(() => ({ [comp.name]: comp.schema }), [comp]);
    return (
      <div ref={ref} style={{ width: CHIP_W, height: PREV_H, overflow: 'hidden', position: 'relative', background: '#161616', borderBottom: '1px solid #333' }}>
        <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
          {inView && window.LoaderOrchestrator ? (
            <PreviewBoundary fallback={<TypeBadge type={comp.type} />}>
              <div style={{ transform: `scale(${SCALE})`, transformOrigin: 'top left', width: CHIP_W / SCALE, height: PREV_H / SCALE }}>
                <window.LoaderOrchestrator layoutJson={layoutJson} />
              </div>
            </PreviewBoundary>
          ) : <TypeBadge type={comp.type} />}
        </div>
      </div>
    );
  };

  window.OaEdGrabBag = ({ store }) => {
    const st = window.useEditorStore(store);
    const [groups, setGroups] = React.useState(null);
    const [error, setError] = React.useState(null);
    const [filter, setFilter] = React.useState('');
    const [showPreviews, setShowPreviews] = React.useState(true);

    const load = React.useCallback((force) => {
      window.OaEdGrabBagLoader.load(force)
        .then((data) => setGroups(window.OaEdGrabBagLoader.byCategory(data.components)))
        .catch((e) => setError(e.message));
    }, []);

    React.useEffect(() => { load(false); }, [load]);

    // Clicking a palette item no longer auto-inserts — it loads the item into the
    // Properties panel (as an editable draft) where an "Add to Canvas" drag handle
    // places it. Dragging a chip straight onto the canvas still works too.
    const selectForProps = (comp) => store.selectLibraryItem(comp);

    const dragStart = (e, comp) =>
      e.dataTransfer.setData('application/json', JSON.stringify({ name: comp.name, schema: comp.schema }));

    if (error) return <div style={{ color: '#f66', fontSize: 11, padding: 10 }}>Palette error: {error}</div>;
    if (!groups) return <div style={{ color: '#888', fontSize: 11, padding: 10 }}>Loading palette…</div>;

    const q = filter.toLowerCase();

    return (
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        <div style={{ display: 'flex', gap: 6, padding: 6, borderBottom: '1px solid #333', flexShrink: 0, alignItems: 'center' }}>
          <input placeholder="filter…" value={filter} onChange={(e) => setFilter(e.target.value)}
            style={{ flex: 1, minWidth: 0, background: '#111', color: '#eee', border: '1px solid #333', borderRadius: 3, padding: '3px 6px', fontSize: 11 }} />
          <button onClick={() => setShowPreviews(!showPreviews)} title="Toggle live previews"
            style={{ background: showPreviews ? '#3a2f12' : '#2a2a2a', color: showPreviews ? '#FF9900' : '#ddd', border: '1px solid #444', borderRadius: 3, fontSize: 11, cursor: 'pointer', padding: '0 6px' }}>👁</button>
          <button onClick={() => load(true)} title="Refresh"
            style={{ background: '#2a2a2a', color: '#ddd', border: '1px solid #444', borderRadius: 3, fontSize: 11, cursor: 'pointer', padding: '0 6px' }}>⟳</button>
        </div>

        <div style={{ flex: 1, minHeight: 0, overflow: 'auto', padding: 6 }}>
          {Object.entries(groups).map(([cat, comps]) => {
            const shown = comps.filter((c) => !q || c.name.toLowerCase().includes(q) || c.type.toLowerCase().includes(q) || cat.toLowerCase().includes(q));
            if (!shown.length) return null;
            return (
              <div key={cat} style={{ marginBottom: 10 }}>
                <div style={{ fontSize: 10, color: '#cca35a', fontWeight: 'bold', textTransform: 'uppercase', margin: '4px 0' }}>{cat}</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {shown.map((c, i) => (
                    <div key={c.name + i}
                      draggable
                      onDragStart={(e) => dragStart(e, c)}
                      onClick={() => selectForProps(c)}
                      title={`${c.type} — click to inspect in Properties, or drag onto the canvas`}
                      style={{ width: CHIP_W, border: (st.libraryItem && st.libraryItem.name === c.name) ? '1px solid #FF9900' : '1px solid #3a3a3a', borderRadius: 4, overflow: 'hidden', cursor: 'grab', background: (st.libraryItem && st.libraryItem.name === c.name) ? '#2a2410' : '#222' }}>
                      {showPreviews
                        ? <WidgetPreview comp={c} />
                        : <div style={{ height: 4 }} />}
                      <div style={{ padding: '4px 6px' }}>
                        <div style={{ fontSize: 11, fontWeight: 'bold', color: '#ddd', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{c.name}</div>
                        <div style={{ fontSize: 9, color: '#777', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{c.type}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };
})();
