/**
 * Header: OcaBin.jsx
 * Purpose: OcaBin component or utility.
 * Description: Handles logic and rendering for OcaBin component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// frameLayout/OcaBin.jsx — OcaBin structural container.
/**
 * Structural Component: OcaBin
 * A high-level container that manages background effects and scrolling.
 */
// Context tracks whether an ANCESTOR already painted a panel cover, so the
// global default only renders on the top-level bin (nested bins don't stack).
const _OaPanelCtx = window.OaPanelContext || (window.OaPanelContext = React.createContext(false));

window.OcaBin = ({ nodeName, node, path_prefix, jsonPath }) => {
  const scaleToFit = node.behavior?.scale_to_fit === true;
  // If scale_to_fit is true, we must hide overflow to prevent scrollbars from the unscaled DOM layout.
  const overflowEW = scaleToFit ? 'hidden' : (node.behavior?.overflow_ew === 'auto' ? 'auto' : 'hidden');
  const overflowNS = scaleToFit ? 'hidden' : (node.behavior?.overflow_ns === 'auto' ? 'auto' : 'hidden');

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

  const containerRef = React.useRef(null);
  const contentRef = React.useRef(null);
  const [scale, setScale] = React.useState(1);

  React.useLayoutEffect(() => {
    if (!scaleToFit || !containerRef.current || !contentRef.current) return;
    const ro = new window.ResizeObserver(() => {
      const container = containerRef.current;
      const content = contentRef.current;
      if (!container || !content) return;
      
      const cw = container.clientWidth;
      const ch = container.clientHeight;
      
      // Temporarily remove transform to measure natural unscaled size
      const oldTransform = content.style.transform;
      content.style.transform = 'none';
      
      const nw = content.scrollWidth;
      const nh = content.scrollHeight;
      
      let newScale = 1;
      if (nw > 0 && nh > 0) {
        const scaleX = cw / nw;
        const scaleY = ch / nh;
        newScale = Math.min(scaleX, scaleY);
        // Usually we only want to scale down to fit, not scale up infinitely.
        // But if they want it to "fit inside", scaling up slightly might be desired,
        // let's cap it at 1.0 to avoid pixelation, or maybe let it scale up? 
        // We'll cap at 1.0 so it just shrinks when needed.
        if (newScale > 1) newScale = 1;
      }
      
      content.style.transform = oldTransform;
      setScale(newScale);
    });
    
    ro.observe(containerRef.current);
    ro.observe(contentRef.current);
    return () => ro.disconnect();
  }, [scaleToFit]);

  return (
    <div className="oca-bin" ref={containerRef} style={{
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
        <div ref={contentRef} style={{ 
            position: 'relative', 
            zIndex: 1, 
            display: 'flex', 
            flexDirection: 'column', 
            minHeight: 0, 
            flex: scaleToFit ? 'none' : '1 1 auto', 
            width: scaleToFit ? 'max-content' : '100%',
            transform: scaleToFit ? `scale(${scale})` : 'none',
            transformOrigin: 'top left',
            // Center it if it's scaled down
            margin: scaleToFit && scale < 1 ? '0 auto' : '0'
        }}>
          {children.map(({ key, k, v, path }) => (
            <window.WidgetFactory key={key} nodeName={k} node={v} path_prefix={nodeName ? `${path_prefix}/${nodeName}` : path_prefix} jsonPath={path} />
          ))}
        </div>
      </_OaPanelCtx.Provider>
    </div>
  );
};
