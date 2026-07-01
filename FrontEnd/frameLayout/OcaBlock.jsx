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

  let gridCols = `repeat(${cols}, 1fr)`;
  if (node.column_sizing && Array.isArray(node.column_sizing)) {
    gridCols = node.column_sizing.map(col => {
      const w = col.weight !== undefined ? col.weight : 1;
      const minW = col.minwidth ? `${col.minwidth}px` : '0px';
      return w > 0 ? `minmax(${minW}, ${w}fr)` : `minmax(${minW}, auto)`;
    }).join(' ');
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
        borderRadius: '2px'
    }}>
      {node.center_line && (
        <div style={{ position: 'absolute', top: 0, bottom: 0, left: '50%', width: node.center_line_width ? `${node.center_line_width}px` : '2px', background: node.center_line_color || 'rgba(0,0,0,0.5)', transform: 'translateX(-50%)', pointerEvents: 'none', zIndex: 0 }} />
      )}
      {showTitle && (
      <div style={{ color: '#888', fontSize: '10px', marginBottom: '0px', fontWeight: 'bold', opacity: 0.8, padding: '1px 3px' }}>
        {title.toUpperCase()}
      </div>
      )}
      <div style={{
          display: 'grid',
          gridTemplateColumns: gridCols,
          gap: '0px'
      }}>
        {node.fields && typeof node.fields === 'object' && Object.entries(node.fields).map(([k, v]) => (
          <window.WidgetFactory key={k} nodeName={k} node={v} path_prefix={nodeName ? `${path_prefix}/${nodeName}` : path_prefix} jsonPath={jsonPath ? `${jsonPath}.fields.${k}` : undefined} />
        ))}
      </div>
    </div>
  );
};
