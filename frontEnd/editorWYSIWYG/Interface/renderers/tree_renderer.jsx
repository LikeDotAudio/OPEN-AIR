/**
 * Interface/renderers/tree_renderer.jsx — recursive property-tree renderer.
 * Mirrors oaGuiEditorWYSIWYG/Interface/renderers/tree_renderer.py.
 *
 * Renders editable controls for a node's own properties, recursing into nested
 * objects/arrays. Structural children (blocks/fields) are skipped.
 *
 * Composite sub-configs (dial_config = embedded knob, fader_config = fader,
 * value_config = readout) are MERGED with the library reference so every
 * supported param is editable. Params that come from the library reference but
 * are NOT in the saved JSON render in RED; editing one writes it to the JSON and
 * it turns normal.
 *
 * Layout: loose top-level scalars are gathered under a "Domain" parent pinned to
 * the top; all sections start folded except Domain.
 */
(function () {
  const SKIP = new Set(['blocks', 'fields']);
  const DIM = new Set(['width', 'height', 'x', 'y']); // accept px or %

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

  const isObj = (v) => v && typeof v === 'object' && !Array.isArray(v);

  // value  = the value to render (may be a merged reference+instance object)
  // saved  = the corresponding value in the SAVED instance (undefined => not saved)
  const PropertyNode = ({ k, value, saved, keyPath, basePath, store, depth, defaultOpen = false }) => {
    if (isObj(value)) {
      // Composite sub-config: merge the library reference so all params show.
      // `saved` is the source of truth for "red" (notSaved); never overwrite it
      // with the merged value, or library-only params would look saved.
      let renderValue = value, savedObj = saved;
      if (window.OaEdComposite && window.OaEdComposite.isSubWidget(k)) {
        const ref = window.OaEdComposite.referenceFor(k);
        if (ref) renderValue = window.OaEdComposite.merge(ref, isObj(value) ? value : {});
      }
      const entries = Object.entries(renderValue);
      return (
        <Section title={k} depth={depth} defaultOpen={defaultOpen} count={entries.length}>
          {entries.map(([ck, cv]) => (
            <PropertyNode key={ck} k={ck} value={cv}
              saved={isObj(savedObj) || Array.isArray(savedObj) ? savedObj[ck] : undefined}
              keyPath={`${keyPath}.${ck}`} basePath={basePath} store={store} depth={depth + 1} />
          ))}
        </Section>
      );
    }
    if (Array.isArray(value)) {
      return (
        <Section title={`${k} [${value.length}]`} depth={depth} defaultOpen={defaultOpen} count={value.length}>
          {value.map((item, i) => (
            <PropertyNode key={i} k={`#${i}`} value={item}
              saved={Array.isArray(saved) ? saved[i] : undefined}
              keyPath={`${keyPath}.${i}`} basePath={basePath} store={store} depth={depth + 1} />
          ))}
        </Section>
      );
    }
    return (
      <window.OaEdPropertyLeaf label={k} value={value} depth={depth}
        notSaved={saved === undefined}
        dimension={DIM.has(k)}
        options={window.OaEdEnum && window.OaEdEnum.optionsFor(keyPath)}
        onChange={(v) => store.setProp(basePath, keyPath, v)} />
    );
  };

  /** Render the editable property tree for `node` (at `basePath`).
   *  Renders in JSON key order (type → domain → value → layout → rest); the
   *  domain and value parents are open by default. `type` is shown in the header,
   *  so it's skipped here. */
  window.OaEdPropertyTree = ({ node, basePath, store }) => {
    if (!node || typeof node !== 'object') {
      return <div style={{ color: '#777', fontSize: 11, padding: 10 }}>No element selected.</div>;
    }
    // Merge the widget's full library reference so every supported param is shown:
    // params present in the library but NOT in the saved JSON render in RED, and
    // editing one writes it to the JSON. `saved` is always read from the original
    // node so the red/normal state reflects the SAVED instance, not the merge.
    const typeRef = window.OaEdComposite && window.OaEdComposite.referenceForType
      ? window.OaEdComposite.referenceForType(node.type) : null;
    const merged = typeRef ? window.OaEdComposite.mergeForType(typeRef, node) : node;
    const entries = Object.entries(merged).filter(([k]) => !SKIP.has(k) && k !== 'type');

    return (
      <div>
        {entries.map(([k, v]) => {
          const savedV = node[k]; // undefined => library-only => red
          if (isObj(v) || Array.isArray(v)) {
            return (
              <PropertyNode key={k} k={k} value={v} saved={savedV} keyPath={k}
                basePath={basePath} store={store} depth={0}
                defaultOpen={k === 'domain' || k === 'value'} />
            );
          }
          return (
            <window.OaEdPropertyLeaf key={k} label={k} value={v} depth={0}
              notSaved={savedV === undefined}
              dimension={DIM.has(k)}
              options={window.OaEdEnum && window.OaEdEnum.optionsFor(k)}
              onChange={(nv) => store.setProp(basePath, k, nv)} />
          );
        })}
      </div>
    );
  };
})();
