// frameLayout/WidgetFactory.jsx — recursive engine: container registry +
// layout/grid mapping + fallback. OcaBin/OcaBlock/FieldComponent/oaCssLen are
// split into sibling files (loaded before this in index.html).
/* Split out of WidgetFactory.jsx — one major concern per file. All pieces
   attach to window.* and reference each other lazily at render time, so the
   index.html load order among them is not critical (all load before render). */

/**
 * WidgetFactory: The recursive engine that translates JSON schema definitions 
 * into a dynamic React component tree. Handles component registry lookups, 
 * layout attribute mapping, and fallback rendering for unregistered types.
 */
window.WidgetFactory = ({ nodeName, node, path_prefix = '', jsonPath }) => {
  if (!node) return null;

  const COMPONENT_REGISTRY = {
    'OcaBin': window.OcaBin,
    'OcaBlock': window.OcaBlock,
    'OcaArray': window.OcaArray,
    // Collapsible block renders as a normal block for now (content shows; the
    // expand/collapse affordance is not yet implemented).
    'OcaCollapsibleBlock': window.OcaBlock,
    'OcaNotebook': window.TabLayout,
    'OcaSplit': window.SplitLayout,
    'OcaTable': window.OcaTable,
  };

  const ComponentToRender = COMPONENT_REGISTRY[node.type];

  // For toggler / multi-option button GROUPS, layout.width & layout.height are the
  // PER-BUTTON dimensions (consumed inside ButtonToggler), NOT the container size.
  // If we pin the wrapper to layout.height (e.g. 50px) the multi-row button grid
  // overflows it and overlaps the next block ("smooshed together"). So skip the
  // wrapper width/height for these and let FieldComponent's toggler branch size
  // the grid (height:auto). [[web-frontend-layout-quirks]]
  const _t = (node.type || '').toLowerCase();
  const _isButtonGroup = _t.includes('toggler')
    || ((_t.includes('button') || _t.includes('toggle') || _t.includes('actuator'))
        && node.options && typeof node.options === 'object'
        && Object.keys(node.options).length > 1);

  // Map JSON layout constraints to CSS Grid attributes for reactive container sizing
  const gridStyles = {
    gridColumnStart: node.layout?.column !== undefined ? node.layout.column : 'auto',
    gridRowStart: node.layout?.row !== undefined ? node.layout.row : 'auto',
    gridColumnEnd: node.layout?.col_span ? `span ${node.layout.col_span}` : 'auto',
    gridRowEnd: node.layout?.row_span ? `span ${node.layout.row_span}` : 'auto',
    // Flex semantics for when this widget is the child of a flex container
    // (e.g. an OcaBin column). 'weight' mirrors the desktop Tk grid weight:
    // 0 = size to content, >0 = grow to share leftover space. flexShrink:0
    // keeps content from being squished, which previously made stacked widgets
    // overlap their neighbours.
    flexGrow: node.layout?.weight !== undefined ? node.layout.weight
            : (node.layout?.weight_y !== undefined ? node.layout.weight_y : 0),
    flexShrink: 0,
    // Explicit width/height (px or %) belong on EVERY widget wrapper — including
    // keyword-routed ones (fader/meter/plot/graph/...), not just registered
    // containers. Without this a plot with layout.height:"100%" collapsed to its
    // min-height because the wrapper had no height for the % chain to resolve.
    ...((node.layout?.width != null && !_isButtonGroup) ? { width: window.oaCssLen(node.layout.width) } : {}),
    ...((node.layout?.height != null && !_isButtonGroup) ? { height: window.oaCssLen(node.layout.height), minHeight: 0 } : {}),
    // Tk grid padx/pady -> external spacing around the element within its cell.
    // box-sizing keeps the padding from overflowing fill containers.
    ...((node.layout?.padx != null || node.layout?.pady != null)
      ? { padding: `${node.layout?.pady ?? 0}px ${node.layout?.padx ?? 0}px`, boxSizing: 'border-box' }
      : {}),
  };

  // Containers declared NSEW must fill their parent so 'overflow: auto' only
  // scrolls when content truly exceeds the pane. The wrapper previously had no
  // height, collapsing every nested container to content height and breaking
  // the height:100% chain from the pane down to the OcaBin.
  const FILL_CONTAINERS = ['OcaBin', 'OcaNotebook', 'OcaSplit', 'OcaTable'];

  if (!ComponentToRender) {
    if (node.type && (
        node.type.startsWith('_') ||
        node.type.toLowerCase().includes('fader') ||
        node.type.toLowerCase().includes('meter') ||
        node.type.toLowerCase().includes('knob') ||
        node.type.toLowerCase().includes('selector') ||
        node.type.toLowerCase().includes('cmdp') ||
        node.type.toLowerCase().includes('mdp') ||
        node.type.toLowerCase().includes('button') ||
        node.type.toLowerCase().includes('actuator') ||
        node.type.toLowerCase().includes('checkbox') ||
        node.type.toLowerCase().includes('value') ||
        node.type.toLowerCase().includes('label') ||
        node.type.toLowerCase().includes('graph') ||
        node.type.toLowerCase().includes('plot') ||
        node.type.toLowerCase().includes('link') ||
        node.type.toLowerCase().includes('panel') ||
        node.type.toLowerCase().includes('screw') ||
        node.type.toLowerCase().includes('protocolconfig')
    )) {
        return (
            <div style={gridStyles} className={`widget-wrapper ${node.type}`} data-oca-path={jsonPath}>
                <window.FieldComponent nodeName={nodeName} node={node} path_prefix={path_prefix} />
            </div>
        );
    }
    return (
        <div style={{ border: '1px dashed #333', padding: '5px', margin: '2px' }} data-oca-path={jsonPath}>
            {node.blocks && typeof node.blocks === 'object' && Object.entries(node.blocks).map(([k, v]) => (
                <window.WidgetFactory key={k} nodeName={k} node={v} path_prefix={nodeName ? `${path_prefix}/${nodeName}` : path_prefix} jsonPath={jsonPath ? `${jsonPath}.blocks.${k}` : undefined} />
            ))}
            {node.fields && typeof node.fields === 'object' && Object.entries(node.fields).map(([k, v]) => (
                <window.WidgetFactory key={k} nodeName={k} node={v} path_prefix={nodeName ? `${path_prefix}/${nodeName}` : path_prefix} jsonPath={jsonPath ? `${jsonPath}.fields.${k}` : undefined} />
            ))}
        </div>
    );
  }

  // 4. Render the registered component
  let wrapperStyle = FILL_CONTAINERS.includes(node.type)
    ? { ...gridStyles, height: '100%', width: '100%', minHeight: 0, display: 'flex', flexDirection: 'column' }
    : gridStyles;

  // Explicit width/height (percent string or px number), e.g. set by the WYSIWYG
  // editor's resize handles. Only applied when present, so existing containers
  // that don't declare a size keep their fill/auto behavior.
  const _lw = node.layout?.width, _lh = node.layout?.height;
  if (_lw != null || _lh != null) {
    wrapperStyle = { ...wrapperStyle };
    if (_lw != null) wrapperStyle.width = window.oaCssLen(_lw);
    if (_lh != null) { wrapperStyle.height = window.oaCssLen(_lh); wrapperStyle.minHeight = 0; }
  }

  return (
    <div style={wrapperStyle} className={`widget-wrapper ${node.type}`} data-oca-path={jsonPath}>
      <ComponentToRender
        nodeName={nodeName}
        node={node}
        path_prefix={path_prefix}
        jsonPath={jsonPath}
      />
    </div>
  );
};
