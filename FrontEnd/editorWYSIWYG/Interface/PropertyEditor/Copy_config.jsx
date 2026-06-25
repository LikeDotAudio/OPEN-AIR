/**
 * Interface/PropertyEditor/Copy_config.jsx — copy/paste handlers for a widget's
 * sub-config objects (any key ending in `_config`: value_config, fader_config,
 * dial_config, …). Rendered as a small button pair beside that fold-out in the
 * property tree, so each sub-config is copyable one at a time.
 *
 * Props: { value, kind, onPaste }
 *   value   — the config object to copy (the saved/merged instance value)
 *   kind    — the config key, e.g. "dial_config" (used to tag the clipboard)
 *   onPaste — (cfgObj) => void, applied when pasting (store.setProp(...,kind,v))
 *
 * The clipboard is wrapped under the config's own key (`{ "dial_config": {…} }`)
 * so paste can REJECT a different kind (you can't paste a fader_config into a
 * dial_config, nor a style/layout into a config). In-memory fallback
 * (`window.OaEdConfigClip = { kind, value }`) is also kind-checked.
 */
(function () {
  window.OaEdCopyConfig = ({ value, kind, onPaste }) => {
    const [msg, setMsg] = React.useState('');
    const flash = (m) => { setMsg(m); setTimeout(() => setMsg(''), 1200); };
    const stop = (e) => { e.stopPropagation(); };

    const copy = async (e) => {
      stop(e);
      if (value == null) { flash('empty'); return; }
      window.OaEdConfigClip = { kind, value: JSON.parse(JSON.stringify(value)) };
      try { await navigator.clipboard.writeText(JSON.stringify({ [kind]: value }, null, 2)); } catch (_) { /* in-memory fallback */ }
      flash('copied');
    };
    const paste = async (e) => {
      stop(e);
      let parsed = null;
      try { const t = await navigator.clipboard.readText(); if (t) parsed = JSON.parse(t); } catch (_) { /* try in-memory */ }
      let v = null;
      if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
        if (parsed[kind] && typeof parsed[kind] === 'object') v = parsed[kind];          // same-kind (or whole element)
        else {
          const other = Object.keys(parsed).find((k) => /_config$/.test(k));
          if (other) { flash(`that's a ${other}`); return; }                              // different config kind
          if (parsed.style || parsed.layout) { flash('wrong kind'); return; }             // a style/layout, not a config
          v = parsed;                                                                      // bare object (legacy/manual)
        }
      }
      if (!v && window.OaEdConfigClip && window.OaEdConfigClip.kind === kind) v = window.OaEdConfigClip.value;
      if (v && typeof v === 'object' && !Array.isArray(v)) { onPaste(JSON.parse(JSON.stringify(v))); flash('pasted'); }
      else flash('empty');
    };

    const b = { background: '#2a2a2a', color: '#cca35a', border: '1px solid #444', borderRadius: 3, fontSize: 9, padding: '0 5px', cursor: 'pointer', lineHeight: '15px' };
    return (
      <span onClick={stop} style={{ display: 'inline-flex', gap: 4, alignItems: 'center', marginLeft: 'auto' }}>
        <button style={b} onClick={copy} title={`Copy ${kind} to clipboard`}>⧉ copy</button>
        <button style={b} onClick={paste} title={`Paste a ${kind} from clipboard`}>⇩ paste</button>
        {msg && <span style={{ fontSize: 9, color: '#FF9900' }}>{msg}</span>}
      </span>
    );
  };
})();
