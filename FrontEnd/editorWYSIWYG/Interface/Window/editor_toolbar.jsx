/**
 * Interface/Window/editor_toolbar.jsx — top action bar for the editor.
 * Mirrors oaGuiEditorWYSIWYG/Interface/Window/editor_toolbar.py + editor_menus.py
 * (file actions are surfaced as toolbar buttons in the web build).
 */
(function () {
  const tbBtn = (extra) => ({
    background: '#2a2a2a', color: '#eee', border: '1px solid #444', borderRadius: 4,
    padding: '5px 12px', fontSize: 12, cursor: 'pointer', fontWeight: 'bold', ...extra,
  });

  window.OaEdToolbar = ({ store, onSave, onClose, saveMsg }) => {
    const st = window.useEditorStore(store);
    const fileName = (st.filePath || 'unsaved').split('/').pop();

    const download = () => window.OaEdFileWriter.download(fileName, store.getData());

    return (
      <div style={{
        display: 'flex', alignItems: 'center', gap: 10, padding: '6px 12px',
        background: '#0c0c0c', borderBottom: '1px solid #333', flexShrink: 0,
      }}>
        <span style={{ color: '#FF9900', fontWeight: 'bold', fontSize: 13, letterSpacing: 1 }}>WYSIWYG</span>
        <span style={{ color: '#bbb', fontSize: 12 }}>{fileName}</span>
        {st.dirty && <span title="Unsaved changes" style={{ color: '#FF9900', fontSize: 18, lineHeight: '12px' }}>•</span>}

        <div style={{ flex: 1 }} />

        {saveMsg && (
          <span style={{ fontSize: 11, color: saveMsg.ok ? '#6c6' : '#f66' }}>
            {saveMsg.ok ? '✓ ' : '⚠ '}{saveMsg.text}
          </span>
        )}
        <button style={tbBtn({ background: '#1f6b2e', borderColor: '#2e8b40' })} onClick={onSave}>💾 Save</button>
        <button style={tbBtn()} onClick={download} title="Download a copy">⤓ Download</button>
        <button style={tbBtn({ borderColor: '#a33', color: '#f99' })} onClick={onClose}>✕ Close</button>
      </div>
    );
  };
})();
