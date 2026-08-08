/**
 * Header: Entry.jsx
 * Purpose: Entry component or utility.
 * Description: Handles logic and rendering for Entry component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

/**
 * Interface/Tabs/TreeRefactor/Entry.jsx — hierarchical structure tree.
 * Mirrors oaGuiEditorWYSIWYG/Interface/Tabs/TreeRefactor/Entry.py.
 *
 * Shows the nested blocks/fields hierarchy. Click selects; ↑/↓ reorder within a
 * parent; ✕ deletes; drag a node onto a container node to relocate it.
 */
(function () {
  const isContainer = (node) =>
    node && (node.type === 'OcaBin' || node.type === 'OcaBlock' || node.type === 'OcaNotebook' || node.blocks || node.fields);

  const childrenOf = (node, path) => {
    const out = [];
    ['blocks', 'fields'].forEach((coll) => {
      if (node && node[coll] && typeof node[coll] === 'object') {
        for (const [k, v] of Object.entries(node[coll])) {
          out.push({ key: k, childPath: `${path}.${coll}.${k}`, node: v });
        }
      }
    });
    return out;
  };

  const TreeNode = ({ nodeKey, node, path, store, selectedPath, depth }) => {
    const [open, setOpen] = React.useState(depth < 2);
    const kids = childrenOf(node, path);
    const selected = selectedPath === path;

    return (
      <div>
        <div
          draggable
          onDragStart={(e) => { e.stopPropagation(); e.dataTransfer.setData('text/oca-move', path); }}
          onDragOver={(e) => { if (isContainer(node)) { e.preventDefault(); e.stopPropagation(); } }}
          onDrop={(e) => {
            const src = e.dataTransfer.getData('text/oca-move');
            if (src && isContainer(node)) { e.preventDefault(); e.stopPropagation(); store.move(src, path); }
          }}
          onClick={(e) => { e.stopPropagation(); store.select(path); }}
          style={{
            display: 'flex', alignItems: 'center', gap: 3, cursor: 'pointer',
            padding: '2px 4px', paddingLeft: 4 + depth * 12,
            background: selected ? '#3a2f12' : 'transparent',
            borderLeft: selected ? '2px solid #FF9900' : '2px solid transparent',
            fontSize: 11, color: selected ? '#FF9900' : '#cfcfcf',
          }}
        >
          <span style={{ width: 10, color: '#888' }}
            onClick={(e) => { e.stopPropagation(); setOpen(!open); }}>
            {kids.length ? (open ? '▾' : '▸') : '·'}
          </span>
          <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {nodeKey}
            <span style={{ color: '#666', marginLeft: 5 }}>{node && node.type ? node.type : ''}</span>
          </span>
          <span className="oa-tree-actions" style={{ display: 'flex', gap: 2 }}>
            <button onClick={(e) => { e.stopPropagation(); store.reorder(path, -1); }} style={miniBtn}>↑</button>
            <button onClick={(e) => { e.stopPropagation(); store.reorder(path, +1); }} style={miniBtn}>↓</button>
            <button onClick={(e) => { e.stopPropagation(); store.deleteNode(path); }} style={{ ...miniBtn, color: '#f88' }}>✕</button>
          </span>
        </div>
        {open && kids.map((c) => (
          <TreeNode key={c.childPath} nodeKey={c.key} node={c.node} path={c.childPath}
            store={store} selectedPath={selectedPath} depth={depth + 1} />
        ))}
      </div>
    );
  };

  const miniBtn = { background: 'transparent', border: 'none', color: '#888', cursor: 'pointer', fontSize: 10, padding: '0 2px' };

  window.OaEdTree = ({ store }) => {
    const st = window.useEditorStore(store);
    const entries = Object.entries(st.data || {});
    return (
      <div style={{ height: '100%', overflow: 'auto', padding: '4px 0' }}>
        {entries.map(([k, v]) => (
          <TreeNode key={k} nodeKey={k} node={v} path={k} store={store} selectedPath={st.selectedPath} depth={0} />
        ))}
        {entries.length === 0 && <div style={{ color: '#777', fontSize: 11, padding: 10 }}>Empty document.</div>}
      </div>
    );
  };
})();
