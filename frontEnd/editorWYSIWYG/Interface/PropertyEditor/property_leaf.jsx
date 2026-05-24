/**
 * Interface/PropertyEditor/property_leaf.jsx — single editable property field.
 * Mirrors oaGuiEditorWYSIWYG/Interface/PropertyEditor/property_leaf.py.
 *
 * Picks an input by value type: boolean -> checkbox, enum -> dropdown,
 * number -> number input, #hex -> color swatch + text, otherwise text.
 *
 * All inputs commit on EVERY change so edits reflect in the live preview in
 * realtime. While a text/number field is focused, the local draft is preserved
 * (not overwritten by store updates) so typing isn't disrupted.
 *
 * Reference-only params (not in the saved JSON) render in one of two states:
 *   'default' (YELLOW) — carries an implied default value you can adopt by editing.
 *   'none'    (RED)    — reference-only with NO real default (empty string / null).
 * Saved params render normally (grey label / white value).
 */
(function () {
  const isHex = (v) => typeof v === 'string' && /^#([0-9a-f]{3}|[0-9a-f]{4}|[0-9a-f]{6}|[0-9a-f]{8})$/i.test(v);

  const RED = '#e5484d', YELLOW = '#e2b203', GREY = '#9aa', WHITE = '#eee';
  const isEmptyVal = (v) => v == null || v === '';
  // Saved -> 'saved'; reference-only with a real value -> 'default'; reference-only
  // empty -> 'none'. (false / 0 count as real defaults, only null/'' are empty.)
  const stateFor = (notSaved, value) => (!notSaved ? 'saved' : (isEmptyVal(value) ? 'none' : 'default'));
  const accentFor = (state) => (state === 'none' ? RED : state === 'default' ? YELLOW : null);

  const rowStyle = (depth, state) => ({
    display: 'flex', alignItems: 'center', gap: 6,
    padding: '2px 4px', paddingLeft: 6 + depth * 10,
    borderLeft: `2px solid ${accentFor(state) || 'transparent'}`,
  });
  const labelStyleFor = (state) => ({
    flex: '0 0 42%', fontSize: 11, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
    color: accentFor(state) || GREY,
    fontStyle: state === 'saved' ? 'normal' : 'italic',
  });
  // The value itself reads YELLOW in the 'default' state so an implied default is
  // visibly NOT a saved value; editing it materializes the param (turns white).
  const inputStyleFor = (state) => ({
    flex: 1, minWidth: 0, background: '#111',
    color: state === 'default' ? YELLOW : WHITE,
    border: '1px solid #333', borderRadius: 3, padding: '2px 4px', fontSize: 11, outline: 'none',
  });

  window.OaEdPropertyLeaf = ({ label, value, onChange, depth = 0, options, notSaved = false, dimension = false }) => {
    const [draft, setDraft] = React.useState(value);
    const focused = React.useRef(false);
    // Sync from the store only when not actively typing here.
    React.useEffect(() => { if (!focused.current) setDraft(value); }, [value]);
    const state = stateFor(notSaved, value);
    const labelStyle = labelStyleFor(state);
    const inputStyle = inputStyleFor(state);

    // Dimension fields (width/height/x/y) accept px OR % in one text box:
    // "200" -> 200 (px number), "50%" -> "50%" (percent string).
    if (dimension) {
      const commitDim = (raw) => {
        const s = String(raw).trim();
        if (s.endsWith('%')) onChange(s);
        else if (s !== '' && !Number.isNaN(Number(s))) onChange(Number(s));
        else onChange(s);
      };
      return (
        <div style={rowStyle(depth, state)}>
          <span style={labelStyle} title={label}>{label}</span>
          <input type="text" style={inputStyle} value={draft == null ? '' : draft} placeholder="px or %"
            onFocus={() => { focused.current = true; }}
            onChange={(e) => { setDraft(e.target.value); commitDim(e.target.value); }}
            onBlur={() => { focused.current = false; }}
            onKeyDown={(e) => { if (e.key === 'Enter') e.target.blur(); }} />
        </div>
      );
    }

    // Enum dropdown (library legends) — commits immediately.
    if (options && options.length && typeof value !== 'boolean' && typeof value !== 'number') {
      const list = options.includes(value) ? options : [value, ...options];
      return (
        <div style={rowStyle(depth, state)}>
          <span style={labelStyle} title={label}>{label}</span>
          <select style={{ ...inputStyle, cursor: 'pointer' }} value={value == null ? '' : value}
            onChange={(e) => onChange(e.target.value)}>
            {list.map((o) => <option key={String(o)} value={o}>{String(o)}</option>)}
          </select>
        </div>
      );
    }

    if (typeof value === 'boolean') {
      return (
        <div style={rowStyle(depth, state)}>
          <span style={labelStyle} title={label}>{label}</span>
          <input type="checkbox" checked={!!draft}
            onChange={(e) => { setDraft(e.target.checked); onChange(e.target.checked); }} />
        </div>
      );
    }

    if (typeof value === 'number') {
      return (
        <div style={rowStyle(depth, state)}>
          <span style={labelStyle} title={label}>{label}</span>
          <input type="number" style={inputStyle} value={draft}
            onFocus={() => { focused.current = true; }}
            onChange={(e) => { setDraft(e.target.value); const n = parseFloat(e.target.value); if (!Number.isNaN(n)) onChange(n); }}
            onBlur={() => { focused.current = false; if (Number.isNaN(parseFloat(draft))) setDraft(value); }}
            onKeyDown={(e) => { if (e.key === 'Enter') e.target.blur(); }} />
        </div>
      );
    }

    return (
      <div style={rowStyle(depth, state)}>
        <span style={labelStyle} title={label}>{label}</span>
        {isHex(value) && (
          <input type="color" value={(draft || '#000000').slice(0, 7)} style={{ width: 22, height: 20, padding: 0, border: '1px solid #333', background: '#111' }}
            onChange={(e) => { setDraft(e.target.value); onChange(e.target.value); }} />
        )}
        <input type="text" style={inputStyle} value={draft == null ? '' : draft}
          onFocus={() => { focused.current = true; }}
          onChange={(e) => { setDraft(e.target.value); onChange(e.target.value); }}
          onBlur={() => { focused.current = false; }}
          onKeyDown={(e) => { if (e.key === 'Enter') e.target.blur(); }} />
      </div>
    );
  };
})();
