/**
 * Interface/renderers/tree_renderer.jsx — recursive property-tree renderer.
 * Mirrors oaGuiEditorWYSIWYG/Interface/renderers/tree_renderer.py.
 *
 * Renders editable controls for a node's own properties, recursing into nested
 * objects/arrays. Structural children (blocks/fields) are skipped.
 *
 * Layout rules (per design feedback):
 *  - Every loose top-level scalar (default_value, min, max, units, step…) is
 *    gathered under a synthetic "Domain" parent pinned to the TOP, so nothing is
 *    rendered un-parented. ("Domain" matches oaGui's pillar vocabulary; oaGui's
 *    "behavior" is a separate, container-only scroll/overflow concept.)
 *  - All sections start FOLDED, except the Domain group which starts open.
 */
(function () {
  const SKIP = new Set(['blocks', 'fields']);

  const Section = ({ title, depth, defaultOpen = false, accent, children }) => {
    const [open, setOpen] = React.useState(defaultOpen);
    return (
      <div>
        <div onClick={() => setOpen(!open)} style={{
          display: 'flex', alignItems: 'center', gap: 4, cursor: 'pointer',
          padding: '3px 4px', paddingLeft: 6 + depth * 10,
          fontSize: 11, fontWeight: 'bold', color: accent || '#cca35a',
          borderTop: '1px solid #2a2a2a',
        }}>
          <span style={{ width: 10 }}>{open ? '▾' : '▸'}</span>
          <span>{title}</span>
        </div>
        {open && <div>{children}</div>}
      </div>
    );
  };

  const isLeaf = (v) => v === null || typeof v !== 'object';

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
        options={window.OaEdEnum && window.OaEdEnum.optionsFor(keyPath)}
        onChange={(v) => store.setProp(basePath, keyPath, v)} />
    );
  };

  /** Render the editable property tree for `node` (at `basePath`). */
  window.OaEdPropertyTree = ({ node, basePath, store }) => {
    if (!node || typeof node !== 'object') {
      return <div style={{ color: '#777', fontSize: 11, padding: 10 }}>No element selected.</div>;
    }
    const entries = Object.entries(node).filter(([k]) => !SKIP.has(k));
    const loose = entries.filter(([, v]) => isLeaf(v));
    const sections = entries.filter(([, v]) => !isLeaf(v));

    return (
      <div>
        {loose.length > 0 && (
          <Section title="Domain" depth={0} defaultOpen accent="#FF9900">
            {loose.map(([k, v]) => (
              <window.OaEdPropertyLeaf key={k} label={k} value={v} depth={1}
                options={window.OaEdEnum && window.OaEdEnum.optionsFor(k)}
                onChange={(nv) => store.setProp(basePath, k, nv)} />
            ))}
          </Section>
        )}
        {sections.map(([k, v]) => (
          <PropertyNode key={k} k={k} value={v} keyPath={k}
            basePath={basePath} store={store} depth={0} />
        ))}
      </div>
    );
  };
})();
