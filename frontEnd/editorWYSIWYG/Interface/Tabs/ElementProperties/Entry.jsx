/**
 * Interface/Tabs/ElementProperties/Entry.jsx — schema-driven property inspector.
 * Mirrors oaGuiEditorWYSIWYG/Interface/Tabs/ElementProperties/Entry.py
 * (+ structural/layout mixins): rename, reorder, duplicate, delete, and the
 * recursive property tree for the focused element.
 */
(function () {
  // Path of the collection (parent) that holds `path`, or null for the root.
  const ownerOf = (path) => {
    const parts = String(path).split('.');
    if (parts.length <= 1) return null;
    const key = parts.pop();
    if (parts[parts.length - 1] === 'fields' || parts[parts.length - 1] === 'blocks') parts.pop();
    return { ownerPath: parts.join('.'), key };
  };

  const btn = (extra) => ({
    background: '#2a2a2a', color: '#ddd', border: '1px solid #444', borderRadius: 3,
    fontSize: 11, padding: '3px 8px', cursor: 'pointer', ...extra,
  });

  // Properties view for a clicked Library item (not yet on the canvas). Renders the
  // item's editable draft + a draggable "Add to Canvas" handle. Edits go to the
  // store's libraryItem draft via a shim store; dropping the handle on the canvas
  // (interactive_layout onDrop) inserts the (edited) schema.
  const LibraryItemPanel = ({ store, item }) => {
    const schema = item.schema || {};
    const libShim = React.useMemo(() => ({
      setProp: (_basePath, key, value) => store.setLibraryProp(key, value),
      getNode: () => schema,
    }), [store, schema]);
    const onDragStart = (e) =>
      e.dataTransfer.setData('application/json', JSON.stringify({ name: item.name, schema }));
    return (
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        <div style={{ padding: 8, borderBottom: '1px solid #333', flexShrink: 0 }}>
          <div style={{ fontSize: 11, color: '#FF9900', fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: 1 }}>Library Item</div>
          <div style={{ fontSize: 18, color: '#fff', fontWeight: 'bold', margin: '4px 0' }}>{schema.type || 'element'}</div>
          <div style={{ fontSize: 12, color: '#aaa', wordBreak: 'break-all' }}>{item.name}</div>
          <div draggable onDragStart={onDragStart}
            title="Drag onto the canvas to place this item"
            style={{ marginTop: 10, padding: '8px 10px', background: '#3a2f12', color: '#FF9900',
              border: '1px dashed #FF9900', borderRadius: 4, fontSize: 12, fontWeight: 'bold',
              textAlign: 'center', cursor: 'grab', userSelect: 'none' }}>
            ➕ Add library item to Canvas — drag me ⤵
          </div>
          <button style={{ ...btn(), marginTop: 6, width: '100%' }} onClick={() => store.clearLibraryItem()}>✕ Close</button>
        </div>
        <div style={{ flex: 1, minHeight: 0, overflow: 'auto' }}>
          <window.OaEdPropertyTree node={schema} basePath="" store={libShim} />
        </div>
      </div>
    );
  };

  window.OaEdProperties = ({ store }) => {
    const st = window.useEditorStore(store);

    // Load library data once: enum legends (dropdowns) + composite reference
    // schemas (full knob/fader/value param sets merged into sub-configs).
    const [, setLibReady] = React.useState(0);
    React.useEffect(() => {
      const bump = () => setLibReady((x) => x + 1);
      if (window.OaEdEnum) window.OaEdEnum.load().then(bump).catch(() => {});
      if (window.OaEdComposite) window.OaEdComposite.load().then(bump).catch(() => {});
    }, []);

    // A clicked Library item takes over the panel until it's placed or closed.
    if (st.libraryItem) return <LibraryItemPanel store={store} item={st.libraryItem} />;

    const path = st.selectedPath;
    const node = path ? store.getNode(path) : null;

    if (!node || typeof node !== 'object') {
      return <div style={{ color: '#777', fontSize: 12, padding: 14 }}>Select an element on the canvas or in the tree.</div>;
    }

    const owner = ownerOf(path);
    const key = owner ? owner.key : path;

    const onRename = (e) => {
      const v = e.target.value.trim();
      if (v && v !== key) store.rename(path, v);
    };
    const duplicate = () => {
      if (!owner) return;
      store.insert(owner.ownerPath, node, key);
    };

    return (
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        {/* header */}
        <div style={{ padding: 8, borderBottom: '1px solid #333', flexShrink: 0 }}>
          <div style={{ fontSize: 20, color: '#fff', fontWeight: 'bold', marginBottom: 6 }}>{node.type || 'element'}</div>
          <input defaultValue={key} key={path} onBlur={onRename}
            onKeyDown={(e) => { if (e.key === 'Enter') e.target.blur(); }}
            style={{ width: '100%', boxSizing: 'border-box', background: '#111', color: '#FF9900',
              border: '1px solid #333', borderRadius: 3, padding: '4px 6px', fontSize: 13, fontWeight: 'bold' }} />
          <div style={{ fontSize: 9, color: '#555', marginTop: 4, wordBreak: 'break-all' }}>{path}</div>
          <div style={{ display: 'flex', gap: 5, marginTop: 8, flexWrap: 'wrap' }}>
            <button style={btn()} onClick={() => store.reorder(path, -1)} title="Move up">↑</button>
            <button style={btn()} onClick={() => store.reorder(path, +1)} title="Move down">↓</button>
            <button style={btn()} onClick={duplicate} disabled={!owner} title="Duplicate">⧉ Dup</button>
            <button style={btn({ borderColor: '#a33', color: '#f88' })} onClick={() => store.deleteNode(path)} title="Delete">✕ Del</button>
          </div>
        </div>

        {/* property tree */}
        <div style={{ flex: 1, minHeight: 0, overflow: 'auto' }}>
          <window.OaEdPropertyTree node={node} basePath={path} store={store} />
        </div>
      </div>
    );
  };
})();
