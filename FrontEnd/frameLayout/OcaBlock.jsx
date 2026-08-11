/**
 * Header: OcaBlock.jsx
 * Purpose: OcaBlock component or utility.
 * Description: Handles logic and rendering for OcaBlock component or utility.
 * 
 * Version: 26.08.08.1
 * Change Log:
 * - 2026-08-08: A block with layout.weight>0 whose field wants a % height now
 *   stretches to give it one, instead of leaving the space around itself.
 * - 2026-07-05: Initial annotation and documentation added.
 */

// frameLayout/OcaBlock.jsx — OcaBlock structural container.
/**
 * Structural Component: OcaBlock
 * A grouped set of controls with a grid layout.
 */
window.OcaBlock = ({ nodeName, node, path_prefix, jsonPath }) => {
  const [lang] = window.useMqttLang();
  const cols = node.layout_columns || 1;
  const title = node.description?.[lang] || node.description?.En || nodeName;
  // A block titles itself via `description`; description.show_label toggles
  // whether that title row is displayed (default on).
  const showTitle = node.description?.show_label !== false;

  // `layout.weight > 0` is the desktop grid weight: this block takes the
  // leftover height instead of sizing to its contents. WidgetFactory already
  // grows the WRAPPER, but a block that does not spend that height leaves the
  // space open around itself — which is how the spectrum graph ended up pinned
  // at 420px above half a screen of dead panel.
  //
  // Weight alone is not enough to start stretching, because five blocks already
  // declare it while every field inside them is a fixed 30px tall (the DMM
  // readout, the four trace rows). Stretching those would only push their own
  // rows apart. A block fills when it grows AND something inside it asked for a
  // PERCENTAGE height — that field is the one with a use for the space.
  // A button is excluded even when it says "100%": its own widget reads that,
  // not the wrapper, so no amount of block height would reach it (the traces
  // tab's CONTINUOUS_MODE is exactly this case).
  const wantsHeight = (f) => typeof f?.layout?.height === 'string'
      && f.layout.height.trim().endsWith('%')
      && window.oaWrapperIsSized(f);
  const grows = (parseFloat(node.layout?.weight) || 0) > 0
      && Object.values(node.fields || {}).some(wantsHeight);

  let gridCols = `repeat(${cols}, 1fr)`;
  if (node.column_sizing && Array.isArray(node.column_sizing)) {
    gridCols = node.column_sizing.map(col => {
      const w = col.weight !== undefined ? col.weight : 1;
      const minW = col.minwidth ? `${col.minwidth}px` : '0px';
      return w > 0 ? `minmax(${minW}, ${w}fr)` : `minmax(${minW}, auto)`;
    }).join(' ');
  }
  // Responsive: collapse to fewer columns (and stack) when the container is too
  // narrow to fit `responsive_min`-wide tracks side by side.
  if (node.responsive) {
    const rmin = node.responsive_min || 600;
    gridCols = `repeat(auto-fit, minmax(min(100%, ${rmin}px), 1fr))`;
  }

  // Background goes through the transparency manager so the panel cover behind
  // the bin shows through (instead of an opaque box). Per-node override via
  // cosmetics.transparent / cosmetics.bg_opacity.
  const blockBg = window.OaTransparency
    ? window.OaTransparency.containerBg(node, '30,30,30', '#1e1e1e')
    : '#1e1e1e';

  return (
    <div className="oca-block" style={{
        position: 'relative',
        margin: '0px',
        border: 'none',
        backgroundColor: blockBg,
        padding: '0px',
        borderRadius: '2px',
        ...(grows ? { flex: '1 1 auto', minHeight: 0, display: 'flex', flexDirection: 'column' } : {})
    }}>
      {node.center_line && (
        <div style={{ position: 'absolute', top: 0, bottom: 0, left: '50%', width: node.center_line_width ? `${node.center_line_width}px` : '2px', background: node.center_line_color || 'rgba(0,0,0,0.5)', transform: 'translateX(-50%)', pointerEvents: 'none', zIndex: 0 }} />
      )}
      {showTitle && (
      <div style={{ color: '#888', fontSize: '10px', marginBottom: '0px', fontWeight: 'bold', opacity: 0.8, padding: '1px 3px' }}>
        {title.toUpperCase()}
      </div>
      )}
      {/* Grid gap: row_spacing / column_spacing (px) may live at the node level
          or under layout{}. Both default to 0 so existing blocks are unchanged. */}
      <div style={{
          display: 'grid',
          gridTemplateColumns: gridCols,
          rowGap: `${parseFloat(node.layout?.row_spacing ?? node.row_spacing ?? 0) || 0}px`,
          columnGap: `${parseFloat(node.layout?.column_spacing ?? node.column_spacing ?? 0) || 0}px`,
          // The grid is what the extra height is FOR: auto rows in a stretched
          // grid grow to fill it, so a `height: "100%"` field inside finally has
          // something to be a percentage of.
          ...(grows ? { flex: '1 1 auto', minHeight: 0 } : {})
      }}>
        {node.fields && typeof node.fields === 'object' && Object.entries(node.fields).map(([k, v]) => (
          <window.WidgetFactory key={k} nodeName={k} node={v} path_prefix={nodeName ? `${path_prefix}/${nodeName}` : path_prefix} jsonPath={jsonPath ? `${jsonPath}.fields.${k}` : undefined} />
        ))}
      </div>
    </div>
  );
};
