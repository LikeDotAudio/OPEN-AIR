/**
 * Header: NeedleMeter.jsx
 * Purpose: NeedleMeter component or utility.
 * Description: Handles logic and rendering for NeedleMeter component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

/**
 * NeedleMeter Component
 * Author: Anthony Peter Kuzub / Gemini (Collaborator)
 * Version: 20260524.0300.0
 *
 * Analog needle meter with ballistics, tilt (center/viewable angle + direction),
 * color-zone limits, transparency, and the full set of procedural bezel "window"
 * shapes ported from oaRustCore/oa_needle_geometry_rs (gem, super_gem, octagon,
 * triangle, pyramid, hex, hotdog/cylinder, squircle/squimonde/squectangle,
 * trapezoid/badge, crest/shield, parking_meter, stereo_diamond,
 * intersecting_overlay). Shapes are scaled-to-fit the widget box (the desktop
 * grows the canvas instead; the web fits it).
 */

// --- Bezel shape geometry (ported from oa_needle_geometry_rs) -----------------
// Each builder returns math points [[x, y], ...] (y up), pivot at (0,0), built
// at a base radius R0; we scale-to-fit afterward. yShift moves the body up.
const R0 = 100;
const _Y = { hotdog: 1.30, pyramid: 0.5, triangle: 0.5, parking_meter: 0.5, hex: 0.5, octagon: 0.9, squircle: 0.4, squimonde: 0.014, squectangle: 0.4, crest: 0.2, badge: 0.3, trapezoid: 0.3, gem: 0.5, super_gem: 0.5, stereo_diamond: 0.0, intersecting_overlay: 0.0, default: 0.0 };
// constants (from oaGuiElements meter_needle constants.py)
const C = {
  GEM_EXP: 3.06, GEM_W: 0.51, GEM_BASE_H: 0.3, GEM_SH_W: 0.69, GEM_SH_H: 0.6, GEM_PEAK_H: 0.98,
  HEX_EXP: 1.4, HEX_TW: 1.2, HEX_MW: 1.8, HEX_MH: 0.8, HEX_TH: 1.8,
  OCT_EXP: 1.4, TRI_EXP: 4.32, TRI_BW: 1.8, TRI_PH: 1.7,
  PM_EXP: 4.32, PY_EXP: 4.32, PY_BW: 1.8, PY_PH: 1.7,
  HOT_WS: 1.9, HOT_CR: 1.01, HOT_CY: 1.01, CYL_WS: 1.2, CYL_CR: 0.65, CYL_CY: 0.6, CYL_STEPS: 10,
  SQ_N: 3.5, SQ_W: 1.0, SQ_H: 1.0, SQ_STEPS: 40, SQT_W: 1.7, SQT_H: 0.85,
  TZ_TW: 1.6, TZ_TH: 1.6, TZ_BW: 1.3,
  CR_STEPS: 15, CR_TW: 1.5, CR_TH: 1.76, CR_BH: 0.6,
  SD_W: 1.4, SD_H: 1.0, SD_FW: 0.6,
  IO_W: 1.77, IO_H: 1.0, IO_SK: 0.3, IO_CR: 0.4,
};

const SHAPE_BUILDERS = {
  gem: (r, ys) => { const g = r * C.GEM_EXP; return [[0, C.GEM_BASE_H*g+ys], [C.GEM_W*g, C.GEM_BASE_H*g+ys], [C.GEM_SH_W*g, C.GEM_SH_H*g+ys], [0, C.GEM_PEAK_H*g+ys], [-C.GEM_SH_W*g, C.GEM_SH_H*g+ys], [-C.GEM_W*g, C.GEM_BASE_H*g+ys]]; },
  super_gem: (r, ys) => { const g = r * C.GEM_EXP; return [[0, -(C.GEM_BASE_H*g)+ys], [C.GEM_W*g, -(C.GEM_BASE_H*g)+ys], [C.GEM_SH_W*g, -(C.GEM_SH_H*g)+ys], [0, -(C.GEM_PEAK_H*g)+ys], [-C.GEM_SH_W*g, -(C.GEM_SH_H*g)+ys], [-C.GEM_W*g, -(C.GEM_BASE_H*g)+ys]]; },
  octagon: (r, ys) => { const o = r * C.OCT_EXP; const p = []; for (let i = 0; i < 8; i++) { const a = (22.5 + i*45) * Math.PI/180; p.push([o*Math.cos(a), o*Math.sin(a)+ys]); } return p; },
  triangle: (r, ys) => { const t = r * C.TRI_EXP; return [[0, ys], [C.TRI_BW*t, C.TRI_PH*t+ys], [-C.TRI_BW*t, C.TRI_PH*t+ys]]; },
  pyramid: (r, ys) => { const t = r * C.PY_EXP; return [[0, C.PY_PH*t+ys], [C.PY_BW*t, ys], [-C.PY_BW*t, ys]]; },
  hex: (r, ys) => { const g = r * C.HEX_EXP; return [[0, ys], [C.HEX_TW*g, ys], [C.HEX_MW*g, C.HEX_MH*g+ys], [C.HEX_TW*g, C.HEX_TH*g+ys], [-C.HEX_TW*g, C.HEX_TH*g+ys], [-C.HEX_MW*g, C.HEX_MH*g+ys], [-C.HEX_TW*g, ys]]; },
  trapezoid: (r, ys) => [[0, ys], [C.TZ_BW*r, ys], [C.TZ_TW*r, C.TZ_TH*r+ys], [-C.TZ_TW*r, C.TZ_TH*r+ys], [-C.TZ_BW*r, ys]],
  parking_meter: (r, ys) => { const pr = r*C.PM_EXP, wv = C.TRI_BW*pr, hv = C.TRI_PH*pr; const ar = Math.hypot(wv, hv); const a0 = Math.atan2(hv, wv), a1 = Math.atan2(hv, -wv); const p = [[0, ys]]; for (let i = 0; i <= 20; i++) { const a = a0 + (a1-a0)*(i/20); p.push([ar*Math.cos(a), ar*Math.sin(a)+ys]); } return p; },
  hotdog: (r, ys) => _capsule(r, ys, C.HOT_WS, C.HOT_CR, C.HOT_CY),
  cylinder: (r, ys) => _capsule(r, ys, C.CYL_WS, C.CYL_CR, C.CYL_CY),
  squircle: (r, ys) => _squircle(r, ys, C.SQ_W, C.SQ_H, false),
  squectangle: (r, ys) => _squircle(r, ys, C.SQT_W, C.SQT_H, false),
  squimonde: (r, ys) => _squircle(r, ys, C.SQ_W, C.SQ_H, true),
  crest: (r, ys) => { const p = [[0, ys]]; const bh = C.CR_BH*r; for (let i = 1; i <= C.CR_STEPS; i++) { const yu = bh*(i/C.CR_STEPS); p.push([C.CR_TW*r*Math.sqrt(yu/bh), yu+ys]); } p.push([C.CR_TW*r, C.CR_TH*r+ys]); p.push([-C.CR_TW*r, C.CR_TH*r+ys]); p.push([-C.CR_TW*r, bh+ys]); for (let i = C.CR_STEPS-1; i >= 0; i--) { let yu = bh*(i/C.CR_STEPS); if (yu < 0.01) yu = 0; p.push([-C.CR_TW*r*Math.sqrt(yu/bh), yu+ys]); } return p; },
  stereo_diamond: (r, ys) => { const w = C.SD_W*r, h = C.SD_H*r, fw = C.SD_FW*r; return [[fw, h+ys], [w, ys], [fw, -h+ys], [-fw, -h+ys], [-w, ys], [-fw, h+ys]]; },
  intersecting_overlay: (r, ys) => { const w = C.IO_W*r, h = C.IO_H*r, sk = C.IO_SK*r, cr = C.IO_CR*r; const p = [[-w+sk, h+ys], [w+sk, h+ys], [w-sk, -h+ys]]; for (let i = 0; i <= 20; i++) { const a = Math.PI + (Math.PI*i/20); p.push([(w-sk)+cr*Math.cos(a), -h+cr*Math.sin(a)+ys]); } p.push([-w-sk, -h+ys]); return p; },
};
// Inline comment: Logic for _capsule
function _capsule(r, ys, wsF, crF, cyF) {
  const ws = wsF*r, rc = crF*r, ccy = cyF*r; const p = [[0, ys], [ws, ys]];
  for (let i = 0; i <= C.CYL_STEPS; i++) { const a = (-90 + 180*i/C.CYL_STEPS)*Math.PI/180; p.push([ws+rc*Math.cos(a), ccy+rc*Math.sin(a)+ys]); }
  for (let i = 0; i <= C.CYL_STEPS; i++) { const a = (90 + 180*i/C.CYL_STEPS)*Math.PI/180; p.push([-ws+rc*Math.cos(a), ccy+rc*Math.sin(a)+ys]); }
  p.push([0, ys]); return p;
}
// Inline comment: Logic for _squircle
function _squircle(r, ys, wf, hf, rot) {
  const n = C.SQ_N, w = wf*r, h = hf*r, p = [];
  const cr = Math.cos(Math.PI/4), sr = Math.sin(Math.PI/4);
  for (let i = 0; i <= C.SQ_STEPS; i++) {
    const t = -Math.PI/2 + 2*Math.PI*i/C.SQ_STEPS, c = Math.cos(t), s = Math.sin(t);
    const x = w*(c>=0?1:-1)*Math.pow(Math.abs(c), 2/n);
    const yr = h*(s>=0?1:-1)*Math.pow(Math.abs(s), 2/n);
    if (rot) p.push([x*cr - yr*sr, (x*sr + yr*cr) + h + ys]);
    else p.push([x, yr + h + ys]);
  }
  return p;
}
// Inline comment: Logic for _shapeKey
function _shapeKey(shape) {
  if (!shape) return null;
  let k = String(shape).toLowerCase();
  if (SHAPE_BUILDERS[k]) return k;
  if (k === 'badge') return 'trapezoid';
  if (k === 'shield') return 'crest';
  return null;
}

// Layout a bezel scaled-to-fit (width,height). Returns {pts, pivotX, pivotY, arcRadius} or null.
function bezelLayout(shape, width, height, frameWidth) {
  const key = _shapeKey(shape);
  if (!key) return null;
  const raw = SHAPE_BUILDERS[key](R0, (_Y[key] || 0) * R0);
  // to canvas-relative (y down), origin at pivot (0,0)
  let minx = Infinity, maxx = -Infinity, miny = Infinity, maxy = -Infinity;
  const cpts = raw.map(([x, y]) => { const cx = x, cy = -y; if (cx<minx)minx=cx; if (cx>maxx)maxx=cx; if (cy<miny)miny=cy; if (cy>maxy)maxy=cy; return [cx, cy]; });
  const bw = (maxx - minx) || 1, bh = (maxy - miny) || 1;
  const pad = frameWidth + 6;
  const scale = Math.min((width - pad) / bw, (height - pad) / bh);
  const offX = (width - bw * scale) / 2 - minx * scale;
  const offY = (height - bh * scale) / 2 - miny * scale;
  const pts = cpts.map(([x, y]) => [offX + x * scale, offY + y * scale]);
  return { pts, pivotX: offX, pivotY: offY, arcRadius: 0.32 * bw * scale };
}

// Inline comment: Logic for _tracePath
function _tracePath(ctx, pts) {
  ctx.beginPath();
  ctx.moveTo(pts[0][0], pts[0][1]);
  for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]);
  ctx.closePath();
}

// --- Vintage face textures (reuse the WASM panel engine, window.OAPanels) ------
// Map a face style/patina to a panel config; the generated RGBA is cached per
// (style, size) in an offscreen canvas and drawn (clipped) as the meter face.
const FACE_PRESETS = {
  cream:        { parameters: { base_material: { color: '#f0ead6', texture_type: 'flat' }, paint_layer: { color: '#ffffff', opacity: 0.06 }, edge_wear: { enabled: true, fade_depth: 22, vignette_intensity: 0.35 } } },
  new_old_stock:{ parameters: { base_material: { color: '#f0ead6', texture_type: 'flat' }, paint_layer: { color: '#ffffff', opacity: 0.06 }, edge_wear: { enabled: true, fade_depth: 22, vignette_intensity: 0.35 } } },
  vintage_aged: { parameters: { base_material: { color: '#d8cdb0', texture_type: 'wrinkle' }, grime: { stain_count: 6, color: '#6b5a3a', opacity: 0.22, stain_spread: 28 }, dust: { enabled: true, intensity: 0.5 }, edge_wear: { enabled: true, fade_depth: 26, vignette_intensity: 0.5 } } },
  bakelite:     { parameters: { base_material: { color: '#2a211c', texture_type: 'flat' }, paint_layer: { color: '#000000', opacity: 0.2, gradient_intensity: 0.3 }, edge_wear: { enabled: true, fade_depth: 22, vignette_intensity: 0.6 } } },
  tungsten:     { parameters: { base_material: { color: '#f3b86a', texture_type: 'flat' }, studio_haze: { enabled: true, intensity: 0.22 }, edge_wear: { enabled: true, fade_depth: 22, vignette_intensity: 0.4 } } },
  wood:         { parameters: { base_material: { color: '#5a3a22', texture_type: 'brushed', grain_direction: 'horizontal', grain_intensity: 0.5 }, edge_wear: { enabled: true, fade_depth: 26, vignette_intensity: 0.5 } } },
};
const _FACE_CACHE = (window._OA_FACE_CACHE = window._OA_FACE_CACHE || new Map());

// Inline comment: Logic for getFaceTexture
function getFaceTexture(styleKey, w, h) {
  const cfg = FACE_PRESETS[String(styleKey || '').toLowerCase()];
  if (!cfg || w < 2 || h < 2) return null;
  const k = `${String(styleKey).toLowerCase()}|${w}x${h}`;
  const hit = _FACE_CACHE.get(k);
  if (hit) return hit === 'pending' ? null : hit;
  const eng = window.OAPanels;
  if (!eng) return null;
  _FACE_CACHE.set(k, 'pending');
  eng.ready.then(() => {
    try {
      const bytes = eng.generatePanel(w, h, cfg);
      const off = document.createElement('canvas'); off.width = w; off.height = h;
      off.getContext('2d').putImageData(new ImageData(new Uint8ClampedArray(bytes.buffer, bytes.byteOffset, bytes.length), w, h), 0, 0);
      _FACE_CACHE.set(k, off);
    } catch (e) { _FACE_CACHE.set(k, null); }
  }).catch(() => _FACE_CACHE.set(k, null));
  return null;
}

// Named needle sizes (dropdown). Each sets the default length factor + thickness;
// explicit needle_length_factor / Needle_thickness still override.
const NEEDLE_SIZES = {
  thin:   { len: 0.95, thick: 1 },
  small:  { len: 0.70, thick: 2 },
  medium: { len: 0.95, thick: 3 },
  large:  { len: 1.00, thick: 5 },
  xlarge: { len: 1.08, thick: 7 },
};

// Needle anatomy (Pointer_Style). Draws from pivot (cx,cy) to the tip at angle
// `ang`, length `len`, weight `thick`. Ported from the desktop pointer shapes.
function drawNeedle(ctx, style, cx, cy, ang, len, thick, color) {
  const tipX = cx + len * Math.cos(ang), tipY = cy + len * Math.sin(ang);
  const perp = ang + Math.PI / 2, px = Math.cos(perp), py = Math.sin(perp);
  ctx.fillStyle = color; ctx.strokeStyle = color; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  switch (style) {
    case 'spade': case 'lance': {
      const w = Math.max(3, thick * 2.2);
      const bR = len * 0.55, sR = len * 0.88;
      const bx = cx + bR * Math.cos(ang), by = cy + bR * Math.sin(ang);
      const sx = cx + sR * Math.cos(ang), sy = cy + sR * Math.sin(ang);
      ctx.lineWidth = Math.max(1, thick * 0.8);
      ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(bx, by); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(bx, by); ctx.lineTo(sx + w * px, sy + w * py); ctx.lineTo(tipX, tipY); ctx.lineTo(sx - w * px, sy - w * py); ctx.closePath(); ctx.fill();
      break;
    }
    case 'knife': case 'knife_edge': {
      const w = Math.max(3, thick * 2);
      ctx.beginPath(); ctx.moveTo(cx + w * px, cy + w * py); ctx.lineTo(tipX, tipY); ctx.lineTo(cx - w * px, cy - w * py); ctx.closePath(); ctx.fill();
      break;
    }
    case 'baton': {
      ctx.lineWidth = Math.max(3, thick * 2);
      ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(tipX, tipY); ctx.stroke();
      ctx.beginPath(); ctx.arc(tipX, tipY, Math.max(3, thick * 1.6), 0, Math.PI * 2); ctx.fill();
      break;
    }
    case 'diamond': case 'hollow_diamond': {
      const w = Math.max(4, thick * 2.5), mR = len * 0.5;
      const mx = cx + mR * Math.cos(ang), my = cy + mR * Math.sin(ang);
      ctx.lineWidth = Math.max(1.5, thick * 0.8);
      ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(mx + w * px, my + w * py); ctx.lineTo(tipX, tipY); ctx.lineTo(mx - w * px, my - w * py); ctx.closePath(); ctx.stroke();
      break;
    }
    default: {
      ctx.lineWidth = Math.max(1, thick);
      ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(tipX, tipY); ctx.stroke();
    }
  }
}

// Inline comment: Logic for useNeedleBallistics
function useNeedleBallistics(rawValueRef, canvasRef, min, max, width, height, config) {
  // Persist the animated needle position across re-renders, and read the latest
  // config via a ref. FieldComponent/VUMeterKnob hand NeedleMeter a fresh config
  // object on every render; if `config` were an effect dep (or displayValue a
  // plain local), each unrelated re-render would tear down the loop and reset
  // the needle to `min` — that snap-to-floor-and-spring-back is the "bounce"
  // seen whenever any other widget changes value.
  const displayRef = React.useRef(min);
  const peakRef = React.useRef(min);     // latched peak the needle attacks toward
  const lastRawRef = React.useRef(min);  // last raw sample (to detect new samples)
  const configRef = React.useRef(config);
  configRef.current = config;
  React.useEffect(() => {
    let animationFrameId;

    const render = () => {
      const config = configRef.current;
      const raw = typeof rawValueRef.current === 'number' ? rawValueRef.current : parseFloat(rawValueRef.current || min);
      const attack = config?.dynamics?.attack_ms ? (100 / config.dynamics.attack_ms) * 0.5 : 0.3;
      const release = config?.dynamics?.release_ms ? (100 / config.dynamics.release_ms) * 0.5 : 0.1;
      // Peak-hold-release ballistics: a NEW sample latches a peak to attack up to,
      // then the needle falls back to the floor (min) at the release rate — a real
      // VU/PPM meter that decays to rest instead of holding the value.
      const eps = (max - min) * 0.005;
      if (raw !== lastRawRef.current) { lastRawRef.current = raw; peakRef.current = raw; }
      if (displayRef.current < peakRef.current - eps) {
        displayRef.current += (peakRef.current - displayRef.current) * attack;
      } else {
        peakRef.current = min; // consume the peak so it releases fully to the floor
        displayRef.current -= (displayRef.current - min) * release;
      }
      const displayValue = displayRef.current;

      if (!canvasRef.current) { animationFrameId = requestAnimationFrame(render); return; }
      const ctx = canvasRef.current.getContext('2d');
      ctx.clearRect(0, 0, width, height);

      const styleOv = config?.cosmetics?.style_overrides || {};
      const colors = config?.cosmetics?.colors || {};
      const pnum = (v, d) => { const n = parseFloat(v); return Number.isNaN(n) ? d : n; };

      const bezelShape = (styleOv.bezel_shape || config?.bezel_shape || '').toLowerCase();
      const frameWidth = pnum(styleOv.bezel_width, 6);
      const layout = bezelLayout(bezelShape, width, height, frameWidth);

      // Geometry knobs: pivot "scootch" (x/y nudge), meter scale relative to the
      // bezel, additive arc-radius offset, and pivot crop (push the dial down,
      // cropping its base — like the desktop's pivot_crop).
      const gnum = (v, d) => { const n = parseFloat(v); return Number.isNaN(n) ? d : n; };
      const offX = gnum(styleOv.pivot_offset_x, 0);
      const offY = gnum(styleOv.pivot_offset_y, 0);
      const meterScale = gnum(styleOv.meter_scale ?? styleOv.needle_scale, 1.0);
      const arcOffset = gnum(styleOv.arc_radius_offset, 0);
      const pivotCrop = gnum(styleOv.pivot_crop, 0);

      let centerX, centerY, arcRadius;
      if (layout) {
        centerX = layout.pivotX; centerY = layout.pivotY; arcRadius = layout.arcRadius;
      } else {
        centerX = width / 2;
        centerY = height / 2;
        arcRadius = Math.min(width, height) / 2 * gnum(styleOv.arc_radius_factor, 0.8);
      }
      arcRadius = Math.max(4, arcRadius * meterScale + arcOffset);
      centerX += offX;
      // pivot_crop is a PERCENT (desktop convention, e.g. 120) — push the pivot
      // down by that fraction of the radius so the base is "cropped".
      centerY += offY + (pivotCrop / 100) * arcRadius;

      // Outer backing: transparent by default (panel shows through) unless a bg is set.
      let outerBg = colors.background || config?.bg_color || null;
      if (window.OaTransparency && outerBg) outerBg = window.OaTransparency.bg(config, outerBg);
      if (config?.cosmetics?.transparent === true) outerBg = null;
      if (outerBg && outerBg !== 'transparent') { ctx.fillStyle = outerBg; ctx.fillRect(0, 0, width, height); }

      // --- Scale geometry (tilt + direction) ---
      const minVal = min, maxVal = max, range = maxVal - minVal || 1;
      const viewAngle = pnum(styleOv.Meter_viewable_angle ?? styleOv.meter_viewable_angle ?? config?.meter_viewable_angle, 90);
      const centerAngle = pnum(styleOv.Meter_center_angle ?? styleOv.meter_center_angle ?? config?.meter_center_angle, 90);
      const ccw = (styleOv.Counter_Clockwise ?? styleOv.counter_clockwise) ? true : false;
      const startDeg = centerAngle + viewAngle / 2, endDeg = centerAngle - viewAngle / 2;
      const toRad = (deg) => -deg * Math.PI / 180;
      const angRad = (val) => { const pct = (Math.max(minVal, Math.min(maxVal, val)) - minVal) / range; return toRad(ccw ? (endDeg + pct * viewAngle) : (startDeg - pct * viewAngle)); };
      const boundedVal = Math.max(minVal, Math.min(maxVal, displayValue));
      const nAng = angRad(boundedVal);


      // --- Bezel body + clipped face ---
      ctx.save();
      if (layout) {
        _tracePath(ctx, layout.pts);
      } else {
        const padDeg = 18;
        ctx.beginPath(); ctx.arc(centerX, centerY, arcRadius + 5, toRad(startDeg + padDeg), toRad(endDeg - padDeg), false); ctx.lineTo(centerX, centerY); ctx.closePath();
      }
      ctx.shadowColor = 'rgba(0,0,0,0.8)'; ctx.shadowBlur = 10; ctx.shadowOffsetX = 2; ctx.shadowOffsetY = 2;
      ctx.fillStyle = colors.bezel || '#111';
      ctx.fill();
      ctx.shadowColor = 'transparent';
      ctx.clip();

      // Face: a WASM-generated vintage/wood texture (face_style/patina) if set,
      // else a flat faceplate colour. A glass sheen is laid over either.
      const cosmetics = config?.cosmetics || {};
      const faceStyle = styleOv.face_style || cosmetics.face || cosmetics.patina;
      const faceTex = faceStyle ? getFaceTexture(faceStyle, width, height) : null;
      const faceColor = colors.faceplate || colors.meter_face_colour || (faceStyle ? null : '#111');
      if (faceTex) {
        ctx.drawImage(faceTex, 0, 0, width, height);
      } else if (faceColor && faceColor !== 'transparent') {
        ctx.fillStyle = faceColor; ctx.fillRect(0, 0, width, height);
      }
      // Glass sheen (radial highlight, top-left) for lit/vintage looks.
      if (styleOv.enable_lighting !== false && (faceStyle || styleOv.glass)) {
        const gg = ctx.createRadialGradient(centerX - arcRadius * 0.4, centerY - arcRadius * 0.9, arcRadius * 0.1, centerX, centerY, arcRadius * 2.2);
        gg.addColorStop(0, 'rgba(255,255,255,0.18)');
        gg.addColorStop(0.5, 'rgba(255,255,255,0.04)');
        gg.addColorStop(1, 'rgba(0,0,0,0.10)');
        ctx.fillStyle = gg; ctx.fillRect(0, 0, width, height);
      }

      // --- Fit-guard: keep the whole gauge inside the bezel interior -----------
      // Tall-origin shapes (squircle/squectangle/…) drop their math pivot below
      // the shape in a square/near-square box, so the dial gets clipped by the
      // cutout (visible in the per-shape zoo cards, hidden in the wider "All"
      // grid). Here we clamp the pivot inside the bezel and cap the arc radius so
      // the ticks/needle never leave the interior. It only shrinks/recenters when
      // the gauge would overflow — configs that already fit are untouched.
      if (layout) {
        let iL = Infinity, iR = -Infinity, iT = Infinity, iB = -Infinity;
        for (const [px, py] of layout.pts) { if (px < iL) iL = px; if (px > iR) iR = px; if (py < iT) iT = py; if (py > iB) iB = py; }
        const fitM = frameWidth + 4;
        iL += fitM; iR -= fitM; iT += fitM; iB -= fitM;
        if (iR > iL && iB > iT) {
          centerX = Math.max(iL, Math.min(iR, centerX));
          // Don't fight an intentional pivot_crop (which pushes the pivot below
          // the shape to crop the dial base); only rescue the un-cropped case.
          if (!pivotCrop) centerY = Math.max(iT, Math.min(iB, centerY));
          const SAMPLES = 24;
          let maxR = Infinity;
          for (let i = 0; i <= SAMPLES; i++) {
            const a = angRad(minVal + range * (i / SAMPLES));
            const ca = Math.cos(a), sa = Math.sin(a);
            if (ca > 1e-6) maxR = Math.min(maxR, (iR - centerX) / ca);
            else if (ca < -1e-6) maxR = Math.min(maxR, (iL - centerX) / ca);
            if (sa > 1e-6) maxR = Math.min(maxR, (iB - centerY) / sa);
            else if (sa < -1e-6) maxR = Math.min(maxR, (iT - centerY) / sa);
          }
          // 0.9 leaves room for the number ring / rule sitting outside the ticks.
          if (Number.isFinite(maxR) && maxR > 0) arcRadius = Math.min(arcRadius, Math.max(6, maxR * 0.9));
        }
      }

      // --- Color-zone limits (green -> yellow -> red) ---
      const upperRange = styleOv.upper_range !== undefined ? styleOv.upper_range
        : (config?.cosmetics?.scale?.upper_range !== undefined ? config.cosmetics.scale.upper_range
        : (config?.upper_range !== undefined ? config.upper_range : maxVal));
      const redStart = Math.max(minVal, Math.min(maxVal, upperRange));
      const lowerColor = colors.lower || colors.primary || '#33aa33';
      const middleColor = colors.middle || colors.warn || colors.mid || '#cccc33';
      const upperColor = colors.upper || colors.alert || '#cc3333';
      const midRaw = styleOv.mid_range_start ?? config?.cosmetics?.scale?.mid_range_start ?? config?.mid_range_start;
      const midStart = (midRaw != null) ? Math.max(minVal, Math.min(redStart, pnum(midRaw, redStart))) : redStart;
      const zoneColor = (v) => (v >= redStart ? upperColor : (v >= midStart ? middleColor : lowerColor));

      // The curved "rule" arc: thickness (curve_thickness), radius offset
      // (rule_radius_offset, +out/-in), and a show/hide gate (show_rule).
      const showRule = !(styleOv.show_rule === false || styleOv.show_rule === 'false' || styleOv.show_rule === 0 || styleOv.show_rule === '0');
      const ruleR = arcRadius + gnum(styleOv.rule_radius_offset, 0);
      ctx.lineWidth = gnum(styleOv.curve_thickness, 3);
      const arcSeg = (a, b, col) => { if (showRule && b > a) { ctx.strokeStyle = col; ctx.beginPath(); ctx.arc(centerX, centerY, ruleR, angRad(a), angRad(b), ccw); ctx.stroke(); } };
      arcSeg(minVal, midStart, lowerColor);
      arcSeg(midStart, redStart, middleColor);
      arcSeg(redStart, maxVal, upperColor);

      // --- Ticks + numbers ---
      ctx.font = 'bold 9px Arial'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      // Scale_numbers may be a boolean OR a string ("false") and may live under
      // style_overrides or style_flags — treat all the falsy spellings as hide.
      const _sn = styleOv.Scale_numbers ?? styleOv.scale_numbers ?? config?.cosmetics?.style_flags?.scale_numbers ?? config?.Scale_numbers;
      const showNumbers = !(_sn === false || _sn === 'false' || _sn === 0 || _sn === '0' || _sn === 'no' || _sn === 'off');
      const subTicks = Math.max(0, parseInt(styleOv.sub_ticks ?? 0, 10) || 0);
      const step = config?.domain?.primary?.step || config?.step || (range / 5);
      const tickLen = gnum(styleOv.tick_length, 8);
      const subTickLen = gnum(styleOv.sub_tick_length, 4);
      const tickRadOff = gnum(styleOv.tick_radius_offset, 0);
      const labelRadOff = gnum(styleOv.label_radius_offset, 20);
      const drawTick = (val, major) => {
        const tRad = angRad(val);
        ctx.strokeStyle = ctx.fillStyle = zoneColor(val);
        const base = arcRadius + tickRadOff;
        const len = major ? tickLen : subTickLen;
        ctx.beginPath();
        ctx.moveTo(centerX + base * Math.cos(tRad), centerY + base * Math.sin(tRad));
        ctx.lineTo(centerX + (base - len) * Math.cos(tRad), centerY + (base - len) * Math.sin(tRad));
        ctx.stroke();
        if (major && showNumbers) ctx.fillText(Math.round(val), centerX + (arcRadius - labelRadOff) * Math.cos(tRad), centerY + (arcRadius - labelRadOff) * Math.sin(tRad));
      };
      const majorCount = Math.max(1, Math.round(range / step));
      for (let i = 0; i <= majorCount; i++) {
        const val = minVal + i * step;
        if (val > maxVal + 1e-6) break;
        drawTick(val, true);
        if (subTicks > 0 && i < majorCount) for (let j = 1; j <= subTicks; j++) { const sv = val + (j * step) / (subTicks + 1); if (sv <= maxVal + 1e-6) drawTick(sv, false); }
      }

      // --- Needle + pivot ---
      const nsize = NEEDLE_SIZES[String(styleOv.needle_size || '').toLowerCase()];
      const needleLen = arcRadius * gnum(styleOv.needle_length_factor, nsize ? nsize.len : 0.95);
      const needleThick = gnum(styleOv.Needle_thickness ?? styleOv.needle_thickness, nsize ? nsize.thick : 2);
      const pointerStyle = String(styleOv.Pointer_Style ?? styleOv.pointer_style ?? config?.Pointer_Style ?? 'line').toLowerCase();
      ctx.shadowColor = 'rgba(0,0,0,0.5)'; ctx.shadowBlur = 5; ctx.shadowOffsetX = 3; ctx.shadowOffsetY = 3;
      drawNeedle(ctx, pointerStyle, centerX, centerY, nAng, needleLen, needleThick, colors.pointer || '#fff');
      ctx.shadowColor = 'transparent';

      const pivotSize = pnum(styleOv.Pivot_size ?? styleOv.pivot_size, 10);
      ctx.fillStyle = colors.pivot || '#000';
      ctx.beginPath(); ctx.arc(centerX, centerY, pivotSize, 0, Math.PI * 2); ctx.fill();
      ctx.strokeStyle = '#444'; ctx.lineWidth = 2; ctx.stroke();

      ctx.restore();

      // --- Colored bezel FRAME on top of the clipped face ---
      if (layout) {
        const frameColor = colors.bezel || colors.frame;
        if (frameColor && frameColor !== 'transparent') {
          _tracePath(ctx, layout.pts);
          ctx.lineJoin = 'round'; ctx.lineCap = 'round';
          ctx.lineWidth = frameWidth; ctx.strokeStyle = frameColor;
          ctx.stroke();
        }
      }

      animationFrameId = requestAnimationFrame(render);
    };
    render();
    return () => cancelAnimationFrame(animationFrameId);
  }, [min, max, width, height]);
}

// Inline comment: Logic for NeedleMeter
const NeedleMeter = ({ value, config }) => {
  const getNum = (v, fallback) => {
    if (typeof v === 'number') return v;
    if (typeof v === 'string') { const p = parseFloat(v); return isNaN(p) ? fallback : p; }
    return fallback;
  };

  const min = getNum(config?.domain?.primary?.min, getNum(config?.min, -60));
  const max = getNum(config?.domain?.primary?.max, getNum(config?.max, 10));
  const width = config?.geometry?.width || config?.layout?.width || 150;
  const height = config?.geometry?.height || config?.layout?.height || 150;

  const canvasRef = React.useRef(null);
  const rawValueRef = React.useRef(value !== undefined ? value : min);
  React.useEffect(() => { rawValueRef.current = value !== undefined ? value : min; }, [value, min]);

  useNeedleBallistics(rawValueRef, canvasRef, min, max, width, height, config);

  const [lang] = window.useMqttLang ? window.useMqttLang() : ['En'];
  const title = config?.label_active?.[lang] || config?.label_active?.En ||
                config?.label?.[lang] || config?.label?.En ||
                (typeof config?.label === 'string' ? config.label : null);

  return (
    <div style={{ width: width, height: height, position: 'relative', overflow: 'hidden' }}>
      <canvas ref={canvasRef} width={width} height={height} style={{ display: 'block' }} />
      {title && (
        <div style={{
          position: 'absolute', bottom: '5px', left: '50%', transform: 'translateX(-50%)',
          color: '#888', fontSize: '9px', fontWeight: 'bold', pointerEvents: 'none',
          textAlign: 'center', width: '90%'
        }}>
          {title.toUpperCase()}
        </div>
      )}
    </div>
  );
};
window.NeedleMeter = NeedleMeter;
 
