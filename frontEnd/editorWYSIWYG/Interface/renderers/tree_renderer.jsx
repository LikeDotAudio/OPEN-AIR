/**
 * Interface/renderers/tree_renderer.jsx — recursive property-tree renderer.
 * Mirrors oaGuiEditorWYSIWYG/Interface/renderers/tree_renderer.py.
 *
 * Renders editable controls for a node's own properties, recursing into nested
 * objects/arrays. Structural children (blocks/fields) are skipped — those are
 * edited via the canvas / tree, not the property inspector.
 */
(function () {
  const SKIP = new Set(['blocks', 'fields']);

  const Section = ({ title, depth, count, children }) => {
    const [open, setOpen] = React.useState(count <= 12);
    return (
      <div>
        <div onClick={() => setOpen(!open)} style={{
          display: 'flex', alignItems: 'center', gap: 4, cursor: 'pointer',
          padding: '3px 4px', paddingLeft: 6 + depth * 10,
          fontSize: 11, fontWeight: 'bold', color: '#cca35a',
          borderTop: '1px solid #2a2a2a',
        }}>
          <span style={{ width: 10 }}>{open ? '▾' : '▸'}</span>
          <span>{title}</span>
        </div>
        {open && <div>{children}</div>}
      </div>
    );
  };

  const PropertyNode = ({ k, value, keyPath, basePath, store, depth }) => {
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      const entries = Object.entries(value);
      return (
        <Section title={k} depth={depth} count={entries.length}>
          {entries.map(([ck, cv]) => (
            <PropertyNode key={ck} k={ck} value={cv} keyPath={`${keyPath}.${ck}`}
              basePath={basePath} store={store} depth={depth + 1} />
          ))}
        </Section>
      );
    }
    if (Array.isArray(value)) {
      return (
        <Section title={`${k} [${value.length}]`} depth={depth} count={value.length}>
          {value.map((item, i) => (
            <PropertyNode key={i} k={`#${i}`} value={item} keyPath={`${keyPath}.${i}`}
              basePath={basePath} store={store} depth={depth + 1} />
          ))}
        </Section>
      );
    }
    return (
      <window.OaEdPropertyLeaf label={k} value={value} depth={depth}
        onChange={(v) => store.setProp(basePath, keyPath, v)} />
    );
  };

  /** Render the editable property tree for `node` (at `basePath`). */
  window.OaEdPropertyTree = ({ node, basePath, store }) => {
    if (!node || typeof node !== 'object') {
      return <div style={{ color: '#777', fontSize: 11, padding: 10 }}>No element selected.</div>;
    }
    const entries = Object.entries(node).filter(([k]) => !SKIP.has(k));
    return (
      <div>
        {entries.map(([k, v]) => (
          <PropertyNode key={k} k={k} value={v} keyPath={k}
            basePath={basePath} store={store} depth={0} />
        ))}
      </div>
    );
  };
})();
