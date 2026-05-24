/**
 * Interface/Tabs/InteractiveLayout/interactive_layout.jsx — the WYSIWYG canvas.
 * Mirrors oaGuiEditorWYSIWYG/Interface/Tabs/InteractiveLayout/interactive_layout.py.
 *
 * Renders the live preview (OaEdPreview) inside a scrollable, grid-backed canvas
 * with rulers. A transparent capture layer over the preview turns widget clicks
 * into element selection (instead of operating the control) and accepts palette
 * drops. The selection outline is drawn by OaEdSelectionOverlay.
 */
(function () {
  // Nearest container node path for an inserted/dropped element.
  const containerPathOf = (store, path) => {
    const data = store.getData();
    const rootKey = Object.keys(data)[0];
    if (!path) return rootKey;
    const node = store.getNode(path);
    if (node && (node.type === 'OcaBin' || node.type === 'OcaBlock' || node.blocks || node.fields)) return path;
    const parts = path.split('.');
    parts.pop(); // drop element key
    if (parts[parts.length - 1] === 'fields' || parts[parts.length - 1] === 'blocks') parts.pop();
    return parts.join('.') || rootKey;
  };

  window.OaEdCanvas = ({ store }) => {
    const st = window.useEditorStore(store);
    const innerRef = React.useRef(null);
    const [scroll, setScroll] = React.useState({ x: 0, y: 0 });
    const [showGrid, setShowGrid] = React.useState(true);
    const [dragOver, setDragOver] = React.useState(false);
    const [caret, setCaret] = React.useState(null);   // insertion cursor rect (move drag)
    const dragSrcRef = React.useRef(null);            // path of element being moved
    const dropTargetRef = React.useRef(null);         // last computed {destContainerPath, beforeKey}

    const selectAt = (clientX, clientY) => {
      const path = window.OaEdFocus.resolvePathAt(clientX, clientY);
      store.select(path || Object.keys(store.getData())[0]);
    };

    // Begin moving an existing canvas element (HTML5 drag from the capture layer).
    const onDragStart = (e) => {
      const p = window.OaEdFocus.resolvePathAt(e.clientX, e.clientY);
      const rootKey = Object.keys(store.getData())[0];
      if (!p || p === rootKey) { e.preventDefault(); return; } // don't drag the root frame
      dragSrcRef.current = p;
      store.select(p);
      try {
        e.dataTransfer.setData('application/x-oca-move', p);
        e.dataTransfer.effectAllowed = 'move';
        const el = window.OaEdFocus.elementForPath(innerRef.current, p);
        if (el) e.dataTransfer.setDragImage(el, 10, 10); // ghost = the widget itself
      } catch (_) { /* noop */ }
    };

    const onDragOver = (e) => {
      e.preventDefault();
      if (dragSrcRef.current && window.OaEdDragMove) {
        e.dataTransfer.dropEffect = 'move';
        const res = window.OaEdDragMove.compute(innerRef.current, store, e.clientX, e.clientY, dragSrcRef.current);
        dropTargetRef.current = res;
        setCaret(res ? res.caret : null);
      } else {
        setDragOver(true); // palette (library) drag
      }
    };

    const clearDrag = () => { dragSrcRef.current = null; dropTargetRef.current = null; setCaret(null); setDragOver(false); };

    const onDrop = (e) => {
      e.preventDefault();
      // Case A — moving an existing element.
      if (dragSrcRef.current) {
        const src = dragSrcRef.current;
        const res = dropTargetRef.current || window.OaEdDragMove.compute(innerRef.current, store, e.clientX, e.clientY, src);
        if (res) store.moveTo(src, res.destContainerPath, res.beforeKey);
        clearDrag();
        return;
      }
      // Case B — dropping a new widget from the Library palette.
      setDragOver(false);
      let comp = null;
      try { comp = JSON.parse(e.dataTransfer.getData('application/json')); } catch (_) { return; }
      if (!comp || !comp.schema) return;
      const hitPath = window.OaEdFocus.resolvePathAt(e.clientX, e.clientY);
      const container = containerPathOf(store, hitPath);
      store.insert(container, comp.schema, comp.name);
    };

    const RULER = (window.OaEdRuler && window.OaEdRuler.SIZE) || 18;

    return (
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: '#1a1a1a' }}>
        {/* mini toolbar */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '4px 8px', background: '#111', borderBottom: '1px solid #333', flexShrink: 0 }}>
          <span style={{ fontSize: 11, color: '#888', fontWeight: 'bold' }}>CANVAS</span>
          <label style={{ fontSize: 11, color: '#aaa', display: 'flex', alignItems: 'center', gap: 4 }}>
            <input type="checkbox" checked={showGrid} onChange={(e) => setShowGrid(e.target.checked)} /> grid
          </label>
          <span style={{ fontSize: 10, color: '#666', marginLeft: 'auto' }}>click a widget to select · drop from Library to add</span>
        </div>

        {/* top rulers */}
        <div style={{ display: 'flex', flexShrink: 0 }}>
          <div style={{ width: RULER, height: RULER, background: '#161616', flexShrink: 0 }} />
          <window.OaEdRuler orientation="h" scroll={scroll.x} />
        </div>

        {/* body: vertical ruler + scroll canvas */}
        <div style={{ display: 'flex', flex: 1, minHeight: 0 }}>
          <window.OaEdRuler orientation="v" scroll={scroll.y} />
          <div
            onScroll={(e) => setScroll({ x: e.target.scrollLeft, y: e.target.scrollTop })}
            style={{ flex: 1, minWidth: 0, overflow: 'auto', position: 'relative', background: '#202020' }}
          >
            <div ref={innerRef} style={{
              position: 'relative', width: '100%', minHeight: '100%',
              ...(showGrid ? window.OaEdGrid.style(10) : {}),
            }}>
              <window.OaEdPreview data={st.data} />

              {/* transparent capture + dropzone (also the drag source for moves) */}
              <div
                draggable
                onClick={(e) => selectAt(e.clientX, e.clientY)}
                onDragStart={onDragStart}
                onDragOver={onDragOver}
                onDragLeave={() => { if (!dragSrcRef.current) setDragOver(false); }}
                onDrop={onDrop}
                onDragEnd={clearDrag}
                style={{
                  position: 'absolute', inset: 0, zIndex: 10,
                  background: dragOver ? 'rgba(255,153,0,0.08)' : 'transparent',
                  outline: dragOver ? '2px dashed #FF9900' : 'none',
                }}
              />

              {/* insertion caret while dragging an element */}
              {caret && (
                <div style={{
                  position: 'absolute', left: caret.left, top: caret.top, width: caret.width, height: caret.height,
                  background: '#FF9900', boxShadow: '0 0 6px #FF9900', borderRadius: 2, zIndex: 20, pointerEvents: 'none',
                }} />
              )}

              <window.OaEdSelectionOverlay containerRef={innerRef} path={st.selectedPath} rev={st.rev} />
              {window.OaEdResizeHandles &&
                <window.OaEdResizeHandles containerRef={innerRef} path={st.selectedPath} rev={st.rev} store={store} />}
            </div>
          </div>
        </div>
      </div>
    );
  };

  window.OaEdCanvas.containerPathOf = containerPathOf;
})();
