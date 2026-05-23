/**
 * Interface/PropertyEditor/property_leaf.jsx — single editable property field.
 * Mirrors oaGuiEditorWYSIWYG/Interface/PropertyEditor/property_leaf.py.
 *
 * Picks an input by value type: boolean -> checkbox, number -> number input,
 * #hex string -> color swatch + text, otherwise text.
 */
(function () {
  const isHex = (v) => typeof v === 'string' && /^#([0-9a-f]{3}|[0-9a-f]{4}|[0-9a-f]{6}|[0-9a-f]{8})$/i.test(v);

  const rowStyle = (depth) => ({
    display: 'flex', alignItems: 'center', gap: 6,
    padding: '2px 4px', paddingLeft: 6 + depth * 10,
  });
  const labelStyle = { flex: '0 0 42%', fontSize: 11, color: '#9aa', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' };
  const inputStyle = { flex: 1, minWidth: 0, background: '#111', color: '#eee', border: '1px solid #333', borderRadius: 3, padding: '2px 4px', fontSize: 11, outline: 'none' };

  window.OaEdPropertyLeaf = ({ label, value, onChange, depth = 0, options }) => {
    const [draft, setDraft] = React.useState(value);
    React.useEffect(() => setDraft(value), [value]);

    // Enum dropdown driven by the library legends (see Constants/property_options).
    if (options && options.length && typeof value !== 'boolean' && typeof value !== 'number') {
      const list = options.includes(value) ? options : [value, ...options];
      return (
        <div style={rowStyle(depth)}>
          <span style={labelStyle} title={label}>{label}</span>
          <select style={{ ...inputStyle, cursor: 'pointer' }} value={value == null ? '' : value}
            onChange={(e) => { setDraft(e.target.value); onChange(e.target.value); }}>
            {list.map((o) => <option key={String(o)} value={o}>{String(o)}</option>)}
          </select>
        </div>
      );
    }

    if (typeof value === 'boolean') {
      return (
        <div style={rowStyle(depth)}>
          <span style={labelStyle} title={label}>{label}</span>
          <input type="checkbox" checked={!!draft}
            onChange={(e) => { setDraft(e.target.checked); onChange(e.target.checked); }} />
        </div>
      );
    }

    if (typeof value === 'number') {
      return (
        <div style={rowStyle(depth)}>
          <span style={labelStyle} title={label}>{label}</span>
          <input type="number" style={inputStyle} value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onBlur={() => { const n = parseFloat(draft); onChange(Number.isNaN(n) ? value : n); }}
            onKeyDown={(e) => { if (e.key === 'Enter') e.target.blur(); }} />
        </div>
      );
    }

    const commit = () => onChange(draft);
    return (
      <div style={rowStyle(depth)}>
        <span style={labelStyle} title={label}>{label}</span>
        {isHex(value) && (
          <input type="color" value={(draft || '#000000').slice(0, 7)} style={{ width: 22, height: 20, padding: 0, border: '1px solid #333', background: '#111' }}
            onChange={(e) => { setDraft(e.target.value); onChange(e.target.value); }} />
        )}
        <input type="text" style={inputStyle} value={draft == null ? '' : draft}
          onChange={(e) => setDraft(e.target.value)}
          onBlur={commit}
          onKeyDown={(e) => { if (e.key === 'Enter') e.target.blur(); }} />
      </div>
    );
  };
})();
