/**
 * Header: TabLayout.jsx
 * Purpose: TabLayout component or utility.
 * Description: Handles logic and rendering for TabLayout component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

/**
 * TabLayout: Renders a tabbed "Notebook" interface.
 */
window.TabLayout = ({ nodeName, node, path_prefix, jsonPath }) => {
  const { tabs = {} } = node;
  const tabKeys = Object.keys(tabs);
  const [activeTab, setActiveTab] = React.useState(tabKeys[0]);

  return (
    <div className="tab-layout" style={{ display: 'flex', flexDirection: 'column', width: '100%', height: '100%' }}>
      {/* Tab Headers */}
      <div className="tab-headers" style={{ display: 'flex', background: '#222', borderBottom: '1px solid #444' }}>
        {tabKeys.map(key => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            style={{
              padding: '8px 15px',
              background: activeTab === key ? '#333' : 'transparent',
              color: activeTab === key ? '#FF9900' : '#888',
              border: 'none',
              borderBottom: activeTab === key ? '2px solid #FF9900' : 'none',
              cursor: 'pointer',
              fontSize: '13px',
              fontWeight: 'bold',
              textTransform: 'uppercase'
            }}
          >
            {tabs[key].label?.En || key}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="tab-content" style={{ flex: 1, overflow: 'auto', background: '#1a1a1a' }}>
        {activeTab && (
          <window.WidgetFactory
            nodeName={activeTab}
            node={tabs[activeTab]}
            path_prefix={nodeName ? `${path_prefix}/${nodeName}` : path_prefix}
            jsonPath={jsonPath ? `${jsonPath}.tabs.${activeTab}` : undefined}
          />
        )}
      </div>
    </div>
  );
};
