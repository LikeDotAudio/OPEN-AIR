/**
 * Interface/layout_engine/preview_engine.jsx — live preview of the GUI JSON.
 * Mirrors oaGuiEditorWYSIWYG/Interface/layout_engine/preview_engine.py.
 *
 * Reuses the runtime renderer (LoaderOrchestrator + WidgetFactory), which emits
 * data-oca-path on every node — so the editor gets a pixel-accurate, selectable
 * preview for free. Root geometry constraints are stripped so the layout fills
 * the canvas fluidly instead of locking to a fixed size.
 */
(function () {
  window.OaEdPreview = ({ data }) => {
    const renderData = React.useMemo(() => {
      const d = window.OaEdState.deepClone(data || {});
      Object.values(d).forEach((node) => {
        if (node && node.geometry) {
          delete node.geometry.width;
          delete node.geometry.height;
          delete node.geometry.x;
          delete node.geometry.y;
        }
      });
      return d;
    }, [data]);

    if (!window.LoaderOrchestrator) {
      return <div style={{ color: '#f55', padding: 20 }}>Renderer (LoaderOrchestrator) not loaded.</div>;
    }
    // Flag editor context so data-driven containers (OcaArray) render a SINGLE
    // template instance instead of all N runtime copies.
    const Ctx = window.OaEdPreviewCtx;
    const tree = <window.LoaderOrchestrator layoutJson={renderData} />;
    return Ctx ? <Ctx.Provider value={true}>{tree}</Ctx.Provider> : tree;
  };
})();
