/**
 * Header: resize_handles.jsx
 * Purpose: resize_handles component or utility.
 * Description: Handles logic and rendering for resize_handles component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

/**
 * Interface/layout_engine/resize_handles.jsx — drag-to-stretch handles.
 * Mirrors oaGuiEditorWYSIWYG/Interface/overlays/sizing.py.
 *
 * Draws 8 handles around the selected element's visual box. Dragging a handle
 * resizes the element and writes layout.width / layout.height as a PERCENTAGE of
 * the element's containing block. Width is exact; height takes effect when the
 * container has a definite height (e.g. a block with weight, or a container
 * element). Integer-percent steps throttle re-renders.
 */
(function () {
  const HS = 9; // handle size (px)

  // name, fx, fy (anchor fraction), sx, sy (which edge moves: -1/0/+1)
  const DIRS = [
    ['nw', 0, 0, -1, -1], ['n', 0.5, 0, 0, -1], ['ne', 1, 0, 1, -1],
    ['w', 0, 0.5, -1, 0], ['e', 1, 0.5, 1, 0],
    ['sw', 0, 1, -1, 1], ['s', 0.5, 1, 0, 1], ['se', 1, 1, 1, 1],
  ];

  window.OaEdResizeHandles = ({ containerRef, path, rev, store }) => {
    const [box, setBox] = React.useState(null);
    const drag = React.useRef(null);

    const measure = React.useCallback(() => {
      const root = containerRef && containerRef.current;
      if (!root || !path) { setBox(null); return; }
      const el = window.OaEdFocus.elementForPath(root, path);
      if (!el) { setBox(null); return; }
      const visual = el.firstElementChild || el;
      const cr = root.getBoundingClientRect();
      const vr = visual.getBoundingClientRect();
      setBox({ left: vr.left - cr.left, top: vr.top - cr.top, width: vr.width, height: vr.height });
    }, [containerRef, path]);

    React.useLayoutEffect(() => { measure(); }, [measure, rev]);

    const pctOf = (v) => (typeof v === 'string' && v.trim().endsWith('%')) ? parseFloat(v) : null;
    const isPx = (v) => v != null && !(typeof v === 'string' && v.trim().endsWith('%'));

    const onMove = (e) => {
      const d = drag.current; if (!d) return;
      const dx = e.clientX - d.startX, dy = e.clientY - d.startY;
      // Preserve the unit: px handles (round) resize in px; % handles (square)
      // resize in % (current % scaled by how much the box grew/shrank).
      if (d.sx !== 0 && d.startW > 0) {
        if (d.pxW) {
          const v = Math.max(2, Math.round(d.startW + d.sx * dx));
          if (v !== d.lastW) { d.lastW = v; store.setProp(path, 'layout.width', v); }
        } else {
          const pct = Math.max(5, Math.min(400, Math.round(d.curW * (d.startW + d.sx * dx) / d.startW)));
          if (pct !== d.lastW) { d.lastW = pct; store.setProp(path, 'layout.width', pct + '%'); }
        }
      }
      if (d.sy !== 0 && d.startH > 0) {
        if (d.pxH) {
          const v = Math.max(2, Math.round(d.startH + d.sy * dy));
          if (v !== d.lastH) { d.lastH = v; store.setProp(path, 'layout.height', v); }
        } else {
          const pct = Math.max(5, Math.min(400, Math.round(d.curH * (d.startH + d.sy * dy) / d.startH)));
          if (pct !== d.lastH) { d.lastH = pct; store.setProp(path, 'layout.height', pct + '%'); }
        }
      }
    };
    const onUp = () => {
      drag.current = null;
      window.removeEventListener('pointermove', onMove);
      window.removeEventListener('pointerup', onUp);
    };
    const onDown = (e, sx, sy) => {
      e.preventDefault(); e.stopPropagation();
      const root = containerRef.current;
      const el = window.OaEdFocus.elementForPath(root, path); if (!el) return;
      const visual = el.firstElementChild || el;
      const vr = visual.getBoundingClientRect();
      const node = (store.getNode && store.getNode(path)) || {};
      drag.current = {
        startX: e.clientX, startY: e.clientY,
        startW: vr.width, startH: vr.height,
        curW: pctOf(node.layout && node.layout.width) ?? 100,
        curH: pctOf(node.layout && node.layout.height) ?? 100,
        pxW: isPx(node.layout && node.layout.width),
        pxH: isPx(node.layout && node.layout.height),
        sx, sy, lastW: null, lastH: null,
      };
      window.addEventListener('pointermove', onMove);
      window.addEventListener('pointerup', onUp);
    };

    if (!box) return null;
    // Handle shape indicates the unit: square = percentage, round dot = pixels.
    // (% / unset => square, since dragging writes %; explicit px => round.)
    const node = (store.getNode && store.getNode(path)) || {};
    const pxW = isPx(node.layout && node.layout.width);
    const pxH = isPx(node.layout && node.layout.height);
    return (
      <React.Fragment>
        {DIRS.map(([name, fx, fy, sx, sy]) => {
          const cW = sx !== 0, cH = sy !== 0;
          const px = (cW && cH) ? (pxW && pxH) : (cW ? pxW : pxH);
          return (
            <div key={name}
              onPointerDown={(e) => onDown(e, sx, sy)}
              style={{
                position: 'absolute', zIndex: 40, width: HS, height: HS,
                left: box.left + fx * box.width - HS / 2,
                top: box.top + fy * box.height - HS / 2,
                background: '#FF9900', border: '1px solid #111',
                borderRadius: px ? '50%' : 2,
                cursor: name + '-resize', touchAction: 'none',
              }} />
          );
        })}
      </React.Fragment>
    );
  };
})();
