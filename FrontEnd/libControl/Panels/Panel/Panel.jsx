/**
 * Panel — the global procedural background "cover".
 *
 * A self-contained <canvas> that measures its own box, asks the WASM engine
 * (window.OAPanels) for a finished RGBA texture at that exact pixel size, and
 * blits it behind whatever children it wraps. Screws auto-place themselves on
 * the cover inside the WASM call. Static (no animation, no MQTT) — it only
 * regenerates when the box size or the config changes.
 *
 * Config resolution (first hit wins):
 *   1. explicit `config` prop
 *   2. node.background  (the established panel key — same schema the Python
 *      generator used, e.g. background.parameters.*)
 *   3. node.cosmetics.panel  /  node.panel   (a page/container declaring its own)
 *   4. window.OA_PANEL_DEFAULT_CONFIG          (the global default)
 *
 * Usage:
 *   <Panel config={cfg}>{children}</Panel>   // background behind content
 *   <Panel node={node} />                     // standalone field widget
 */

// Cross-instance cache so re-mounts / identical containers don't regenerate.
// Keyed by "WxH|configJSON"; holds an ImageData ready to putImageData().
const _OA_PANEL_CACHE = (window._OA_PANEL_CACHE = window._OA_PANEL_CACHE || new Map());
const _OA_PANEL_CACHE_MAX = 48;

function _resolvePanelConfig(config, node) {
  if (config && typeof config === "object") return config;
  const fromNode = node?.background || node?.cosmetics?.panel || node?.panel;
  if (fromNode && typeof fromNode === "object") return fromNode;
  return window.OA_PANEL_DEFAULT_CONFIG || {};
}

const Panel = ({ config, node, children, style, className }) => {
  const cfg = _resolvePanelConfig(config, node);
  // Explicit { enabled:false } turns the cover off (renders children bare).
  const disabled = cfg && cfg.enabled === false;
  const cfgKey = React.useMemo(() => {
    try { return JSON.stringify(cfg); } catch (e) { return String(Math.random()); }
  }, [cfg]);

  const wrapRef = React.useRef(null);
  const canvasRef = React.useRef(null);
  const [box, setBox] = React.useState({ w: 0, h: 0 });

  // Measure the outer box (CSS px). Debounced so drag-resizing doesn't thrash
  // the WASM generator; rounds to even px to avoid 1px jitter loops.
  React.useEffect(() => {
    if (disabled || !wrapRef.current || typeof ResizeObserver === "undefined") return;
    let timer = null;
    const ro = new ResizeObserver((entries) => {
      const r = entries[0].contentRect;
      const w = Math.max(0, Math.round(r.width));
      const h = Math.max(0, Math.round(r.height));
      if (timer) clearTimeout(timer);
      timer = setTimeout(() => {
        setBox((p) => (p.w === w && p.h === h ? p : { w, h }));
      }, 90);
    });
    ro.observe(wrapRef.current);
    return () => { if (timer) clearTimeout(timer); ro.disconnect(); };
  }, [disabled]);

  // Generate + paint whenever size or config changes.
  React.useEffect(() => {
    if (disabled) return;
    const { w, h } = box;
    const canvas = canvasRef.current;
    if (!canvas || w < 2 || h < 2) return;

    let cancelled = false;
    const key = `${w}x${h}|${cfgKey}`;

    const paint = (imageData) => {
      if (cancelled) return;
      canvas.width = w;
      canvas.height = h;
      canvas.getContext("2d").putImageData(imageData, 0, 0);
    };

    const cached = _OA_PANEL_CACHE.get(key);
    if (cached) { paint(cached); return; }

    const engine = window.OAPanels;
    if (!engine) return; // wasm bundle not present — render children bare
    engine.ready
      .then(() => {
        if (cancelled) return;
        const bytes = engine.generatePanel(w, h, cfg); // Uint8Array RGBA
        const imageData = new ImageData(new Uint8ClampedArray(bytes.buffer, bytes.byteOffset, bytes.length), w, h);
        if (_OA_PANEL_CACHE.size >= _OA_PANEL_CACHE_MAX) {
          _OA_PANEL_CACHE.delete(_OA_PANEL_CACHE.keys().next().value);
        }
        _OA_PANEL_CACHE.set(key, imageData);
        paint(imageData);
      })
      .catch(() => { /* engine failed — leave background transparent */ });

    return () => { cancelled = true; };
  }, [box, cfgKey, disabled]);

  if (disabled) {
    return <div className={className} style={{ width: "100%", height: "100%", ...style }}>{children}</div>;
  }

  return (
    <div
      ref={wrapRef}
      className={className ? `oa-panel ${className}` : "oa-panel"}
      style={{ position: "relative", width: "100%", height: "100%", overflow: "hidden", ...style }}
    >
      <canvas
        ref={canvasRef}
        style={{ position: "absolute", top: 0, left: 0, width: "100%", height: "100%", display: "block", pointerEvents: "none", zIndex: 0 }}
      />
      <div style={{ position: "relative", zIndex: 1, width: "100%", height: "100%" }}>{children}</div>
    </div>
  );
};

window.Panel = Panel;
