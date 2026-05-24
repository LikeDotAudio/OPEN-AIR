// frameLayout/OcaBin.jsx — OcaBin structural container.
/**
 * Structural Component: OcaBin
 * A high-level container that manages background effects and scrolling.
 */
// Context tracks whether an ANCESTOR already painted a panel cover, so the
// global default only renders on the top-level bin (nested bins don't stack).
const _OaPanelCtx = window.OaPanelContext || (window.OaPanelContext = React.createContext(false));

window.OcaBin = ({ nodeName, node, path_prefix, jsonPath }) => {
  const overflowEW = node.behavior?.overflow_ew === 'auto' ? 'auto' : 'hidden';
  const overflowNS = node.behavior?.overflow_ns === 'auto' ? 'auto' : 'hidden';

  // Panel cover. A page/container declares its own via `background` (or
  // cosmetics.panel / panel) and that ALWAYS paints (and overrides). The GLOBAL
  // default (window.OA_PANEL_DEFAULT_CONFIG) paints only on the TOP-LEVEL bin —
  // i.e. when no ancestor already has one — so nested bins don't stack covers.
  // `enabled:false` opts a bin out entirely.
  const PanelBg = window.Panel;
  const ancestorHasPanel = React.useContext(_OaPanelCtx);
  const explicitCfg = node.background ?? node.cosmetics?.panel ?? node.panel;
  const panelOff = explicitCfg && explicitCfg.enabled === false;
  const hasExplicit = !!explicitCfg && !panelOff;
  const renderPanel = !!PanelBg && !panelOff && (hasExplicit || !ancestorHasPanel);

  // Build the child render list. Tolerate the legacy/demo shape
  // `blocks: { fields: {...} }` by hoisting those into real fields (so they
  // render as widgets, not a dashed fallback box) while keeping their true
  // JSON path (blocks.fields.*) for the editor.
  const children = [];
  const rawBlocks = (node.blocks && typeof node.blocks === 'object') ? node.blocks : {};
  const hoist = rawBlocks.fields && typeof rawBlocks.fields === 'object' && !rawBlocks.fields.type;
  for (const [k, v] of Object.entries(rawBlocks)) {
    if (hoist && k === 'fields') continue; // handled as fields below
    children.push({ key: `b:${k}`, k, v, path: jsonPath ? `${jsonPath}.blocks.${k}` : undefined });
  }
  if (hoist) {
    for (const [k, v] of Object.entries(rawBlocks.fields)) {
      children.push({ key: `bf:${k}`, k, v, path: jsonPath ? `${jsonPath}.blocks.fields.${k}` : undefined });
    }
  }
  if (node.fields && typeof node.fields === 'object') {
    for (const [k, v] of Object.entries(node.fields)) {
      children.push({ key: `f:${k}`, k, v, path: jsonPath ? `${jsonPath}.fields.${k}` : undefined });
    }
  }

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
      {renderPanel && (
        <PanelBg node={node} config={explicitCfg || undefined}
          style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, zIndex: 0 }} />
      )}
      {/* Content layer above the cover. Descendants learn (via context) that a
          panel already exists here, so they skip the global default. */}
      <_OaPanelCtx.Provider value={ancestorHasPanel || renderPanel}>
        <div style={{ position: 'relative', zIndex: 1, display: 'flex', flexDirection: 'column', minHeight: 0, flex: '1 1 auto', width: '100%' }}>
          {children.map(({ key, k, v, path }) => (
            <window.WidgetFactory key={key} nodeName={k} node={v} path_prefix={`${path_prefix}/${nodeName}`} jsonPath={path} />
          ))}
        </div>
      </_OaPanelCtx.Provider>
    </div>
  );
};
