/**
 * Header: grab_bag_loader.jsx
 * Purpose: grab_bag_loader component or utility.
 * Description: Handles logic and rendering for grab_bag_loader component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

/**
 * FileReaders/grab_bag_loader.jsx — Load the palette of placeable widgets.
 * Mirrors oaGuiEditorWYSIWYG/FileReaders/grab_bag_loader.py.
 *
 * Fetches /api/grabbag (the server scans oaGuiElements/ * /sample.json), and
 * caches the result globally so the palette opens instantly after first load.
 */
(function () {
  let _cache = null;

  window.OaEdGrabBagLoader = {
    /** Returns { components: [{name, category, type, schema, path}, ...] }. */
    async load(force = false) {
      if (_cache && !force) return _cache;
      const res = await fetch('/api/grabbag');
      if (!res.ok) throw new Error('Failed to fetch /api/grabbag');
      _cache = await res.json();
      return _cache;
    },

    /** Group the flat component list into { category: [components] }. */
    byCategory(components) {
      const groups = {};
      for (const c of (components || [])) {
        (groups[c.category] = groups[c.category] || []).push(c);
      }
      return groups;
    },

    clearCache() { _cache = null; },
  };
})();
