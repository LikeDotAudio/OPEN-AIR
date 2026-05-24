// frameLayout/OcaBin.jsx — OcaBin structural container.
/**
 * Structural Component: OcaBin
 * A high-level container that manages background effects and scrolling.
 */
window.OcaBin = ({ nodeName, node, path_prefix, jsonPath }) => {
  const overflowEW = node.behavior?.overflow_ew === 'auto' ? 'auto' : 'hidden';
  const overflowNS = node.behavior?.overflow_ns === 'auto' ? 'auto' : 'hidden';

  // Global procedural panel "cover" rendered behind the bin's content. A page
  // declares its own via the established `background` key on the OcaBin (same
  // schema the Python panel generator used, e.g. background.parameters.*); we
  // also accept cosmetics.panel / panel. With none declared, the global default
  // (window.OA_PANEL_DEFAULT_CONFIG) is used. `enabled:false` opts a bin out.
  const PanelBg = window.Panel;
  const panelCfg = node.background ?? node.cosmetics?.panel ?? node.panel;
  const panelOff = panelCfg && panelCfg.enabled === false;
  const showPanel = !!PanelBg && !panelOff;

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
      {/* Background cover — absolute layer so it never disturbs the children's
          flex flow. pointerEvents:none keeps it click-through. */}
      {showPanel && (
        <PanelBg node={node} config={panelCfg}
          style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, zIndex: 0 }} />
      )}
      {/* Content layer above the cover. */}
      <div style={{ position: 'relative', zIndex: 1, display: 'flex', flexDirection: 'column', minHeight: 0, flex: '1 1 auto', width: '100%' }}>
        {node.blocks && typeof node.blocks === 'object' && Object.entries(node.blocks).map(([k, v]) => (
          <window.WidgetFactory key={k} nodeName={k} node={v} path_prefix={`${path_prefix}/${nodeName}`} jsonPath={jsonPath ? `${jsonPath}.blocks.${k}` : undefined} />
        ))}
        {node.fields && typeof node.fields === 'object' && Object.entries(node.fields).map(([k, v]) => (
          <window.WidgetFactory key={k} nodeName={k} node={v} path_prefix={`${path_prefix}/${nodeName}`} jsonPath={jsonPath ? `${jsonPath}.fields.${k}` : undefined} />
        ))}
      </div>
    </div>
  );
};
