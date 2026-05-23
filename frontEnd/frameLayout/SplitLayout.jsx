/**
 * SplitLayout: Renders a container split into multiple panels.
 */
window.SplitLayout = ({ nodeName, node, path_prefix, jsonPath }) => {
  const { behavior, panels = {} } = node;
  const orientation = behavior?.orientation === 'horizontal' ? 'row' : 'column';

  return (
    <div 
      className={`split-layout ${behavior?.orientation || 'vertical'}`}
      style={{
        display: 'flex',
        flexDirection: orientation,
        width: '100%',
        height: '100%',
        gap: '2px',
        backgroundColor: '#222'
      }}
    >
      {Object.entries(panels).map(([key, panel]) => (
        <div 
          key={key} 
          style={{ 
            flex: panel.weight || 1, 
            overflow: 'hidden',
            backgroundColor: '#1a1a1a' 
          }}
        >
          <window.WidgetFactory
            nodeName={key}
            node={panel}
            path_prefix={`${path_prefix}/${nodeName}`}
            jsonPath={jsonPath ? `${jsonPath}.panels.${key}` : undefined}
          />
        </div>
      ))}
    </div>
  );
};
