/**
 * FileReaders/file_reader.jsx — Load a GUI definition from the server.
 * Mirrors oaGuiEditorWYSIWYG/FileReaders/file_reader.py.
 *
 * The directory tree (/api/tree) embeds each file's parsed content, so loading
 * a panel is a walk of that tree by its relative path.
 */
(function () {
  const findFile = (node, relPath) => {
    if (!node) return null;
    if (node.type === 'file' && node.path === relPath) return node;
    if (node.children) {
      for (const child of node.children) {
        const found = findFile(child, relPath);
        if (found) return found;
      }
    }
    return null;
  };

  window.OaEdFileReader = {
    /** Re-fetch the tree and return the parsed content for relPath, or null. */
    async load(relPath) {
      const res = await fetch('/api/tree');
      if (!res.ok) throw new Error('Failed to fetch /api/tree');
      const tree = await res.json();
      const file = findFile(tree, relPath);
      return file ? file.content : null;
    },
  };
})();
