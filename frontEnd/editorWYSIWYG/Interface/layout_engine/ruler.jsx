/**
 * Interface/layout_engine/ruler.jsx — horizontal/vertical pixel rulers.
 * Mirrors oaGuiEditorWYSIWYG/Interface/layout_engine/ruler.py.
 */
(function () {
  const SIZE = 18; // ruler thickness in px

  window.OaEdRuler = ({ orientation = 'h', length = 4000, grid = 100, scroll = 0 }) => {
    const horizontal = orientation === 'h';
    const ticks = [];
    for (let pos = 0; pos <= length; pos += grid) {
      ticks.push(
        <div key={pos} style={horizontal ? {
          position: 'absolute', left: pos - scroll, top: 0, height: '100%',
          borderLeft: '1px solid #444', paddingLeft: 2, fontSize: 8, color: '#777',
        } : {
          position: 'absolute', top: pos - scroll, left: 0, width: '100%',
          borderTop: '1px solid #444', paddingLeft: 2, fontSize: 8, color: '#777',
        }}>{pos}</div>
      );
    }
    return (
      <div style={{
        position: 'relative', overflow: 'hidden', background: '#161616',
        flexShrink: 0, userSelect: 'none',
        ...(horizontal ? { height: SIZE, width: '100%' } : { width: SIZE, height: '100%' }),
      }}>{ticks}</div>
    );
  };

  window.OaEdRuler.SIZE = SIZE;
})();
