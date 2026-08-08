/**
 * Header: ruler.jsx
 * Purpose: ruler component or utility.
 * Description: Handles logic and rendering for ruler component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

/**
 * Interface/layout_engine/ruler.jsx — horizontal/vertical PERCENT rulers.
 * Mirrors oaGuiEditorWYSIWYG/Interface/layout_engine/ruler.py.
 *
 * The web GUI is laid out in PERCENT of the panel (widgets use width:"100%" etc.),
 * so the ruler reads 0–120% rather than pixels. 100% == the canvas width/height,
 * which the ruler measures from its own box (it spans the same column as the
 * canvas). It runs to 120% to give a little overflow headroom past full width.
 */
(function () {
  const SIZE = 18;       // ruler thickness in px
  const MAX_PCT = 120;   // run a bit past 100% for overflow headroom
  const STEP_PCT = 10;   // major tick every 10%

  window.OaEdRuler = ({ orientation = 'h', scroll = 0, maxPct = MAX_PCT, step = STEP_PCT }) => {
    const horizontal = orientation === 'h';
    const ref = React.useRef(null);
    const [extent, setExtent] = React.useState(0); // px that equals 100%

    React.useEffect(() => {
      if (!ref.current || typeof ResizeObserver === 'undefined') return;
      const ro = new ResizeObserver(() => {
        const el = ref.current;
        if (!el) return;
        const px = horizontal ? el.clientWidth : el.clientHeight;
        if (px > 0) setExtent((p) => (p === px ? p : px));
      });
      ro.observe(ref.current);
      return () => ro.disconnect();
    }, [horizontal]);

    const ticks = [];
    if (extent > 0) {
      for (let pct = 0; pct <= maxPct; pct += step) {
        const pos = (pct / 100) * extent - scroll;
        ticks.push(
          <div key={pct} style={horizontal ? {
            position: 'absolute', left: pos, top: 0, height: '100%',
            borderLeft: '1px solid #444', paddingLeft: 2, fontSize: 8,
            color: pct === 100 ? '#FF9900' : '#777', whiteSpace: 'nowrap',
          } : {
            position: 'absolute', top: pos, left: 0, width: '100%',
            borderTop: '1px solid #444', paddingLeft: 2, fontSize: 8,
            color: pct === 100 ? '#FF9900' : '#777', whiteSpace: 'nowrap',
          }}>{pct}</div>
        );
      }
    }
    return (
      <div ref={ref} style={{
        position: 'relative', overflow: 'hidden', background: '#161616',
        flexShrink: 0, userSelect: 'none',
        ...(horizontal ? { height: SIZE, width: '100%' } : { width: SIZE, height: '100%' }),
      }}>{ticks}</div>
    );
  };

  window.OaEdRuler.SIZE = SIZE;
})();
