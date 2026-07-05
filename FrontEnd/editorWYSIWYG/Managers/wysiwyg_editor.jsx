/**
 * Header: wysiwyg_editor.jsx
 * Purpose: wysiwyg_editor component or utility.
 * Description: Handles logic and rendering for wysiwyg_editor component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

/**
 * Managers/wysiwyg_editor.jsx — main editor controller (overlay modal).
 * Mirrors oaGuiEditorWYSIWYG/Managers/wysiwyg_editor.py (WysiwygEditor).
 *
 * Creates the editor store for the opened file, assembles toolbar + layout in a
 * full-viewport overlay, and wires Save (POST /api/save with backup). Rendered
 * inside the app tree so it shares the MqttProvider context (live preview works).
 */
(function () {
  window.WysiwygEditor = ({ filePath, content, onClose }) => {
    // One store per opened file; recreated if the target file changes.
    const store = React.useMemo(
      () => window.OaEdState.create(content || {}, filePath),
      [filePath]
    );

    // Focus the root element on open so Properties has something to show.
    React.useEffect(() => {
      const rootKey = Object.keys(store.getData())[0];
      if (rootKey) store.select(rootKey);
    }, [store]);

    const [saveMsg, setSaveMsg] = React.useState(null);

    const doSave = React.useCallback(async () => {
      const res = await window.OaEdFileWriter.save(store.getState().filePath, store.getData());
      if (res.ok) {
        store.markSaved();
        setSaveMsg({ ok: true, text: `Saved${res.backup ? ` · backup ${res.backup}` : ''}` });
      } else {
        setSaveMsg({ ok: false, text: res.error || 'Save failed' });
      }
      window.clearTimeout(doSave._t);
      doSave._t = window.setTimeout(() => setSaveMsg(null), 5000);
    }, [store]);

    // Esc closes, Ctrl/Cmd+S saves.
    React.useEffect(() => {
      const onKey = (e) => {
        if (e.key === 'Escape') { onClose && onClose(); }
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') { e.preventDefault(); doSave(); }
      };
      window.addEventListener('keydown', onKey);
      return () => window.removeEventListener('keydown', onKey);
    }, [onClose, doSave]);

    return (
      <div style={{
        position: 'fixed', inset: 0, zIndex: 9999,
        display: 'flex', flexDirection: 'column',
        background: '#141414', color: '#eee',
        fontFamily: 'Segoe UI, Tahoma, sans-serif',
      }}>
        <window.OaEdToolbar store={store} onSave={doSave} onClose={onClose} saveMsg={saveMsg} />
        <window.OaEdLayout store={store} />
      </div>
    );
  };
})();
