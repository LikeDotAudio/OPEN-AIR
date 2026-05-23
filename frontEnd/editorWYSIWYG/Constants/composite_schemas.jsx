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

  // Strip library-only annotation keys (_README/_LEGEND/…) and identity (id/type)
  // so the reference holds only real, editable params. Recurses into objects.
  const cleanRef = (o) => {
    if (Array.isArray(o)) return o.map(cleanRef);
    if (!o || typeof o !== 'object') return o;
    const out = {};
    for (const k in o) {
      if (k.startsWith('_') || k === 'id') continue;
      out[k] = cleanRef(o[k]);
    }
    return out;
  };

  window.OaEdComposite = {
    KEYWORDS,
    _refs: null,
    _byType: null,

    async load(force) {
      if (this._refs && this._byType && !force) return this._refs;
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

      // Per widget TYPE: the richest library sample for that type, cleaned. Lets
      // the property editor surface every library-supported param (in red) even
      // when the placed instance only saved a few.
      const byType = {};
      for (const c of comps) {
        const t = String(c.type || '').toLowerCase();
        if (!t) continue;
        const n = countKeys(c.schema);
        if (!byType[t] || n > byType[t]._n) byType[t] = { schema: cleanRef(c.schema), _n: n };
      }
      this._byType = byType;
      return refs;
    },

    isSubWidget(key) { return Object.prototype.hasOwnProperty.call(KEYWORDS, key); },
    referenceFor(key) { return this._refs ? (this._refs[key] || null) : null; },

    /** Full library reference for a widget `type` (null if no library match). */
    referenceForType(type) {
      if (!this._byType || !type) return null;
      const e = this._byType[String(type).toLowerCase()];
      return e ? e.schema : null;
    },

    /** Merge for the TOP level: keep the instance's key ORDER (and values), then
     *  APPEND library-only keys after — so the saved layout is undisturbed and
     *  reference-only params surface (in red) at the end of each object. */
    mergeForType(ref, inst) {
      if (!ref || typeof ref !== 'object') return inst;
      if (!inst || typeof inst !== 'object' || Array.isArray(inst)) return inst;
      const out = {};
      for (const k of Object.keys(inst)) {
        if (ref[k] && typeof ref[k] === 'object' && !Array.isArray(ref[k]) &&
            inst[k] && typeof inst[k] === 'object' && !Array.isArray(inst[k])) {
          out[k] = this.mergeForType(ref[k], inst[k]);
        } else {
          out[k] = inst[k];
        }
      }
      for (const k of Object.keys(ref)) if (!(k in out)) out[k] = ref[k];
      return out;
    },

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
