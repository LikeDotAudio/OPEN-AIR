/**
 * Header: file_writer.jsx
 * Purpose: file_writer component or utility.
 * Description: Handles logic and rendering for file_writer component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

/**
 * FileWriters/file_writer.jsx — Persist a GUI definition to disk.
 * Mirrors oaGuiEditorWYSIWYG/FileWriters/file_writer.py.
 *
 * POSTs to /api/save; the server writes a timestamped .old backup before
 * overwriting the target JSON inside Gui_Frames.
 */
(function () {
  window.OaEdFileWriter = {
    /**
     * @param {string} relPath  path relative to Gui_Frames (from the tree node)
     * @param {object} content  full file object ({ rootKey: node })
     * @returns {Promise<{ok:boolean, backup?:string, error?:string}>}
     */
    async save(relPath, content) {
      if (!relPath) return { ok: false, error: 'No file path (cannot save).' };
      const res = await fetch('/api/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: relPath, content }),
      });
      let body = {};
      try { body = await res.json(); } catch (_) { /* ignore */ }
      if (!res.ok || !body.ok) {
        return { ok: false, error: body.error || `Save failed (HTTP ${res.status})` };
      }
      return { ok: true, backup: body.backup };
    },

    /** Browser download fallback (no server write). */
    download(filename, content) {
      const blob = new Blob([JSON.stringify(content, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename || 'layout.json';
      a.click();
      URL.revokeObjectURL(url);
    },
  };
})();
