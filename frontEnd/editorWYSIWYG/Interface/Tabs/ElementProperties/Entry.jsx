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

  window.OaEdProperties = ({ store }) => {
    const st = window.useEditorStore(store);

    // Load the library enum legends once so property fields can become dropdowns.
    const [, setLegendsReady] = React.useState(0);
    React.useEffect(() => {
      if (window.OaEdEnum) window.OaEdEnum.load().then(() => setLegendsReady((x) => x + 1)).catch(() => {});
    }, []);

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
          <div style={{ fontSize: 10, color: '#888', marginBottom: 4 }}>{node.type || 'element'}</div>
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
