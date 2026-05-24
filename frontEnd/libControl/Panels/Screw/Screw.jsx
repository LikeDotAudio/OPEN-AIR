/**
 * Screw — a single procedural Robertson screw head, rendered by the WASM engine
 * (window.OAPanels). The Panel cover auto-places its own screws; this component
 * is for dropping a standalone screw explicitly into a layout.
 *
 * Config (under cosmetics.screw, or top-level on the node, or the `config` prop):
 *   size_px   number  head diameter in px (default 24)
 *   type      "fillister" | "countersunk"
 *   finish    "chrome" | "black" | "custom"
 *   color     hex (when finish=custom)
 *   angle     drive rotation in degrees
 *   damage    0..1   screwdriver slippage wear
 *   rust      0..1   oxide accumulation
 */
const Screw = ({ config, node }) => {
  const cfg = (config && typeof config === "object")
    ? config
    : (node?.cosmetics?.screw || node?.screw || node || {});

  const size = Math.max(6, parseInt(cfg.size_px ?? node?.geometry?.width ?? 24, 10) || 24);
  const cfgKey = React.useMemo(() => {
    try { return JSON.stringify({ ...cfg, size }); } catch (e) { return String(size); }
  }, [cfg, size]);

  const canvasRef = React.useRef(null);

  React.useEffect(() => {
    const canvas = canvasRef.current;
    const engine = window.OAPanels;
    if (!canvas || !engine) return;
    let cancelled = false;
    engine.ready
      .then(() => {
        if (cancelled) return;
        const dim = engine.screwCanvasDim(size);
        const bytes = engine.generateScrew(size, cfg);
        canvas.width = dim;
        canvas.height = dim;
        const imageData = new ImageData(new Uint8ClampedArray(bytes.buffer, bytes.byteOffset, bytes.length), dim, dim);
        canvas.getContext("2d").putImageData(imageData, 0, 0);
      })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [cfgKey, size]);

  // Canvas includes 40% padding around the head (for the drop shadow); render it
  // at its natural size so the head reads at `size_px`.
  return <canvas ref={canvasRef} style={{ display: "block", pointerEvents: "none" }} />;
};

window.Screw = Screw;
