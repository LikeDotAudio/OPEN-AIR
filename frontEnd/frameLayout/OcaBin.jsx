// frameLayout/OcaBin.jsx — OcaBin structural container.
/**
 * Structural Component: OcaBin
 * A high-level container that manages background effects and scrolling.
 */
window.OcaBin = ({ nodeName, node, path_prefix, jsonPath }) => {
  const overflowEW = node.behavior?.overflow_ew === 'auto' ? 'auto' : 'hidden';
  const overflowNS = node.behavior?.overflow_ns === 'auto' ? 'auto' : 'hidden';

  return (
    <div className="oca-bin" style={{
        width: '100%',
        height: '100%',
        // Flex column so child blocks stack and the bin actually fills the
        // NSEW space declared in geometry. overflow_ns/ew then only scroll
        // when content genuinely exceeds the pane ("auto overflow as needed").
        display: 'flex',
        flexDirection: 'column',
        minHeight: 0,
        overflowX: overflowEW,
        overflowY: overflowNS,
        backgroundColor: '#121212',
        position: 'relative',
        padding: '0px',
        boxSizing: 'border-box'
    }}>
      {node.blocks && typeof node.blocks === 'object' && Object.entries(node.blocks).map(([k, v]) => (
        <window.WidgetFactory key={k} nodeName={k} node={v} path_prefix={`${path_prefix}/${nodeName}`} jsonPath={jsonPath ? `${jsonPath}.blocks.${k}` : undefined} />
      ))}
      {node.fields && typeof node.fields === 'object' && Object.entries(node.fields).map(([k, v]) => (
        <window.WidgetFactory key={k} nodeName={k} node={v} path_prefix={`${path_prefix}/${nodeName}`} jsonPath={jsonPath ? `${jsonPath}.fields.${k}` : undefined} />
      ))}
    </div>
  );
};
