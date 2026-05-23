/**
 * Constants/composite_schemas.jsx — full param sets for composite sub-widgets.
 *
 * A composite (e.g. _Horizontal_with_dial_Value) carries sub-config blocks
 * (dial_config = embedded knob, fader_config = embedded fader, value_config =
 * readout). The placed instance only stores a few of each sub-widget's params,
 * but FaderDial renders the embedded widget as { ...config, ...dial_config }, so
 * any standard styling param put in the sub-config IS honored.
 *
 * This module pulls the richest matching widget schema from the library
 * (/api/grabbag) and exposes its styling groups as a "reference" that the
 * property editor merges in, so every supported knob/fader/value param is
 * editable — pre-filled with the library default until the user overrides it.
 */
(function () {
  // sub-config key -> library type keyword used to find the reference widget.
  const KEYWORDS = { dial_config: 'knob', fader_config: 'fader', value_config: 'value' };
  // Top-level groups worth exposing (styling surface the embedded widget reads).
  const KEEP = ['cosmetics', 'style', 'readout', 'interaction', 'dynamics', 'scale', 'styling', 'pointer', 'style_flags'];

  const countKeys = (o) => {
    let n = 0;
    if (o && typeof o === 'object') for (const k in o) { n++; if (o[k] && typeof o[k] === 'object') n += countKeys(o[k]); }
    return n;
  };

  window.OaEdComposite = {
    KEYWORDS,
    _refs: null,

    async load(force) {
      if (this._refs && !force) return this._refs;
      const data = await window.OaEdGrabBagLoader.load(force);
      const comps = data.components || [];
      const refs = {};
      for (const [subKey, kw] of Object.entries(KEYWORDS)) {
        let best = null, bestN = -1;
        for (const c of comps) {
          if (String(c.type || '').toLowerCase().includes(kw)) {
            const n = countKeys(c.schema);
            if (n > bestN) { bestN = n; best = c.schema; }
          }
        }
        if (best) {
          const ref = {};
          for (const g of KEEP) if (best[g] !== undefined) ref[g] = best[g];
          if (Object.keys(ref).length) refs[subKey] = ref;
        }
      }
      this._refs = refs;
      return refs;
    },

    isSubWidget(key) { return Object.prototype.hasOwnProperty.call(KEYWORDS, key); },
    referenceFor(key) { return this._refs ? (this._refs[key] || null) : null; },

    /** Deep-merge reference defaults UNDER the instance (instance values win). */
    merge(ref, inst) {
      if (!ref) return inst;
      if (!inst || typeof inst !== 'object' || Array.isArray(inst)) return inst != null ? inst : ref;
      const out = { ...ref, ...inst };
      for (const k in ref) {
        if (ref[k] && typeof ref[k] === 'object' && !Array.isArray(ref[k]) &&
            inst[k] && typeof inst[k] === 'object' && !Array.isArray(inst[k])) {
          out[k] = this.merge(ref[k], inst[k]);
        }
      }
      return out;
    },
  };
})();
