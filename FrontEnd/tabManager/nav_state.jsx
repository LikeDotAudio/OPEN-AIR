/**
 * tabManager/nav_state.jsx — persist the live view (active window + every pane's
 * active tab) in the URL hash so a refresh restores exactly where you were.
 *
 * The layout is a TREE (splits show panes side-by-side, each with its own tabs),
 * so a single path can't capture it. Instead each selection is stored keyed by
 * its node PATH (e.g. "Window_1/left_50/top_100/0_Spectrum"). The active window
 * is stored under "__win". State lives in the hash as URLSearchParams, updated
 * with history.replaceState (URL changes, no reload, no history spam).
 */
(function () {
  const parse = () => new URLSearchParams((window.location.hash || '').replace(/^#/, ''));
  let params = parse();
  window.addEventListener('hashchange', () => { params = parse(); });

  window.OaNav = {
    /** Active selection saved for `key` (a node path), or `fallback`. */
    get(key, fallback) {
      const v = parse().get(key);
      return v != null ? v : fallback;
    },
    /** Persist `value` for `key` into the URL hash (no reload). */
    set(key, value) {
      const url = this.buildUrl(key, value);
      // update local params
      params = parse();
      window.history.replaceState(null, '', url);
    },
    /** Return a new URL with `value` set for `key`, without navigating */
    buildUrl(key, value) {
      const p = parse();
      if (value == null) p.delete(key); else p.set(key, value);
      const s = p.toString();
      return window.location.pathname + window.location.search + (s ? '#' + s : '');
    },
    /** Return a new URL with the isolate query parameter set to fullPath */
    buildIsolatedUrl(fullPath) {
      const search = new URLSearchParams(window.location.search);
      search.set('isolate', fullPath);
      return window.location.pathname + '?' + search.toString() + window.location.hash;
    }
  };
})();
