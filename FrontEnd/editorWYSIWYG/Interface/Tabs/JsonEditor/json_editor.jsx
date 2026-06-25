/**
 * Interface/Tabs/JsonEditor/json_editor.jsx — raw JSON code view, two-way synced.
 * Mirrors oaGuiEditorWYSIWYG/Interface/Tabs/JsonEditor/json_editor.py.
 *
 * Editing valid JSON commits live to the store (canvas/tree update). When the
 * store changes elsewhere and the editor isn't focused, the text refreshes.
 *
 * Selecting an element elsewhere scrolls the JSON to that element AND highlights
 * its whole JSON block in colour. This uses a coloured "mirror" <pre> behind a
 * transparent <textarea>: the textarea handles editing/caret, the mirror shows
 * the text and the highlighted block.
 */
(function () {
  // Char offset of the path's last key, walking each segment in order.
  const keyOffset = (text, path) => {
    if (!path) return null;
    let idx = 0, found = -1, key = '';
    for (const seg of String(path).split('.')) {
      const at = text.indexOf(`"${seg}"`, idx);
      if (at === -1) break;
      found = at; key = seg; idx = at + seg.length;
    }
    return found < 0 ? null : { start: found, afterKey: found + key.length + 2 };
  };

  // Range [start,end) covering the selected element's key AND its value block.
  const blockRange = (text, path) => {
    const ko = keyOffset(text, path);
    if (!ko) return null;
    let i = text.indexOf(':', ko.afterKey);
    if (i === -1) return { start: ko.start, end: ko.afterKey };
    i++;
    while (i < text.length && /\s/.test(text[i])) i++;
    const ch = text[i];
    if (ch === '{' || ch === '[') {
      const open = ch, close = ch === '{' ? '}' : ']';
      let depth = 0, inStr = false, esc = false, j = i;
      for (; j < text.length; j++) {
        const c = text[j];
        if (inStr) { if (esc) esc = false; else if (c === '\\') esc = true; else if (c === '"') inStr = false; }
        else if (c === '"') inStr = true;
        else if (c === open) depth++;
        else if (c === close) { depth--; if (depth === 0) { j++; break; } }
      }
      return { start: ko.start, end: j };
    }
    let j = text.indexOf('\n', i);
    if (j === -1) j = text.length;
    return { start: ko.start, end: j };
  };

  const BOX = {
    margin: 0, padding: 10, border: 'none',
    fontFamily: 'monospace', fontSize: 12, lineHeight: 1.4,
    whiteSpace: 'pre', boxSizing: 'border-box', tabSize: 2,
  };

  window.OaEdJsonEditor = ({ store }) => {
    const st = window.useEditorStore(store);
    const [text, setText] = React.useState(() => JSON.stringify(st.data, null, 2));
    const [error, setError] = React.useState(null);
    const focusedRef = React.useRef(false);
    const taRef = React.useRef(null);
    const mirrorRef = React.useRef(null);

    React.useEffect(() => {
      if (!focusedRef.current) { setText(JSON.stringify(st.data, null, 2)); setError(null); }
    }, [st.rev]);

    const range = React.useMemo(() => blockRange(text, st.selectedPath), [text, st.selectedPath]);

    // Scroll the selected block into view when selection changes.
    React.useEffect(() => {
      const ta = taRef.current;
      if (!ta || !range || focusedRef.current) return;
      const line = text.slice(0, range.start).split('\n').length - 1;
      const top = Math.max(0, line * 12 * 1.4 - 60);
      ta.scrollTop = top;
      if (mirrorRef.current) mirrorRef.current.scrollTop = top;
    }, [st.selectedPath]);

    const onChange = (e) => {
      const v = e.target.value;
      setText(v);
      try { store.replaceData(JSON.parse(v)); setError(null); }
      catch (err) { setError(err.message); }
    };
    const onScroll = (e) => {
      if (mirrorRef.current) {
        mirrorRef.current.scrollTop = e.target.scrollTop;
        mirrorRef.current.scrollLeft = e.target.scrollLeft;
      }
    };

    // Mirror content: text with the selected block wrapped in a highlight span.
    const mirror = range
      ? [
          text.slice(0, range.start),
          <span key="hl" style={{ background: 'rgba(255,153,0,0.22)', color: '#ffd9a0', borderRadius: 2 }}>
            {text.slice(range.start, range.end)}
          </span>,
          text.slice(range.end),
        ]
      : text;

    return (
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '4px 8px', background: '#111', borderBottom: '1px solid #333', flexShrink: 0 }}>
          <span style={{ fontSize: 11, color: '#888', fontWeight: 'bold' }}>JSON</span>
          {error
            ? <span style={{ fontSize: 10, color: '#f66' }}>⚠ {error}</span>
            : <span style={{ fontSize: 10, color: '#5a5' }}>✓ valid · edits apply live</span>}
        </div>
        <div style={{ position: 'relative', flex: 1, minHeight: 0, borderLeft: error ? '3px solid #a33' : '3px solid transparent' }}>
          <pre ref={mirrorRef} aria-hidden="true" style={{
            ...BOX, position: 'absolute', inset: 0, overflow: 'hidden',
            color: '#cfe', background: '#0d0d0d', pointerEvents: 'none',
          }}>{mirror}</pre>
          <textarea
            ref={taRef}
            value={text}
            onChange={onChange}
            onScroll={onScroll}
            onFocus={() => { focusedRef.current = true; }}
            onBlur={() => { focusedRef.current = false; setText(JSON.stringify(store.getData(), null, 2)); setError(null); }}
            spellCheck={false}
            wrap="off"
            style={{
              ...BOX, position: 'absolute', inset: 0, overflow: 'auto', resize: 'none', outline: 'none',
              color: 'transparent', caretColor: '#cfe', background: 'transparent',
            }}
          />
        </div>
      </div>
    );
  };
})();
