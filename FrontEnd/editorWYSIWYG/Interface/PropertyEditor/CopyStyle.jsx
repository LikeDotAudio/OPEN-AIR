/**
 * Header: CopyStyle.jsx
 * Purpose: CopyStyle component or utility.
 * Description: Handles logic and rendering for CopyStyle component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

/**
 * Interface/PropertyEditor/CopyStyle.jsx — copy/paste handlers for an element's
 * `style` object, rendered as a small button pair beside the `style` fold-out in
 * the property tree.
 *
 * Props: { value, onPaste }
 *   value   — the style object to copy (the saved instance value)
 *   onPaste — (styleObj) => void, applied when pasting (e.g. store.setProp(...,'style',v))
 *
 * Uses the system clipboard (pretty JSON) with an in-memory fallback
 * (`window.OaEdStyleClip`) for when the Clipboard API is blocked. Accepts a copied
 * WHOLE element too (plucks its `.style`).
 */
(function () {
  window.OaEdCopyStyle = ({ value, onPaste }) => {
    const [msg, setMsg] = React.useState('');
    const flash = (m) => { setMsg(m); setTimeout(() => setMsg(''), 1100); };
    const stop = (e) => { e.stopPropagation(); };

    const copy = async (e) => {
      stop(e);
      if (value == null) { flash('empty'); return; }
      window.OaEdStyleClip = JSON.parse(JSON.stringify(value));
      // Wrap under a `style` parent so paste can tell a style from a layout.
      try { await navigator.clipboard.writeText(JSON.stringify({ style: value }, null, 2)); } catch (_) { /* in-memory fallback */ }
      flash('copied');
    };
    const paste = async (e) => {
      stop(e);
      let parsed = null;
      try { const t = await navigator.clipboard.readText(); if (t) parsed = JSON.parse(t); } catch (_) { /* try in-memory */ }
      let v = null;
      if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
        if (parsed.style && typeof parsed.style === 'object') v = parsed.style;          // wrapped style / whole element
        else if (parsed.layout && typeof parsed.layout === 'object') { flash("that's a layout"); return; } // wrong kind
        else v = parsed;                                                                  // bare object (legacy/manual)
      }
      if (!v && window.OaEdStyleClip) v = window.OaEdStyleClip;                            // clipboard-blocked fallback
      if (v && typeof v === 'object' && !Array.isArray(v)) { onPaste(JSON.parse(JSON.stringify(v))); flash('pasted'); }
      else flash('empty');
    };

    const b = { background: '#2a2a2a', color: '#cca35a', border: '1px solid #444', borderRadius: 3, fontSize: 9, padding: '0 5px', cursor: 'pointer', lineHeight: '15px' };
    return (
      <span onClick={stop} style={{ display: 'inline-flex', gap: 4, alignItems: 'center', marginLeft: 'auto' }}>
        <button style={b} onClick={copy} title="Copy style to clipboard">⧉ copy</button>
        <button style={b} onClick={paste} title="Paste style from clipboard">⇩ paste</button>
        {msg && <span style={{ fontSize: 9, color: '#FF9900' }}>{msg}</span>}
      </span>
    );
  };
})();
