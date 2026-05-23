/**
 * Methods/builder_editor_grid.jsx — diagnostic PERCENT grid background.
 * Mirrors oaGuiEditorWYSIWYG/Methods/builder_editor_grid.py.
 *
 * Returns a style object for a CSS grid backdrop applied behind the preview. The
 * cells are sized in PERCENT so they line up with the 0–120% ruler (each cell =
 * `pct`% of the canvas), keeping ruler and grid on the same scale.
 */
(function () {
  window.OaEdGrid = {
    style(pct = 10) {
      return {
        backgroundImage:
          'linear-gradient(to right, rgba(255,255,255,0.04) 1px, transparent 1px),' +
          'linear-gradient(to bottom, rgba(255,255,255,0.04) 1px, transparent 1px)',
        backgroundSize: `${pct}% ${pct}%, ${pct}% ${pct}%`,
      };
    },
  };
})();
