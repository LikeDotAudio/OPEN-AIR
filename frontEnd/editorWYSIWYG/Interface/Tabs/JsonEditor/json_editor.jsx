/**
 * Interface/Tabs/JsonEditor/json_editor.jsx — raw JSON code view, two-way synced.
 * Mirrors oaGuiEditorWYSIWYG/Interface/Tabs/JsonEditor/json_editor.py.
 *
 * Editing valid JSON commits live to the store (so canvas/tree update). When the
 * store changes elsewhere and the editor isn't focused, the text refreshes.
 */
(function () {
  window.OaEdJsonEditor = ({ store }) => {
    const st = window.useEditorStore(store);
    const [text, setText] = React.useState(() => JSON.stringify(st.data, null, 2));
    const [error, setError] = React.useState(null);
    const focusedRef = React.useRef(false);

    // Refresh from store when not actively editing.
    React.useEffect(() => {
      if (!focusedRef.current) {
        setText(JSON.stringify(st.data, null, 2));
        setError(null);
      }
    }, [st.rev]);

    const onChange = (e) => {
      const v = e.target.value;
      setText(v);
      try {
        const parsed = JSON.parse(v);
        setError(null);
        store.replaceData(parsed);
      } catch (err) {
        setError(err.message);
      }
    };

    return (
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '4px 8px', background: '#111', borderBottom: '1px solid #333', flexShrink: 0 }}>
          <span style={{ fontSize: 11, color: '#888', fontWeight: 'bold' }}>JSON</span>
          {error
            ? <span style={{ fontSize: 10, color: '#f66' }}>⚠ {error}</span>
            : <span style={{ fontSize: 10, color: '#5a5' }}>✓ valid · edits apply live</span>}
        </div>
        <textarea
          value={text}
          onChange={onChange}
          onFocus={() => { focusedRef.current = true; }}
          onBlur={() => { focusedRef.current = false; setText(JSON.stringify(store.getData(), null, 2)); setError(null); }}
          spellCheck={false}
          style={{
            flex: 1, minHeight: 0, resize: 'none', border: 'none', outline: 'none',
            background: '#0d0d0d', color: error ? '#f99' : '#cfe', padding: 10,
            fontFamily: 'monospace', fontSize: 12, lineHeight: 1.4,
            borderLeft: error ? '3px solid #a33' : '3px solid transparent', boxSizing: 'border-box',
          }}
        />
      </div>
    );
  };
})();
