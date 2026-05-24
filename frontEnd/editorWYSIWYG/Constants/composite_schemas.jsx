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

  // Canonical "default declaration" for the structural containers. Their library
  // samples are minimal, so on their own they surface no red params. These unions
  // declare the full param set so a placed OcaBin/OcaBlock shows everything it can
  // carry (missing ones in red). Children collections (blocks/fields) are omitted.
  const STRUCTURAL = {
    ocabin: {
      type: 'OcaBin',
      geometry: { anchor: 'NSEW', x: 0, y: 0, width: '100%', height: '100%' },
      behavior: { overflow_ns: 'auto', overflow_ew: 'auto', fluid_ew: false, allow_scrolling: true, transparent: false },
      layout: { weight: 1, width: '100%', height: '100%', padx: 0, pady: 0, stretch: 'both' },
      description: { En: '', Fr: '', De: '', Es: '' },
    },
    ocablock: {
      type: 'OcaBlock',
      layout_columns: 1,
      column_sizing: [],
      geometry: { anchor: 'NSEW' },
      behavior: { overflow_ns: 'hidden', overflow_ew: 'hidden' },
      // A block titles itself via description; show_label lives INSIDE it and
      // toggles whether that title row is shown.
      description: { En: '', Fr: '', De: '', Es: '', show_label: true },
    },
  };

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
      const legends = data.legends || {};
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
      // Type ALIASES: any _LEGEND array listing widget-type names (e.g.
      // toggle_types: ["_SmartToggle","_GuiButtonToggle"]) is an equivalence group.
      // Register the group's richest sample under every alias so legacy type names
      // (_GuiButtonToggle, _GuiButtonToggler, …) resolve to the canonical sample
      // and show the same library/red params.
      for (const lv of Object.values(legends)) {
        if (!Array.isArray(lv)) continue;
        const names = lv.filter((x) => typeof x === 'string' && (x.startsWith('_') || x.startsWith('Oca')));
        if (names.length < 2) continue;
        let best = null;
        for (const name of names) {
          const e = byType[name.toLowerCase()];
          if (e && (!best || e._n > best._n)) best = e;
        }
        if (!best) continue;
        for (const name of names) {
          const key = name.toLowerCase();
          if (!byType[key]) byType[key] = best;
        }
      }
      this._byType = byType;
      return refs;
    },

    isSubWidget(key) { return Object.prototype.hasOwnProperty.call(KEYWORDS, key); },
    referenceFor(key) { return this._refs ? (this._refs[key] || null) : null; },

    /** Full library reference for a widget `type` (null if no library match).
     *  For structural containers, unions the minimal sample with the canonical
     *  STRUCTURAL declaration so the editor surfaces the full default param set. */
    referenceForType(type) {
      if (!type) return null;
      const t = String(type).toLowerCase();
      const e = this._byType ? this._byType[t] : null;
      const sample = e ? e.schema : null;
      const struct = STRUCTURAL[t];
      if (struct && sample) return this.mergeForType(struct, sample); // sample wins; struct adds the rest
      return sample || (struct ? JSON.parse(JSON.stringify(struct)) : null);
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
