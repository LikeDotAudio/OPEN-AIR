/**
 * Interface/Tabs/GrabBagView/grab_bag_view.jsx — categorized widget palette.
 * Mirrors oaGuiEditorWYSIWYG/Interface/Tabs/GrabBagView/grab_bag_view.py.
 *
 * Loads templates from /api/grabbag (oaGuiElements sample.json). Drag a chip
 * onto the canvas to add it, or click to insert into the selected container.
 */
(function () {
  window.OaEdGrabBag = ({ store }) => {
    const st = window.useEditorStore(store);
    const [groups, setGroups] = React.useState(null);
    const [error, setError] = React.useState(null);
    const [filter, setFilter] = React.useState('');

    const load = React.useCallback((force) => {
      window.OaEdGrabBagLoader.load(force)
        .then((data) => setGroups(window.OaEdGrabBagLoader.byCategory(data.components)))
        .catch((e) => setError(e.message));
    }, []);

    React.useEffect(() => { load(false); }, [load]);

    // Insert into the selected container (or the block owning the selected field).
    const insertSelected = (comp) => {
      const sel = st.selectedPath;
      const target = window.OaEdCanvas.containerPathOf(store, sel);
      store.insert(target, comp.schema, comp.name);
    };

    if (error) return <div style={{ color: '#f66', fontSize: 11, padding: 10 }}>Palette error: {error}</div>;
    if (!groups) return <div style={{ color: '#888', fontSize: 11, padding: 10 }}>Loading palette…</div>;

    const q = filter.toLowerCase();

    return (
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        <div style={{ display: 'flex', gap: 6, padding: 6, borderBottom: '1px solid #333', flexShrink: 0 }}>
          <input placeholder="filter…" value={filter} onChange={(e) => setFilter(e.target.value)}
            style={{ flex: 1, minWidth: 0, background: '#111', color: '#eee', border: '1px solid #333', borderRadius: 3, padding: '3px 6px', fontSize: 11 }} />
          <button onClick={() => load(true)} title="Refresh"
            style={{ background: '#2a2a2a', color: '#ddd', border: '1px solid #444', borderRadius: 3, fontSize: 11, cursor: 'pointer' }}>⟳</button>
        </div>
        <div style={{ flex: 1, minHeight: 0, overflow: 'auto', padding: 6 }}>
          {Object.entries(groups).map(([cat, comps]) => {
            const shown = comps.filter((c) => !q || c.name.toLowerCase().includes(q) || c.type.toLowerCase().includes(q) || cat.toLowerCase().includes(q));
            if (!shown.length) return null;
            return (
              <div key={cat} style={{ marginBottom: 8 }}>
                <div style={{ fontSize: 10, color: '#cca35a', fontWeight: 'bold', textTransform: 'uppercase', margin: '4px 0' }}>{cat}</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
                  {shown.map((c, i) => (
                    <div key={c.name + i}
                      draggable
                      onDragStart={(e) => e.dataTransfer.setData('application/json', JSON.stringify({ name: c.name, schema: c.schema }))}
                      onClick={() => insertSelected(c)}
                      title={`${c.type} — drag to canvas or click to insert into selection`}
                      style={{
                        background: '#252525', border: '1px solid #3a3a3a', borderRadius: 4,
                        padding: '5px 8px', fontSize: 11, color: '#ddd', cursor: 'grab', maxWidth: 130,
                        overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                      }}>
                      <div style={{ fontWeight: 'bold', overflow: 'hidden', textOverflow: 'ellipsis' }}>{c.name}</div>
                      <div style={{ fontSize: 9, color: '#777' }}>{c.type}</div>
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
