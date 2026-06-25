/**
 * Interface/layout_engine/overlay_manager.jsx — designer overlays on the preview.
 * Mirrors oaGuiEditorWYSIWYG/Interface/layout_engine/overlay_manager.py +
 * overlays/selection_overlay.py.
 *
 * Draws a selection outline over the live preview by measuring the DOM element
 * for the selected path inside the canvas scroll container.
 */
(function () {
  window.OaEdSelectionOverlay = ({ containerRef, path, rev }) => {
    const [rect, setRect] = React.useState(null);

    const measure = React.useCallback(() => {
      const root = containerRef && containerRef.current;
      if (!root || !path) { setRect(null); return; }
      const el0 = window.OaEdFocus.elementForPath(root, path);
      if (!el0) { setRect(null); return; }
      // Outline the actual rendered control (firstElementChild), not the
      // full-width grid cell, so the selection box hugs the widget.
      const el = el0.firstElementChild || el0;
      const cr = root.getBoundingClientRect();
      const er = el.getBoundingClientRect();
      setRect({
        left: er.left - cr.left + root.scrollLeft,
        top: er.top - cr.top + root.scrollTop,
        width: er.width,
        height: er.height,
      });
    }, [containerRef, path]);

    React.useLayoutEffect(() => {
      measure();
      window.addEventListener('resize', measure);
      return () => window.removeEventListener('resize', measure);
    }, [measure, rev]);

    if (!rect) return null;
    return (
      <React.Fragment>
        <div style={{
          position: 'absolute', left: rect.left, top: rect.top,
          width: rect.width, height: rect.height,
          border: '2px solid #FF9900', boxShadow: '0 0 8px #FF990088',
          pointerEvents: 'none', zIndex: 30, boxSizing: 'border-box', borderRadius: '2px',
        }} />
        <div style={{
          position: 'absolute', left: rect.left, top: Math.max(0, rect.top - 16),
          background: '#FF9900', color: '#111', fontSize: '9px', fontWeight: 'bold',
          padding: '1px 5px', borderRadius: '2px', pointerEvents: 'none', zIndex: 31,
          whiteSpace: 'nowrap', maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis',
        }}>{String(path).split('.').pop()}</div>
      </React.Fragment>
    );
  };
})();
