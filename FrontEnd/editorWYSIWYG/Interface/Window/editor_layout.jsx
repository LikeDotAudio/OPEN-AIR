
/**
 * Header: editor_layout.jsx
 * Purpose: Assembles the main work area layout for the WYSIWYG editor.
 * Description: This file implements the overall layout structure of the web editor, dividing the interface into three main panels: a left sidebar (for structure tree, raw JSON code, and a library grab bag), a central WYSIWYG canvas for visual editing, and a right sidebar for property inspection.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 * 
 * Interface/Window/editor_layout.jsx — assembles the editor work area.
 * Mirrors oaGuiEditorWYSIWYG/Interface/Window/editor_layout.py.
 *
 * Left sidebar: Structure (tree) / JSON (code) / Library (grab bag) tabs.
 * Center: the WYSIWYG canvas. Right: the property inspector.
 */
(function () {
  // Define the available tabs for the left sidebar pane
  const LEFT_TABS = [
    { id: 'structure', label: 'Structure', render: (store) => <window.OaEdTree store={store} /> },
    { id: 'code', label: 'JSON', render: (store) => <window.OaEdJsonEditor store={store} /> },
    { id: 'library', label: 'Library', render: (store) => <window.OaEdGrabBag store={store} /> },
  ];

  // Main Layout Component for the editor window
  window.OaEdLayout = ({ store }) => {
    // Local state to track which left sidebar tab is currently active
    const [tab, setTab] = React.useState('structure');
    // Resolve the currently active tab configuration
    const active = LEFT_TABS.find((t) => t.id === tab) || LEFT_TABS[0];

    return (
      <div style={{ display: 'flex', flex: 1, minHeight: 0, background: '#181818' }}>
        {/* left sidebar */}
        <div style={{ width: 290, flexShrink: 0, display: 'flex', flexDirection: 'column', borderRight: '1px solid #333', background: '#1c1c1c' }}>
          <div style={{ display: 'flex', flexShrink: 0, background: '#111' }}>
            {/* Render tab buttons dynamically based on LEFT_TABS config */}
            {LEFT_TABS.map((t) => (
              <button key={t.id} onClick={() => setTab(t.id)} style={{
                flex: 1, padding: '7px 4px', fontSize: 11, fontWeight: 'bold', cursor: 'pointer',
                background: tab === t.id ? '#1c1c1c' : 'transparent',
                color: tab === t.id ? '#FF9900' : '#999',
                border: 'none', borderBottom: tab === t.id ? '2px solid #FF9900' : '2px solid transparent',
              }}>{t.label}</button>
            ))}
          </div>
          <div style={{ flex: 1, minHeight: 0 }}>
            {/* Render the content of the currently active tab */}
            {active.render(store)}
          </div>
        </div>

        {/* center canvas */}
        <div style={{ flex: 1, minWidth: 0 }}>
          {/* The main interactive visual editing area */}
          <window.OaEdCanvas store={store} />
        </div>

        {/* right properties */}
        <div style={{ width: 310, flexShrink: 0, borderLeft: '1px solid #333', background: '#1c1c1c', display: 'flex', flexDirection: 'column' }}>
          <div style={{ padding: '7px 10px', fontSize: 11, fontWeight: 'bold', color: '#999', background: '#111', borderBottom: '1px solid #333' }}>PROPERTIES</div>
          <div style={{ flex: 1, minHeight: 0 }}>
            {/* Inspector for modifying properties of the selected element */}
            <window.OaEdProperties store={store} />
          </div>
        </div>
      </div>
    );
  };
})();
