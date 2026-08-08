/**
 * Header: snap_logic.jsx
 * Purpose: snap_logic component or utility.
 * Description: Handles logic and rendering for snap_logic component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

/**
 * Interface/layout_engine/snap_logic.jsx — grid snapping math.
 * Mirrors oaGuiEditorWYSIWYG/Interface/layout_engine/snap_logic.py.
 */
(function () {
  window.OaEdSnap = {
    GRID: 100,
    snap(value, grid = 100) {
      if (typeof value !== 'number') return value;
      return Math.round(value / grid) * grid;
    },
    snapGeometry(geometry, grid = 100) {
      const g = { ...(geometry || {}) };
      ['x', 'y', 'width', 'height'].forEach((k) => {
        if (typeof g[k] === 'number') g[k] = this.snap(g[k], grid);
      });
      return g;
    },
  };
})();
