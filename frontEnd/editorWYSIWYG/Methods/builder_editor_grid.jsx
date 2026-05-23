/**
 * Methods/builder_editor_grid.jsx — diagnostic 100px grid background.
 * Mirrors oaGuiEditorWYSIWYG/Methods/builder_editor_grid.py.
 *
 * Returns a style object for a CSS grid backdrop, applied behind the preview.
 */
(function () {
  window.OaEdGrid = {
    style(grid = 100) {
      return {
        backgroundImage:
          'linear-gradient(to right, rgba(255,255,255,0.04) 1px, transparent 1px),' +
          'linear-gradient(to bottom, rgba(255,255,255,0.04) 1px, transparent 1px)',
        backgroundSize: `${grid}px ${grid}px, ${grid}px ${grid}px`,
      };
    },
  };
})();
