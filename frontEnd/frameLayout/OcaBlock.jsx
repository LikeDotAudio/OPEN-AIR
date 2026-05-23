// frameLayout/OcaBlock.jsx — OcaBlock structural container.
/**
 * Structural Component: OcaBlock
 * A grouped set of controls with a grid layout.
 */
window.OcaBlock = ({ nodeName, node, path_prefix, jsonPath }) => {
  const [lang] = window.useMqttLang();
  const cols = node.layout_columns || 1;
  const title = node.description?.[lang] || node.description?.En || nodeName;

  return (
    <div className="oca-block" style={{
        margin: '0px',
        border: '1px solid #222',
        backgroundColor: '#1e1e1e',
        padding: '5px',
        borderRadius: '2px'
    }}>
      <div style={{ color: '#888', fontSize: '10px', borderBottom: '1px solid #222', marginBottom: '5px', fontWeight: 'bold', opacity: 0.8 }}>
        {title.toUpperCase()}
      </div>
      <div style={{
          display: 'grid',
          gridTemplateColumns: `repeat(${cols}, 1fr)`,
          gap: '5px'
      }}>
        {node.fields && typeof node.fields === 'object' && Object.entries(node.fields).map(([k, v]) => (
          <window.WidgetFactory key={k} nodeName={k} node={v} path_prefix={`${path_prefix}/${nodeName}`} jsonPath={jsonPath ? `${jsonPath}.fields.${k}` : undefined} />
        ))}
      </div>
    </div>
  );
};
