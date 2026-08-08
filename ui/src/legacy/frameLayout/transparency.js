/**
 * Header: transparency.js
 * Purpose: transparency component or utility.
 * Description: Handles logic and rendering for transparency component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// frameLayout/transparency.js — central transparency / layering manager.
//
// With the procedural panel cover now rendered behind every OcaBin (see
// libControl/Panels), structural containers must NOT paint an opaque fill over
// it — otherwise the metal texture is hidden. This manager is the single place
// that decides how see-through each layer is, and guarantees content sits ABOVE
// the panel canvas. Components call window.OaTransparency.* instead of
// hard-coding background colors.
//
// Per-node overrides (read from the layout JSON):
//   cosmetics.transparent  /  behavior.transparent  -> fully transparent
//   cosmetics.bg_opacity   (0..1)                    -> explicit fill opacity
(function () {
  "use strict";

  window.OaTransparency = {
    // Global defaults (0 = fully see-through, 1 = opaque). Containers default to
    // a faint frost so text stays legible over busy metal while the panel still
    // reads through; bump/lower these to taste (or override per node).
    containerOpacity: 0.18,
    controlOpacity: 0.85,
    // z-index for the content layer that rides above a panel canvas.
    contentZ: 1,

    _clamp: function (v) { return Math.max(0, Math.min(1, v)); },

    // Resolve a container's background fill, honoring per-node overrides.
    // `rgb` is the base tint; `opaqueFallback` is used when opacity hits 1.
    containerBg: function (node, rgb, opaqueFallback) {
      rgb = rgb || "30,30,30";
      var c = (node && node.cosmetics) || {};
      var b = (node && node.behavior) || {};
      if (c.transparent === true || b.transparent === true) return "transparent";
      var op = (c.bg_opacity != null) ? c.bg_opacity : this.containerOpacity;
      op = this._clamp(op);
      if (op <= 0) return "transparent";
      if (op >= 1) return opaqueFallback || ("rgb(" + rgb + ")");
      return "rgba(" + rgb + ", " + op + ")";
    },

    // Same idea for interactive controls (kept more opaque for readability).
    controlBg: function (node, rgb, opaqueFallback) {
      rgb = rgb || "43,43,43";
      var c = (node && node.cosmetics) || {};
      if (c.transparent === true) return "transparent";
      var op = (c.bg_opacity != null) ? c.bg_opacity : this.controlOpacity;
      op = this._clamp(op);
      if (op <= 0) return "transparent";
      if (op >= 1) return opaqueFallback || ("rgb(" + rgb + ")");
      return "rgba(" + rgb + ", " + op + ")";
    },

    // Universal opt-in wrapper for ANY element's background value. Returns the
    // ORIGINAL value unchanged unless the node opts in, so wiring a component
    // through this is visually a no-op until someone sets:
    //   cosmetics.transparent : true        -> fully transparent
    //   cosmetics.bg_opacity  : 0..1         -> that opacity (hex value -> rgba)
    // `value` may be a hex string ("#222") or any CSS color/variable.
    bg: function (config, value) {
      var c = (config && config.cosmetics) || {};
      if (c.transparent === true) return "transparent";
      if (c.bg_opacity != null) {
        var op = this._clamp(c.bg_opacity);
        if (op <= 0) return "transparent";
        if (op >= 1) return value;
        var rgb = this._toRgb(value);
        if (rgb) return "rgba(" + rgb + ", " + op + ")";
      }
      return value;
    },

    // "#rgb" / "#rrggbb" -> "r,g,b" (null if not a hex string).
    _toRgb: function (v) {
      if (typeof v !== "string") return null;
      var h = v.trim();
      if (h.charAt(0) !== "#") return null;
      h = h.slice(1);
      if (h.length === 3) h = h.charAt(0)+h.charAt(0)+h.charAt(1)+h.charAt(1)+h.charAt(2)+h.charAt(2);
      if (h.length !== 6) return null;
      var n = parseInt(h, 16);
      if (isNaN(n)) return null;
      return ((n >> 16) & 255) + "," + ((n >> 8) & 255) + "," + (n & 255);
    }
  };
})();
