/**
 * Header: drag_move.jsx
 * Purpose: drag_move component or utility.
 * Description: Handles logic and rendering for drag_move component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

/**
 * Interface/layout_engine/drag_move.jsx — drag-to-reorder geometry for the canvas.
 *
 * Given the cursor position and the path of the element being dragged, works out
 * WHERE it would land (which container, before which sibling) and the screen
 * rectangle for the insertion caret. The canvas (interactive_layout) drives the
 * HTML5 drag events; this module is the pure geometry/targeting brain.
 *
 * Targeting rules (word-processor feel):
 *   - Over a leaf widget: insert BEFORE/AFTER it among its siblings, axis chosen
 *     from the parent's flex/grid direction (vertical Y-split, horizontal X-split).
 *   - Over the MIDDLE of a container (OcaBin/OcaBlock/…): drop INTO it (append).
 *   - Near a container's top/bottom EDGE: reorder it among ITS siblings instead.
 */
(function () {
  const esc = (s) => ((window.CSS && CSS.escape) ? CSS.escape(s) : String(s).replace(/"/g, '\\"'));
  const isContainerNode = (n) => !!(n && (
    n.type === 'OcaBin' || n.type === 'OcaBlock' || n.type === 'OcaArray' ||
    n.type === 'OcaCollapsibleBlock' || n.type === 'OcaNotebook' || n.type === 'OcaSplit' ||
    n.blocks || n.fields));

  window.OaEdDragMove = {
    /** @returns {null | {destContainerPath, beforeKey, into, caret:{left,top,width,height}}} */
    compute(innerEl, store, x, y, srcPath) {
      if (!innerEl || !window.OaEdState) return null;

      // Topmost element carrying a data-oca-path, skipping the dragged node + subtree.
      let hoverPath = null;
      for (const el of document.elementsFromPoint(x, y)) {
        const p = el.getAttribute && el.getAttribute('data-oca-path');
        if (!p) continue;
        if (srcPath && (p === srcPath || p.startsWith(srcPath + '.'))) continue;
        hoverPath = p; break;
      }
      if (!hoverPath) return null;

      const hoverEl = innerEl.querySelector(`[data-oca-path="${esc(hoverPath)}"]`);
      if (!hoverEl) return null;
      const r = hoverEl.getBoundingClientRect();
      const innerR = innerEl.getBoundingClientRect();
      const node = store.getNode(hoverPath);

      const parts = hoverPath.split('.');
      const hoveredKey = parts.pop();
      const collKey = parts.pop();            // 'fields' | 'blocks'
      const parentNodePath = parts.join('.'); // the container NODE that owns the collection

      const EDGE = Math.min(16, r.height * 0.3);
      const nearTop = y < r.top + EDGE;
      const nearBottom = y > r.bottom - EDGE;

      // Middle of a container → drop INTO it (append at end).
      if (isContainerNode(node) && !nearTop && !nearBottom) {
        return {
          destContainerPath: hoverPath,
          beforeKey: null,
          into: true,
          caret: { left: r.left - innerR.left + 4, top: r.bottom - innerR.top - 7, width: Math.max(8, r.width - 8), height: 3 },
        };
      }

      // Otherwise insert before/after the hovered element among its siblings.
      const parentEl = hoverEl.parentElement;
      const cs = parentEl ? getComputedStyle(parentEl) : null;
      const horizontal = !!(cs && (cs.display.indexOf('grid') !== -1 || cs.flexDirection.indexOf('row') === 0));
      const before = horizontal ? (x < r.left + r.width / 2) : (y < r.top + r.height / 2);

      const coll = store.getNode(`${parentNodePath}.${collKey}`) || {};
      const keys = Object.keys(coll);
      const idx = keys.indexOf(hoveredKey);
      const beforeKey = before ? hoveredKey : (keys[idx + 1] || null);

      let caret;
      if (horizontal) {
        const cx = before ? r.left : r.right;
        caret = { left: cx - innerR.left - 1, top: r.top - innerR.top, width: 3, height: r.height };
      } else {
        const cy = before ? r.top : r.bottom;
        caret = { left: r.left - innerR.left, top: cy - innerR.top - 1, width: r.width, height: 3 };
      }
      return { destContainerPath: parentNodePath, beforeKey, into: false, caret };
    },
  };
})();
