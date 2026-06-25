// frameLayout/OcaArray.jsx — data-driven repeater container.
/**
 * OcaArray renders its `blueprint` (a template node) ONCE PER entry in `data`,
 * substituting {{token}} placeholders with that entry's fields and giving each
 * instance a distinct path (from the entry's `id`) so its widgets bind to unique
 * MQTT topics. `layout_columns` controls the grid.
 *
 * In the WYSIWYG editor it renders the template ONCE (a single representative
 * instance) — flagged via `window.OaEdPreviewCtx` set by the editor's preview —
 * so the canvas isn't flooded with N copies. At runtime it renders all N.
 */
// Shared context: true inside the editor's live preview, false in the running app.
window.OaEdPreviewCtx = window.OaEdPreviewCtx || React.createContext(false);

(function () {
  // Replace {{key}} tokens in any string with data[key] (localized if an object).
  const substitute = (tpl, item, lang) => {
    const lookup = (key) => {
      let v = item ? item[key] : undefined;
      if (v && typeof v === 'object' && !Array.isArray(v)) v = v[lang] || v.En || '';
      return v;
    };
    const repl = (s) => (typeof s === 'string'
      ? s.replace(/\{\{(\w+)\}\}/g, (m, k) => {
          const v = lookup(k);
          return (v !== undefined && v !== null) ? String(v) : m;
        })
      : s);
    const walk = (o) => {
      if (Array.isArray(o)) return o.map(walk);
      if (o && typeof o === 'object') {
        const out = {};
        for (const k in o) out[k] = walk(o[k]);
        return out;
      }
      return repl(o);
    };
    return walk(tpl);
  };

  window.OcaArray = ({ nodeName, node, path_prefix, jsonPath }) => {
    const [lang] = (window.useMqttLang ? window.useMqttLang() : ['En']);
    const inEditor = React.useContext(window.OaEdPreviewCtx);

    const blueprint = node.blueprint || {};
    const data = Array.isArray(node.data) ? node.data : [];
    const cols = parseInt(node.layout_columns, 10) || data.length || 1;

    // Editor: a single representative instance (template). Runtime: all entries.
    const items = inEditor ? (data.length ? data.slice(0, 1) : [{}]) : data;

    return (
      <div className="oca-array" style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${inEditor ? 1 : cols}, minmax(0, 1fr))`,
        gap: '6px', width: '100%', alignItems: 'start',
      }}>
        {items.map((item, i) => {
          const inst = substitute(blueprint, item, lang);
          const instName = (item && item.id) || `${nodeName}_${i}`;
          // In the editor, point selection at the raw blueprint so edits hit the
          // template; at runtime, tag with the data index.
          const jp = jsonPath ? (inEditor ? `${jsonPath}.blueprint` : `${jsonPath}.data.${i}`) : undefined;
          return (
            <window.WidgetFactory key={instName} nodeName={instName} node={inst}
              path_prefix={nodeName ? `${path_prefix}/${nodeName}` : path_prefix} jsonPath={jp} />
          );
        })}
        {inEditor && data.length > 1 && (
          <div style={{ gridColumn: '1 / -1', fontSize: 10, color: '#cca35a', opacity: 0.85, padding: '2px 4px' }}>
            ⤷ OcaArray template — renders ×{data.length} at runtime (showing 1)
          </div>
        )}
      </div>
    );
  };
})();
