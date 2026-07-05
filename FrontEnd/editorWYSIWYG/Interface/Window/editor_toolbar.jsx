
/**
 * Header: editor_toolbar.jsx
 * Purpose: Provides the top action bar (toolbar) for the WYSIWYG editor.
 * Description: This file defines a React component that renders the top toolbar for the editor. It includes UI for saving, downloading, and closing the editor, and displays the current filename and save status. It mirrors the desktop application's toolbar actions for the web environment.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 * 
 * Interface/Window/editor_toolbar.jsx — top action bar for the editor.
 * Mirrors oaGuiEditorWYSIWYG/Interface/Window/editor_toolbar.py + editor_menus.py
 * (file actions are surfaced as toolbar buttons in the web build).
 */
(function () {
  // Helper function to generate consistent button styles
  const tbBtn = (extra) => ({
    background: '#2a2a2a', color: '#eee', border: '1px solid #444', borderRadius: 4,
    padding: '5px 12px', fontSize: 12, cursor: 'pointer', fontWeight: 'bold', ...extra,
  });

  // Main Toolbar Component
  window.OaEdToolbar = ({ store, onSave, onClose, saveMsg }) => {
    // Subscribe to the editor store for reactive updates
    const st = window.useEditorStore(store);
    // Extract just the filename from the full file path
    const fileName = (st.filePath || 'unsaved').split('/').pop();

    // Handler to download the current editor state as a JSON file
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

        // Display feedback messages (e.g., successful save or errors)
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
