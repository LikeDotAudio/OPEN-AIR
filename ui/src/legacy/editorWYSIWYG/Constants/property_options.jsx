/**
 * Header: property_options.jsx
 * Purpose: property_options component or utility.
 * Description: Handles logic and rendering for property_options component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

/**
 * Constants/property_options.jsx — enum lookup for property fields.
 *
 * The widget library declares allowed enum values in each sample.json `_LEGEND`
 * block (visualization_types, knob_styles, pointer_styles, …). The server merges
 * them and serves them at /api/grabbag → { legends }. This module resolves a
 * property path (e.g. "cosmetics.visualization") to its option array so the
 * property editor can render a dropdown instead of free text.
 *
 * To make a NEW property a dropdown: add a `_LEGEND` array to the relevant
 * widget's sample.json (and, if its name isn't auto-resolved, an alias below).
 */
(function () {
  window.OaEdEnum = {
    _legends: null,

    // property key (or "parentKey.key") -> legend key, for names that don't
    // auto-resolve by suffix.
    ALIAS: {
      'visualization': 'visualization_types',
      'knob_style': 'knob_styles',
      'shape': 'knob_shapes',
      'pointer.style': 'pointer_styles',
      'scale.style': 'scale_styles', // faders use scale_styles, but they match tick_styles
      'scale.sides': 'scale_sides',
      'sides': 'scale_sides',
      'tick_style': 'tick_styles',
      'orientation': 'orientations',
      'law': 'laws',
      'ballistics': 'ballistics',
      'label_position': 'label_positions',
      'selection_mode': 'selection_modes',
      'font_style': 'font_styles',
      'active_font_style': 'font_styles',
      'inactive_font_style': 'font_styles',
      'mode': 'meter_modes',
      'unit_position': 'unit_positions',
      'tick_label_position': 'tick_label_positions',
      'overlay_type': 'overlay_types',
      'aperture': 'aperture_masks',
      'aperture_mask': 'aperture_masks',
      'bezel': 'bezel_shapes',
      'bezel_shape': 'bezel_shapes',
    },

    async load(force) {
      if (this._legends && !force) return this._legends;
      const data = await window.OaEdGrabBagLoader.load(force);
      this._legends = data.legends || {};
      return this._legends;
    },

    /** Options array for a dot-path property key, or null if it isn't an enum. */
    optionsFor(keyPath) {
      const legends = this._legends;
      if (!legends) return null;
      const parts = String(keyPath).split('.');
      const key = parts[parts.length - 1];
      const parent = parts.length > 1 ? parts[parts.length - 2] : null;
      const pick = (name) => (name && Array.isArray(legends[name]) && legends[name].length ? legends[name] : null);

      if (parent) { const r = pick(this.ALIAS[`${parent}.${key}`]); if (r) return r; }
      const aliased = pick(this.ALIAS[key]); if (aliased) return aliased;
      for (const suf of ['', 's', 'es', '_types', '_styles', '_positions', '_modes', '_shapes', '_masks']) {
        const r = pick(key + suf); if (r) return r;
      }
      return null;
    },
  };
})();
