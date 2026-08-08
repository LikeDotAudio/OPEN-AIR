/**
 * Header: focus.jsx
 * Purpose: focus component or utility.
 * Description: Handles logic and rendering for focus component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

/**
 * Interface/layout_engine/focus.jsx — path resolution for canvas interaction.
 * Mirrors oaGuiEditorWYSIWYG/Interface/layout_engine/focus.py.
 *
 * Widgets carry a data-oca-path attribute (emitted by WidgetFactory). These
 * helpers translate screen coordinates and stored paths to/from DOM elements.
 */
(function () {
  const esc = (s) => ((window.CSS && CSS.escape) ? CSS.escape(s) : String(s).replace(/"/g, '\\"'));

  window.OaEdFocus = {
    /** Topmost element with a data-oca-path under the given screen point. */
    resolvePathAt(x, y) {
      const els = document.elementsFromPoint(x, y);
      for (const el of els) {
        const p = el.getAttribute && el.getAttribute('data-oca-path');
        if (p) return p;
      }
      return null;
    },

    /** Find the nearest container path (OcaBin/OcaBlock) at a screen point. */
    resolveContainerAt(x, y, isContainerPath) {
      const els = document.elementsFromPoint(x, y);
      for (const el of els) {
        const p = el.getAttribute && el.getAttribute('data-oca-path');
        if (p && (!isContainerPath || isContainerPath(p))) return p;
      }
      return null;
    },

    elementForPath(root, path) {
      if (!root || !path) return null;
      try { return root.querySelector(`[data-oca-path="${esc(path)}"]`); }
      catch (e) { return null; }
    },
  };
})();
