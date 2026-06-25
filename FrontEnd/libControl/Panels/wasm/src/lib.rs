// frontEnd/libControl/Panels/wasm/src/lib.rs
// Author: Anthony Peter Kuzub
//
// WASM port of the procedural panel + screw background engine. Mirrors the
// Python pipeline (oaGuiElements/Core/panels/panel_generator.py + layer_* +
// panel_screw/screw_generator.py) and the Rust pattern engine
// (oaRustCore_pkg/src/oa_pattern_engine_rs), composited entirely in Rust so the
// browser only has to blit one finished RGBA buffer to a <canvas>.
//
// Two entry points are exported to JS:
//   generate_panel(width, height, config_json) -> RGBA bytes (w*h*4)
//   generate_screw(size, config_json)          -> RGBA bytes (canvas_dim^2*4)
// Everything is deterministic (seeded) — there is NO animation and NO I/O.

use image::{imageops, GrayImage, ImageBuffer, Luma, RgbaImage};
use noise::{NoiseFn, Perlin};
use rand::rngs::StdRng;
use rand::{Rng, SeedableRng};
use serde_json::Value;
use std::f64::consts::PI;
use wasm_bindgen::prelude::*;

const NORM: f64 = 127.5; // perlin (-1..1) -> (0..255)

// ----------------------------------------------------------------------------
// Small RGBA buffer with the blend ops the pipeline needs. Stored row-major as
// [r,g,b,a, r,g,b,a, ...]; the canvas consumes it directly as ImageData.
// ----------------------------------------------------------------------------
struct Buf {
    w: u32,
    h: u32,
    px: Vec<u8>,
}

impl Buf {
    fn filled(w: u32, h: u32, rgba: [u8; 4]) -> Self {
        let mut px = Vec::with_capacity((w * h * 4) as usize);
        for _ in 0..(w * h) {
            px.extend_from_slice(&rgba);
        }
        Buf { w, h, px }
    }

    fn transparent(w: u32, h: u32) -> Self {
        Buf { w, h, px: vec![0u8; (w * h * 4) as usize] }
    }

    #[inline]
    fn idx(&self, x: u32, y: u32) -> usize {
        ((y * self.w + x) * 4) as usize
    }

    #[inline]
    fn in_bounds(&self, x: i32, y: i32) -> bool {
        x >= 0 && y >= 0 && (x as u32) < self.w && (y as u32) < self.h
    }

    // Multiply RGB by a single-channel (grayscale) plane / 255. Used for every
    // "texture" / shading layer (brushed, hammered, vignette, gradient).
    fn multiply_gray(&mut self, gray: &[u8]) {
        for i in 0..(self.w * self.h) as usize {
            let g = gray[i] as u16;
            let p = i * 4;
            self.px[p] = ((self.px[p] as u16 * g) / 255) as u8;
            self.px[p + 1] = ((self.px[p + 1] as u16 * g) / 255) as u8;
            self.px[p + 2] = ((self.px[p + 2] as u16 * g) / 255) as u8;
        }
    }

    // Source-over alpha composite of a single RGBA pixel. Background stays opaque.
    #[inline]
    fn blend_over(&mut self, x: i32, y: i32, s: [u8; 4]) {
        if !self.in_bounds(x, y) {
            return;
        }
        let a = s[3] as f32 / 255.0;
        if a <= 0.0 {
            return;
        }
        let p = self.idx(x as u32, y as u32);
        for c in 0..3 {
            self.px[p + c] = (s[c] as f32 * a + self.px[p + c] as f32 * (1.0 - a)) as u8;
        }
        // Keep alpha at least as opaque as it was (panel base is opaque).
        let na = a + (self.px[p + 3] as f32 / 255.0) * (1.0 - a);
        self.px[p + 3] = (na * 255.0).min(255.0) as u8;
    }

    // Composite an entire RGBA sub-buffer with its top-left at (ox, oy).
    fn composite(&mut self, src: &Buf, ox: i32, oy: i32) {
        for sy in 0..src.h {
            for sx in 0..src.w {
                let sp = src.idx(sx, sy);
                self.blend_over(
                    ox + sx as i32,
                    oy + sy as i32,
                    [src.px[sp], src.px[sp + 1], src.px[sp + 2], src.px[sp + 3]],
                );
            }
        }
    }

    // Bresenham line of a flat RGBA color (alpha-composited).
    fn line(&mut self, x1: f64, y1: f64, x2: f64, y2: f64, color: [u8; 4]) {
        let mut x = x1.round() as i32;
        let mut y = y1.round() as i32;
        let x2i = x2.round() as i32;
        let y2i = y2.round() as i32;
        let dx = (x2i - x).abs();
        let dy = (y2i - y).abs();
        let sx = if x < x2i { 1 } else { -1 };
        let sy = if y < y2i { 1 } else { -1 };
        let mut err = dx - dy;
        let mut guard = 0;
        loop {
            self.blend_over(x, y, color);
            if x == x2i && y == y2i {
                break;
            }
            let e2 = 2 * err;
            if e2 > -dy {
                err -= dy;
                x += sx;
            }
            if e2 < dx {
                err += dx;
                y += sy;
            }
            guard += 1;
            if guard > 20000 {
                break;
            }
        }
    }

    // Gaussian blur the whole RGBA buffer in place (global blur).
    fn blur_rgba(&mut self, sigma: f32) {
        if sigma <= 0.0 {
            return;
        }
        if let Some(img) = RgbaImage::from_raw(self.w, self.h, self.px.clone()) {
            self.px = imageops::blur(&img, sigma).into_raw();
        }
    }

    fn into_pixels(self) -> Vec<u8> {
        self.px
    }
}

// ----------------------------------------------------------------------------
// Config helpers — read a serde_json tree the same forgiving way the Python
// code does (missing keys fall back to defaults).
// ----------------------------------------------------------------------------
fn obj<'a>(v: &'a Value, key: &str) -> Option<&'a Value> {
    v.get(key)
}
fn f64_of(v: &Value, key: &str, d: f64) -> f64 {
    v.get(key).and_then(|x| x.as_f64()).unwrap_or(d)
}
fn u32_of(v: &Value, key: &str, d: u32) -> u32 {
    v.get(key).and_then(|x| x.as_u64()).map(|n| n as u32).unwrap_or(d)
}
fn bool_of(v: &Value, key: &str, d: bool) -> bool {
    v.get(key).and_then(|x| x.as_bool()).unwrap_or(d)
}
fn str_of(v: &Value, key: &str, d: &str) -> String {
    v.get(key).and_then(|x| x.as_str()).unwrap_or(d).to_string()
}

fn hex_to_rgb(hex: &str) -> [u8; 3] {
    let h = hex.trim_start_matches('#');
    if h.len() != 6 {
        return [128, 128, 128];
    }
    [
        u8::from_str_radix(&h[0..2], 16).unwrap_or(128),
        u8::from_str_radix(&h[2..4], 16).unwrap_or(128),
        u8::from_str_radix(&h[4..6], 16).unwrap_or(128),
    ]
}

// ----------------------------------------------------------------------------
// Grayscale texture generators (ported from the Rust pattern engine).
// ----------------------------------------------------------------------------
fn streaks_gray(w: u32, h: u32, vertical: bool, sigma: f64, seed: u32) -> Vec<u8> {
    let perlin = Perlin::new(seed);
    let (sw, sh) = if vertical {
        (w, (h / 100).max(5))
    } else {
        ((w / 100).max(5), h)
    };
    let mut small: GrayImage = ImageBuffer::new(sw, sh);
    for (x, y, p) in small.enumerate_pixels_mut() {
        let v = perlin.get([x as f64 * sigma * 0.01, y as f64 * sigma * 0.01]);
        *p = Luma([((v + 1.0) * NORM) as u8]);
    }
    imageops::resize(&small, w, h, imageops::FilterType::Lanczos3).into_raw()
}

fn hammered_gray(w: u32, h: u32, seed: u32) -> Vec<u8> {
    let base = Perlin::new(seed);
    let dimple = Perlin::new(seed.wrapping_add(1));
    let mut out = vec![0u8; (w * h) as usize];
    for y in 0..h {
        for x in 0..w {
            let b = base.get([x as f64 * 0.1, y as f64 * 0.1]);
            let d = dimple.get([x as f64 * 0.02, y as f64 * 0.02]);
            let c = (b * 0.7 + d * 0.3 + 1.0) * NORM;
            out[(y * w + x) as usize] = c.clamp(0.0, 255.0) as u8;
        }
    }
    out
}

// Multiply two grayscale planes (crosshatch weave).
fn mul_planes(a: &[u8], b: &[u8]) -> Vec<u8> {
    a.iter()
        .zip(b.iter())
        .map(|(&x, &y)| ((x as u16 * y as u16) / 255) as u8)
        .collect()
}

// ----------------------------------------------------------------------------
// PANEL
// ----------------------------------------------------------------------------
#[wasm_bindgen]
pub fn generate_panel(width: u32, height: u32, config_json: &str) -> Vec<u8> {
    let w = width.max(1);
    let h = height.max(1);

    let cfg: Value = serde_json::from_str(config_json).unwrap_or(Value::Null);
    // Prefer the "parameters" sub-block (matches DEFAULT_PANEL_CONFIG); else the
    // top-level object.
    let settings = cfg.get("parameters").cloned().unwrap_or(cfg.clone());
    let settings = if settings.is_object() { settings } else { Value::Object(Default::default()) };

    let seed = u32_of(&settings, "random_seed", 304);
    let mut rng = StdRng::seed_from_u64(seed as u64);

    // ---- Layer 1: substrate ----
    let base = obj(&settings, "base_material").cloned().unwrap_or(Value::Null);
    let sub_rgb = hex_to_rgb(&str_of(&base, "color", "#2a2a2a"));
    let mut panel = Buf::filled(w, h, [sub_rgb[0], sub_rgb[1], sub_rgb[2], 255]);

    let texture = str_of(&base, "texture_type", "flat");
    let vertical = str_of(&base, "grain_direction", "horizontal") == "vertical";
    match texture.as_str() {
        "flat" => {}
        "hammered" => {
            let g = hammered_gray(w, h, seed);
            panel.multiply_gray(&g);
        }
        "crosshatch" => {
            let hori = streaks_gray(w, h, false, 10.0, seed);
            let vert = streaks_gray(w, h, true, 10.0, seed.wrapping_add(7));
            panel.multiply_gray(&mul_planes(&hori, &vert));
        }
        "brushed" => {
            let g = streaks_gray(w, h, vertical, 20.0, seed);
            panel.multiply_gray(&g);
        }
        "wrinkle" => {
            // High-contrast two-octave crinkle (≈ PIL effect_noise multiply).
            let p = Perlin::new(seed.wrapping_add(11));
            let mut g = vec![0u8; (w * h) as usize];
            for y in 0..h {
                for x in 0..w {
                    let n = p.get([x as f64 * 0.08, y as f64 * 0.08]) * 0.6
                        + p.get([x as f64 * 0.21, y as f64 * 0.21]) * 0.4;
                    let v = (0.78 + 0.22 * n).clamp(0.0, 1.0);
                    g[(y * w + x) as usize] = (v * 255.0) as u8;
                }
            }
            panel.multiply_gray(&g);
        }
        "enamel" => {
            // Gentle low-frequency sheen (≈ PIL soft_light peel).
            let p = Perlin::new(seed.wrapping_add(23));
            let mut g = vec![0u8; (w * h) as usize];
            for y in 0..h {
                for x in 0..w {
                    let n = p.get([x as f64 * 0.03, y as f64 * 0.03]);
                    let v = (0.92 + 0.08 * n).clamp(0.0, 1.0);
                    g[(y * w + x) as usize] = (v * 255.0) as u8;
                }
            }
            panel.multiply_gray(&g);
        }
        // any other named texture -> fine directional streaks.
        _ => {
            let g = streaks_gray(w, h, vertical, 5.0, seed);
            panel.multiply_gray(&g);
        }
    }

    // ---- Layer 2: paint + edge wear + lighting gradient ----
    let paint = obj(&settings, "paint_layer").cloned().unwrap_or(Value::Null);
    let edge = obj(&settings, "edge_wear").cloned().unwrap_or(Value::Null);
    let scratches_cfg = obj(&settings, "panel_scratches")
        .or_else(|| obj(&settings, "scratches"))
        .cloned()
        .unwrap_or(Value::Null);

    // mask: 255 = paint shows, 0 = bare substrate.
    let mut mask = vec![255u8; (w * h) as usize];

    if bool_of(&edge, "enabled", false) {
        let depth = f64_of(&edge, "scratch_depth", 30.0) as i32;
        let count = (f64_of(&edge, "scratch_intensity", 0.5) * 50.0) as i32;
        for _ in 0..count {
            let edge_sel = rng.gen_range(0..4);
            let (sx, sy, ex, ey) = match edge_sel {
                0 => {
                    let x = rng.gen_range(0..w as i32);
                    (x, 0, x + rng.gen_range(-20..20), rng.gen_range(0..depth.max(1)))
                }
                1 => {
                    let x = rng.gen_range(0..w as i32);
                    (x, h as i32 - 1, x + rng.gen_range(-20..20), h as i32 - 1 - rng.gen_range(0..depth.max(1)))
                }
                2 => {
                    let y = rng.gen_range(0..h as i32);
                    (0, y, rng.gen_range(0..depth.max(1)), y + rng.gen_range(-20..20))
                }
                _ => {
                    let y = rng.gen_range(0..h as i32);
                    (w as i32 - 1, y, w as i32 - 1 - rng.gen_range(0..depth.max(1)), y + rng.gen_range(-20..20))
                }
            };
            subtract_line(&mut mask, w, h, sx, sy, ex, ey);
        }
    }

    // Deep substrate-revealing scratches.
    let scount = u32_of(&scratches_cfg, "count", 0);
    if scount > 0 && bool_of(&scratches_cfg, "reveals_substrate", false) {
        let min_l = f64_of(&scratches_cfg, "min_length_px", 20.0);
        let max_l = f64_of(&scratches_cfg, "max_length_px", 150.0).max(min_l + 1.0);
        for _ in 0..scount {
            let x1 = rng.gen_range(0.0..w as f64);
            let y1 = rng.gen_range(0.0..h as f64);
            let len = rng.gen_range(min_l..max_l);
            let ang = rng.gen_range(0.0..(2.0 * PI));
            subtract_line(&mut mask, w, h, x1 as i32, y1 as i32, (x1 + len * ang.cos()) as i32, (y1 + len * ang.sin()) as i32);
        }
    }

    let opacity = f64_of(&paint, "opacity", 0.0).clamp(0.0, 1.0);
    if opacity > 0.0 {
        let pc = hex_to_rgb(&str_of(&paint, "color", "#4a5a6a"));
        for i in 0..(w * h) as usize {
            let m = mask[i] as f32 / 255.0; // how much paint applies here
            let p = i * 4;
            for c in 0..3 {
                let substrate = panel.px[p + c] as f32;
                let blended = substrate * (1.0 - opacity as f32) + pc[c] as f32 * opacity as f32;
                panel.px[p + c] = (substrate * (1.0 - m) + blended * m) as u8;
            }
        }
    }

    // Lighting gradient (overhead): top brighter than bottom.
    let grad = f64_of(&paint, "gradient_intensity", 0.2);
    if grad > 0.0 {
        let mut gray = vec![255u8; (w * h) as usize];
        for y in 0..h {
            let f = 1.0 - (y as f64 / h as f64) * (grad * 0.15);
            let val = (255.0 * f) as u8;
            for x in 0..w {
                gray[(y * w + x) as usize] = val;
            }
        }
        panel.multiply_gray(&gray);
    }

    // ---- Layer 3: studio haze (warm multiply) ----
    let haze = obj(&settings, "studio_haze").cloned().unwrap_or(Value::Null);
    if bool_of(&haze, "enabled", false) {
        let inten = f64_of(&haze, "intensity", 0.15) as f32;
        let warm = [180.0f32, 140.0, 50.0];
        for i in 0..(w * h) as usize {
            let p = i * 4;
            for c in 0..3 {
                let tint = 255.0 * (1.0 - inten) + warm[c] * inten;
                panel.px[p + c] = ((panel.px[p + c] as f32 * tint) / 255.0) as u8;
            }
        }
    }

    // ---- Layer 4: rust oxidation ----
    let rust = obj(&settings, "rust").cloned().unwrap_or(Value::Null);
    if bool_of(&rust, "enabled", false) {
        apply_rust(&mut panel, f64_of(&rust, "intensity", 0.5), &mut rng);
    }

    // ---- Layer 5: vignette edge fade ----
    if bool_of(&edge, "enabled", false) {
        let vig = f64_of(&edge, "vignette_intensity", 0.0);
        if vig > 0.0 {
            let depth = (f64_of(&edge, "fade_depth", 110.0) as u32).min(w.min(h) / 2).max(1);
            panel.multiply_gray(&vignette_gray(w, h, vig, depth));
        }
    }

    // ---- Layer 6: surface micro-scratches ----
    if scount > 0 {
        let inten = f64_of(&scratches_cfg, "intensity", 0.4);
        let highlight = f64_of(&scratches_cfg, "depth_highlight", 0.5);
        let sw = u32_of(&scratches_cfg, "width_px", 1);
        let min_l = f64_of(&scratches_cfg, "min_length_px", 20.0);
        let max_l = f64_of(&scratches_cfg, "max_length_px", 150.0).max(min_l + 1.0);
        for _ in 0..scount {
            let x1 = rng.gen_range(0.0..w as f64);
            let y1 = rng.gen_range(0.0..h as f64);
            let len = rng.gen_range(min_l..max_l);
            let ang = rng.gen_range(0.0..(2.0 * PI));
            let x2 = x1 + len * ang.cos();
            let y2 = y1 + len * ang.sin();
            let dark = [0, 0, 0, (255.0 * inten) as u8];
            let light = [255, 255, 255, (255.0 * inten * highlight) as u8];
            for o in 0..sw.max(1) {
                let off = o as f64;
                panel.line(x1 + off, y1 + off, x2 + off, y2 + off, dark);
            }
            panel.line(x1 + 1.0, y1 + 1.0, x2 + 1.0, y2 + 1.0, light);
        }
    }

    // ---- Layer 7: grease / coffee stains ----
    let grime = obj(&settings, "grime").cloned().unwrap_or(Value::Null);
    let stain_count = u32_of(&grime, "stain_count", 0);
    if stain_count > 0 {
        let color = hex_to_rgb(&str_of(&grime, "color", "#0d0d0d"));
        let opacity = f64_of(&grime, "opacity", 0.4);
        let spread = u32_of(&grime, "stain_spread", 40).max(2);
        let mut stains = Buf::transparent(w, h);
        for _ in 0..stain_count {
            let cx = rng.gen_range(0..w) as i32;
            let cy = rng.gen_range(0..h) as i32;
            let r = rng.gen_range((spread / 2) as i32..spread as i32).max(1);
            fill_circle(&mut stains, cx, cy, r, [color[0], color[1], color[2], (255.0 * opacity) as u8]);
        }
        // Soften the blobs, then composite.
        if let Some(img) = RgbaImage::from_raw(w, h, stains.px.clone()) {
            stains.px = imageops::blur(&img, (spread as f32 / 2.0).max(1.0)).into_raw();
        }
        panel.composite(&stains, 0, 0);
    }

    // ---- Layer 8a: screws (auto-placed on the cover) ----
    let screws = obj(&settings, "screws").cloned().unwrap_or(Value::Null);
    let fold = obj(&settings, "metal_fold").cloned().unwrap_or(Value::Null);
    if bool_of(&screws, "enabled", false) {
        place_screws(&mut panel, &screws, &fold, &mut rng);
    }

    // ---- Layer 8b: metal fold creases ----
    if bool_of(&fold, "enabled", false) {
        apply_metal_fold(&mut panel, &fold);
    }

    // ---- Layer 8c: settled dust ----
    let dust = obj(&settings, "dust").cloned().unwrap_or(Value::Null);
    if bool_of(&dust, "enabled", false) {
        let inten = f64_of(&dust, "intensity", 0.3);
        let num = ((w * h) as f64 * 0.0005 * inten) as u32;
        for _ in 0..num {
            let x = rng.gen_range(0..w) as i32;
            let y = rng.gen_range(0..h) as i32;
            let c = rng.gen_range(180..=240) as u8;
            let a = rng.gen_range(50..=150) as u8;
            panel.blend_over(x, y, [c, c, c, a]);
        }
    }

    // ---- Global blur ----
    let gb = f64_of(&settings, "global_blur", 0.0) as f32;
    if gb > 0.0 {
        panel.blur_rgba(gb);
    }

    // Force opaque background (drop-shadow alphas may have lowered edges).
    for i in 0..(w * h) as usize {
        panel.px[i * 4 + 3] = 255;
    }
    panel.into_pixels()
}

// Subtract a drawn line from an L (grayscale) mask (carves bare substrate).
fn subtract_line(mask: &mut [u8], w: u32, h: u32, x1: i32, y1: i32, x2: i32, y2: i32) {
    let mut x = x1;
    let mut y = y1;
    let dx = (x2 - x).abs();
    let dy = (y2 - y).abs();
    let sx = if x < x2 { 1 } else { -1 };
    let sy = if y < y2 { 1 } else { -1 };
    let mut err = dx - dy;
    let mut guard = 0;
    loop {
        if x >= 0 && y >= 0 && (x as u32) < w && (y as u32) < h {
            mask[(y as u32 * w + x as u32) as usize] = 0;
        }
        if x == x2 && y == y2 {
            break;
        }
        let e2 = 2 * err;
        if e2 > -dy {
            err -= dy;
            x += sx;
        }
        if e2 < dx {
            err += dx;
            y += sy;
        }
        guard += 1;
        if guard > 20000 {
            break;
        }
    }
}

fn fill_circle(buf: &mut Buf, cx: i32, cy: i32, r: i32, color: [u8; 4]) {
    for dy in -r..=r {
        for dx in -r..=r {
            if dx * dx + dy * dy <= r * r {
                buf.blend_over(cx + dx, cy + dy, color);
            }
        }
    }
}

fn vignette_gray(w: u32, h: u32, intensity: f64, depth: u32) -> Vec<u8> {
    let mut gray = vec![255u8; (w * h) as usize];
    let depth_f = depth as f64;
    for i in 0..depth {
        let progress = i as f64 / depth_f;
        let f = 1.0 - ((1.0 - progress).powf(1.2) * intensity * 0.8);
        let v = (255.0 * f) as u8;
        // rectangle outline at inset i
        for x in i..(w - i) {
            gray[(i * w + x) as usize] = v;
            gray[((h - 1 - i) * w + x) as usize] = v;
        }
        for y in i..(h - i) {
            gray[(y * w + i) as usize] = v;
            gray[(y * w + (w - 1 - i)) as usize] = v;
        }
    }
    // Soften.
    if let Some(img) = GrayImage::from_raw(w, h, gray.clone()) {
        gray = imageops::blur(&img, (depth as f32 / 2.0).max(2.0)).into_raw();
    }
    gray
}

fn apply_rust(panel: &mut Buf, intensity: f64, rng: &mut StdRng) {
    let w = panel.w;
    let h = panel.h;
    let thresh = 255.0 - (intensity * 50.0);
    // noise + threshold -> mask
    let mut mask = vec![0u8; (w * h) as usize];
    let mut noise = vec![0u8; (w * h) as usize];
    for i in 0..(w * h) as usize {
        let n = rng.gen_range(0..=255) as u8;
        noise[i] = n;
        if n as f64 > thresh {
            mask[i] = 255;
        }
    }
    // dilate 3x3 then blur (MaxFilter + GaussianBlur equivalent)
    let dilated = dilate3(&mask, w, h);
    let blurred = if let Some(img) = GrayImage::from_raw(w, h, dilated) {
        imageops::blur(&img, 2.0).into_raw()
    } else {
        mask
    };
    for i in 0..(w * h) as usize {
        let a = ((blurred[i] as u16 * noise[i] as u16) / 255) as u8;
        let p = i * 4;
        let af = a as f32 / 255.0;
        panel.px[p] = (110.0 * af + panel.px[p] as f32 * (1.0 - af)) as u8;
        panel.px[p + 1] = (50.0 * af + panel.px[p + 1] as f32 * (1.0 - af)) as u8;
        panel.px[p + 2] = (20.0 * af + panel.px[p + 2] as f32 * (1.0 - af)) as u8;
    }
}

fn dilate3(mask: &[u8], w: u32, h: u32) -> Vec<u8> {
    let mut out = vec![0u8; (w * h) as usize];
    for y in 0..h as i32 {
        for x in 0..w as i32 {
            let mut m = 0u8;
            for dy in -1..=1 {
                for dx in -1..=1 {
                    let nx = x + dx;
                    let ny = y + dy;
                    if nx >= 0 && ny >= 0 && (nx as u32) < w && (ny as u32) < h {
                        m = m.max(mask[(ny as u32 * w + nx as u32) as usize]);
                    }
                }
            }
            out[(y as u32 * w + x as u32) as usize] = m;
        }
    }
    out
}

fn apply_metal_fold(panel: &mut Buf, cfg: &Value) {
    let w = panel.w;
    let h = panel.h;
    let thickness = u32_of(cfg, "width_px", 20).max(1);
    let creases = cfg.get("creases").and_then(|v| v.as_array()).cloned().unwrap_or_default();
    let mut h_creases: Vec<f64> = vec![];
    let mut v_creases: Vec<f64> = vec![];
    for c in &creases {
        let pos = f64_of(c, "position_pct", 0.5);
        if str_of(c, "orientation", "horizontal") == "horizontal" {
            h_creases.push(pos);
        } else {
            v_creases.push(pos);
        }
    }
    h_creases.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
    let mut bounds = vec![0.0];
    bounds.extend(h_creases);
    bounds.push(1.0);
    for i in 0..(bounds.len() - 1) {
        let y_start = (h as f64 * bounds[i]) as i32;
        let y_end = (h as f64 * bounds[i + 1]) as i32;
        if y_end <= y_start {
            continue;
        }
        for j in 0..thickness as i32 {
            let f = (1.0 - j as f64 / thickness as f64).powi(2);
            let shadow = (160.0 * f) as u8;
            let hi = (60.0 * f) as u8;
            for x in 0..w as i32 {
                panel.blend_over(x, y_end - 1 - j, [0, 0, 0, shadow]);
                panel.blend_over(x, y_start + j, [255, 255, 255, hi]);
            }
            for y in y_start..y_end {
                panel.blend_over(j, y, [255, 255, 255, hi]);
                panel.blend_over(w as i32 - 1 - j, y, [0, 0, 0, shadow]);
            }
        }
    }
    for pos in v_creases {
        let x = (w as f64 * pos) as i32;
        if x > 0 && x < w as i32 - 1 {
            for y in 0..h as i32 {
                panel.blend_over(x - 1, y, [255, 255, 255, 60]);
                panel.blend_over(x, y, [0, 0, 0, 100]);
                panel.blend_over(x + 1, y, [0, 0, 0, 100]);
            }
        }
    }
}

// Auto-place screws at the cover's mount points (mirrors layer_screws.py).
fn place_screws(panel: &mut Buf, cfg: &Value, fold: &Value, rng: &mut StdRng) {
    let w = panel.w as i32;
    let h = panel.h as i32;
    let size = u32_of(cfg, "size_px", 24);
    let margin = 30i32;

    let mut locs: Vec<String> = match cfg.get("locations") {
        Some(Value::Array(a)) => a.iter().filter_map(|v| v.as_str().map(|s| s.to_lowercase())).collect(),
        Some(Value::String(s)) => vec![s.to_lowercase()],
        _ => vec!["top".into(), "bottom".into()],
    };
    if locs.is_empty() {
        locs = vec!["top".into(), "bottom".into()];
    }

    let mut positions: Vec<(i32, i32)> = vec![];
    if locs.iter().any(|l| l == "top") {
        positions.push((margin, margin));
        positions.push((w - margin, margin));
    }
    if locs.iter().any(|l| l == "bottom") {
        positions.push((margin, h - margin));
        positions.push((w - margin, h - margin));
    }
    if locs.iter().any(|l| l == "middle") {
        positions.push((w / 2, margin));
        positions.push((w / 2, h - margin));
    }

    // Repeat screws along folds, if requested.
    if bool_of(fold, "enabled", false) && bool_of(fold, "repeat_screws", false) {
        if let Some(creases) = fold.get("creases").and_then(|v| v.as_array()) {
            for c in creases {
                let pos = f64_of(c, "position_pct", 0.5);
                if str_of(c, "orientation", "vertical") == "vertical" {
                    let x = (w as f64 * pos) as i32;
                    if locs.iter().any(|l| l == "top") {
                        positions.push((x, margin));
                    }
                    if locs.iter().any(|l| l == "bottom") {
                        positions.push((x, h - margin));
                    }
                } else {
                    let y = (h as f64 * pos) as i32;
                    positions.push((margin, y - margin));
                    positions.push((w - margin, y - margin));
                    positions.push((margin, y + margin));
                    positions.push((w - margin, y + margin));
                }
            }
        }
    }

    for (cx, cy) in positions {
        let angle = rng.gen_range(0..90) as f64;
        let screw = render_screw(size, cfg, angle);
        panel.composite(&screw, cx - screw.w as i32 / 2, cy - screw.h as i32 / 2);
    }
}

// ----------------------------------------------------------------------------
// SCREW (ported from oa_pattern_engine_rs::generate_screw)
// ----------------------------------------------------------------------------
fn screw_canvas_dim_internal(size: u32) -> u32 {
    let padding = (size as f64 * 0.4) as u32;
    size + padding * 2
}

fn render_screw(size: u32, cfg: &Value, angle_deg: f64) -> Buf {
    let canvas = screw_canvas_dim_internal(size);
    let center = canvas as f64 / 2.0;
    let radius = size as f64 / 2.0;
    let mut img = Buf::transparent(canvas, canvas);

    let head_type = str_of(cfg, "type", "fillister");
    let rotation = angle_deg * PI / 180.0;
    let damage = f64_of(cfg, "damage", 0.0);
    let rust = f64_of(cfg, "rust", 0.0);
    let finish = str_of(cfg, "finish", "chrome");
    let base_hex = cfg
        .get("color")
        .and_then(|v| v.as_str())
        .map(|s| s.to_string())
        .unwrap_or_else(|| if finish == "chrome" { "#e0e0e0".into() } else { "#222222".into() });
    let base = hex_to_rgb(&base_hex);

    let mut rng = StdRng::seed_from_u64(size as u64 + (angle_deg as u64) * 123);
    let perlin = Perlin::new(1234);

    // 1. Drop shadow (fillister only).
    if head_type == "fillister" {
        let off = size as f64 * 0.15;
        let scx = center + off;
        let scy = center + off;
        for y in 0..canvas {
            for x in 0..canvas {
                let dx = x as f64 - scx;
                let dy = y as f64 - scy;
                let dist = (dx * dx + dy * dy).sqrt();
                if dist <= radius {
                    let falloff = 1.0 - dist / radius;
                    let a = (150.0 * falloff * falloff) as u8;
                    img.blend_over(x as i32, y as i32, [0, 0, 0, a]);
                }
            }
        }
    }

    // 2. Head geometry + lighting + Robertson void + wear.
    for y in 0..canvas {
        for x in 0..canvas {
            let dx = x as f64 - center;
            let dy = y as f64 - center;
            let dist = (dx * dx + dy * dy).sqrt();
            if dist > radius {
                continue;
            }
            let light = if head_type == "fillister" {
                let so = radius * 0.3;
                let lx = dx + so;
                let ly = dy + so;
                let ld = (lx * lx + ly * ly).sqrt();
                0.5 + 0.5 * (1.0 - (ld / (radius * 1.5)).clamp(0.0, 1.0))
            } else {
                0.7
            };
            let mut r = (base[0] as f64 * light) as u8;
            let mut g = (base[1] as f64 * light) as u8;
            let mut b = (base[2] as f64 * light) as u8;

            // Robertson square drive void (rotated).
            let drive = radius * 0.55;
            let rx = dx * rotation.cos() - dy * rotation.sin();
            let ry = dx * rotation.sin() + dy * rotation.cos();
            if rx.abs() < drive / 2.0 && ry.abs() < drive / 2.0 {
                r = 20;
                g = 20;
                b = 20;
                let e = 1.0;
                if ry < -drive / 2.0 + e {
                    r = 100; g = 100; b = 100;
                } else if rx < -drive / 2.0 + e {
                    r = 80; g = 80; b = 80;
                } else if rx > drive / 2.0 - e {
                    r = 10; g = 10; b = 10;
                } else if ry > drive / 2.0 - e {
                    r = 0; g = 0; b = 0;
                }
            } else if damage > 0.0 && rng.gen_bool((damage * 0.02).clamp(0.0, 1.0)) {
                r = 200; g = 200; b = 200;
            }

            if rust > 0.0 {
                let n = perlin.get([x as f64 * 0.2, y as f64 * 0.2]);
                if n > 1.0 - rust {
                    r = 130; g = 60; b = 20;
                }
            }

            let p = img.idx(x, y);
            img.px[p] = r;
            img.px[p + 1] = g;
            img.px[p + 2] = b;
            img.px[p + 3] = 255;
        }
    }

    img
}

#[wasm_bindgen]
pub fn generate_screw(size: u32, config_json: &str) -> Vec<u8> {
    let cfg: Value = serde_json::from_str(config_json).unwrap_or(Value::Null);
    let angle = f64_of(&cfg, "angle", 0.0);
    render_screw(size.max(1), &cfg, angle).into_pixels()
}

#[wasm_bindgen]
pub fn screw_canvas_dim(size: u32) -> u32 {
    screw_canvas_dim_internal(size.max(1))
}
