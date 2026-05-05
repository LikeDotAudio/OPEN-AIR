import React from 'react';
import SplitLayout from './SplitLayout';
import TabLayout from './TabLayout';

// Structural Component: OcaBin
// A high-level container that manages background effects and scrolling.
const OcaBin = ({ nodeName, node, path_prefix }) => {
  const overflowEW = node.behavior?.overflow_ew === 'auto' ? 'auto' : 'hidden';
  const overflowNS = node.behavior?.overflow_ns === 'auto' ? 'auto' : 'hidden';

  return (
    <div className="oca-bin" style={{ 
        width: '100%', 
        height: '100%', 
        overflowX: overflowEW, 
        overflowY: overflowNS,
        backgroundColor: '#121212',
        position: 'relative'
    }}>
      {/* Recursively render child blocks or fields */}
      {node.blocks && Object.entries(node.blocks).map(([k, v]) => (
        <WidgetFactory key={k} nodeName={k} node={v} path_prefix={`${path_prefix}/${nodeName}`} />
      ))}
      {node.fields && Object.entries(node.fields).map(([k, v]) => (
        <WidgetFactory key={k} nodeName={k} node={v} path_prefix={`${path_prefix}/${nodeName}`} />
      ))}
    </div>
  );
};

// Structural Component: OcaBlock
// A grouped set of controls with a grid layout.
const OcaBlock = ({ nodeName, node, path_prefix }) => {
  const cols = node.layout_columns || 1;
  const title = node.description?.En || nodeName;

  return (
    <div className="oca-block" style={{
        margin: '10px',
        border: '1px solid #333',
        backgroundColor: '#1e1e1e',
        padding: '10px'
    }}>
      <div style={{ color: '#888', fontSize: '12px', borderBottom: '1px solid #333', marginBottom: '10px', fontWeight: 'bold' }}>
        {title.toUpperCase()}
      </div>
      <div style={{
          display: 'grid',
          gridTemplateColumns: `repeat(${cols}, 1fr)`,
          gap: '10px'
      }}>
        {node.fields && Object.entries(node.fields).map(([k, v]) => (
          <WidgetFactory key={k} nodeName={k} node={v} path_prefix={`${path_prefix}/${nodeName}`} />
        ))}
      </div>
    </div>
  );
};

// Registry of available components
const COMPONENT_REGISTRY = {
  'OcaBin': OcaBin,
  'OcaBlock': OcaBlock,
  'OcaNotebook': TabLayout,
  'OcaSplit': SplitLayout,
};

/**
 * WidgetFactory: The recursive engine that translates JSON nodes into React components.
 */
const WidgetFactory = ({ nodeName, node, path_prefix = '' }) => {
  if (!node) return null;

  // 1. Identify the component type from the JSON
  const ComponentToRender = COMPONENT_REGISTRY[node.type];

  // 2. Handle Grid/Layout styles (for children inside an OcaBlock)
  const gridStyles = {
    gridColumnStart: node.layout?.column !== undefined ? node.layout.column : 'auto',
    gridRowStart: node.layout?.row !== undefined ? node.layout.row : 'auto',
    gridColumnEnd: node.layout?.col_span ? `span ${node.layout.col_span}` : 'auto',
    gridRowEnd: node.layout?.row_span ? `span ${node.layout.row_span}` : 'auto',
  };

  // 3. Fallback for unknown types or generic containers
  if (!ComponentToRender) {
    // If it's a leaf node starting with _, it's likely a control widget
    if (node.type && node.type.startsWith('_')) {
        return (
            <div style={gridStyles} className="mock-widget">
                <div style={{fontSize: '9px', color: '#666'}}>{node.type}</div>
                <div style={{color: '#aaa', fontWeight: 'bold'}}>{nodeName}</div>
            </div>
        );
    }

    return (
        <div style={{ border: '1px dashed #333', padding: '5px', margin: '2px' }}>
            {node.blocks && Object.entries(node.blocks).map(([k, v]) => (
                <WidgetFactory key={k} nodeName={k} node={v} path_prefix={`${path_prefix}/${nodeName}`} />
            ))}
            {node.fields && Object.entries(node.fields).map(([k, v]) => (
                <WidgetFactory key={k} nodeName={k} node={v} path_prefix={`${path_prefix}/${nodeName}`} />
            ))}
        </div>
    );
  }

  // 4. Render the registered component
  return (
    <div style={gridStyles} className={`widget-wrapper ${node.type}`}>
      <ComponentToRender 
        nodeName={nodeName}
        node={node} 
        path_prefix={path_prefix}
      />
    </div>
  );
};

export default WidgetFactory;
