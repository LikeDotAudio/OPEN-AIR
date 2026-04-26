// oaGuiBackground/Methods/oaPatternEngine_rs/mod.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260413.1400.1
//
// Description: Procedural background generation engine. 
// Utilizes Perlin noise and deterministic RNG for dynamic UI textures.

use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict, PyList};
use image::{Rgba, RgbaImage, GrayImage, Luma, imageops};
use rand::{Rng, SeedableRng};
use rand::rngs::StdRng;
use noise::{NoiseFn, Perlin};
use rayon::prelude::*;
use std::f64::consts::PI;

const COLOR_NORMALIZATION_FACTOR: f64 = 127.5;

#[pyclass]
struct PatternEngine;

#[pymethods]
impl PatternEngine {
    #[new]
    fn new() -> Self {
        PatternEngine
    }

    /// Generates directional streaks (brushed metal effect).
    fn generate_streaks<'py>(&self, py: Python<'py>, width: u32, height: u32, vertical: bool, sigma: f64, seed: u32) -> Bound<'py, PyBytes> {
        let perlin = Perlin::new(seed);

        let (src_w, src_h) = if vertical {
            (width, 5.max(height / 100))
        } else {
            (5.max(width / 100), height)
        };

        let mut img = GrayImage::new(src_w, src_h);
        for (position_x, position_y, pixel) in img.enumerate_pixels_mut() {
            let value = perlin.get([position_x as f64 * sigma * 0.01, position_y as f64 * sigma * 0.01]);
            let normalized_value = ((value + 1.0) * COLOR_NORMALIZATION_FACTOR) as u8;
            *pixel = Luma([normalized_value]);
        }

        let resized = imageops::resize(&img, width, height, imageops::FilterType::Lanczos3);
        
        let mut rgba = RgbaImage::new(width, height);
        for (position_x, position_y, pixel) in rgba.enumerate_pixels_mut() {
            let gray = resized.get_pixel(position_x, position_y)[0];
            *pixel = Rgba([gray, gray, gray, 255]);
        }

        PyBytes::new_bound(py, rgba.as_raw())
    }

    /// Generates a hammered metal texture.
    fn generate_hammered<'py>(&self, py: Python<'py>, width: u32, height: u32, seed: u32) -> Bound<'py, PyBytes> {
        let raw_pixels: Vec<u8> = (0..height).into_par_iter().flat_map(|position_y| {
            let mut row = Vec::with_capacity((width * 4) as usize);
            let perlin_inner = Perlin::new(seed);
            let dimple_perlin = Perlin::new(seed + 1);
            
            for position_x in 0..width {
                let base = perlin_inner.get([position_x as f64 * 0.1, position_y as f64 * 0.1]);
                let dimples = dimple_perlin.get([position_x as f64 * 0.02, position_y as f64 * 0.02]);
                
                let combined = (base * 0.7 + dimples * 0.3 + 1.0) * COLOR_NORMALIZATION_FACTOR;
                let value = combined.clamp(0.0, 255.0) as u8;
                
                row.push(value); row.push(value); row.push(value); row.push(255);
            }
            row
        }).collect();

        PyBytes::new_bound(py, &raw_pixels)
    }

    fn generate_vignette<'py>(&self, py: Python<'py>, width: u32, height: u32, intensity: f64, depth: u32) -> Bound<'py, PyBytes> {
        let mut img = RgbaImage::new(width, height);
        let depth_f = depth as f64;
        
        for index_i in 0..depth {
            let progress = index_i as f64 / depth_f;
            let alpha_factor = 1.0 - ((1.0 - progress).powf(1.2) * intensity * 0.8);
            let value = (255.0 * alpha_factor) as u8;
            
            // Draw a rectangle "outline" at depth index_i
            for position_x in index_i..(width - index_i) {
                img.put_pixel(position_x, index_i, Rgba([value, value, value, 255]));
                img.put_pixel(position_x, height - 1 - index_i, Rgba([value, value, value, 255]));
            }
            for position_y in index_i..(height - index_i) {
                img.put_pixel(index_i, position_y, Rgba([value, value, value, 255]));
                img.put_pixel(width - 1 - index_i, position_y, Rgba([value, value, value, 255]));
            }
        }
        
        // Fill the center
        for position_y in depth..(height.saturating_sub(depth)) {
            for position_x in depth..(width.saturating_sub(depth)) {
                img.put_pixel(position_x, position_y, Rgba([255, 255, 255, 255]));
            }
        }

        PyBytes::new_bound(py, img.as_raw())
    }

    fn generate_scratches<'py>(&self, py: Python<'py>, width: u32, height: u32, config: &Bound<'_, PyDict>) -> PyResult<Bound<'py, PyBytes>> {
        let intensity: f64 = config.get_item("intensity")?.and_then(|v| v.extract().ok()).unwrap_or(0.4);
        let count: u32 = config.get_item("count")?.and_then(|v| v.extract().ok()).unwrap_or(25);
        let min_len: u32 = config.get_item("min_length_px")?.and_then(|v| v.extract().ok()).unwrap_or(20);
        let max_len: u32 = config.get_item("max_length_px")?.and_then(|v| v.extract().ok()).unwrap_or(150);
        let depth_highlight: f64 = config.get_item("depth_highlight")?.and_then(|v| v.extract().ok()).unwrap_or(0.5);
        
        let mut img = RgbaImage::new(width, height);
        let mut rng = StdRng::from_entropy();
        
        for _ in 0..count {
            let x1 = rng.gen_range(0.0..(width as f64));
            let y1 = rng.gen_range(0.0..(height as f64));
            let length = rng.gen_range((min_len as f64)..(max_len as f64));
            let angle = rng.gen_range(0.0..(2.0 * PI));
            
            let x2 = x1 + length * angle.cos();
            let y2 = y1 + length * angle.sin();
            
            self.internal_draw_line(&mut img, x1, y1, x2, y2, [0, 0, 0, (255.0 * intensity) as u8]);
            self.internal_draw_line(&mut img, x1 + 1.0, y1 + 1.0, x2 + 1.0, y2 + 1.0, [255, 255, 255, (255.0 * intensity * depth_highlight) as u8]);
        }

        Ok(PyBytes::new_bound(py, img.as_raw()))
    }

    fn generate_metal_fold<'py>(&self, py: Python<'py>, width: u32, height: u32, config: &Bound<'_, PyDict>) -> PyResult<Bound<'py, PyBytes>> {
        let mut img = RgbaImage::new(width, height);
        let thickness: u32 = config.get_item("width_px")?.and_then(|v| v.extract().ok()).unwrap_or(20);
        
        let creases = config.get_item("creases")?.and_then(|v| v.downcast_into::<PyList>().ok()).unwrap_or_else(|| PyList::empty_bound(py));
        
        let mut h_creases: Vec<f64> = Vec::new();
        let mut v_creases: Vec<f64> = Vec::new();
        
        for item in creases.iter() {
            let dict = item.downcast::<PyDict>()?;
            let orientation: String = dict.get_item("orientation")?.and_then(|v| v.extract::<String>().ok()).unwrap_or_else(|| "horizontal".to_string());
            let position: f64 = dict.get_item("position_pct")?.and_then(|v| v.extract::<f64>().ok()).unwrap_or(0.5);
            if orientation == "horizontal" {
                h_creases.push(position);
            } else {
                v_creases.push(position);
            }
        }
        
        h_creases.sort_by(|a, b| a.partial_cmp(b).unwrap());
        let mut h_bounds = vec![0.0];
        h_bounds.extend(h_creases);
        h_bounds.push(1.0);
        
        for i in 0..(h_bounds.len() - 1) {
            let y_start = (height as f64 * h_bounds[i]) as u32;
            let y_end = (height as f64 * h_bounds[i+1]) as u32;
            
            if y_end <= y_start { continue; }
            
            for j in 0..thickness {
                let j_f = j as f64;
                let thick_f = thickness as f64;
                let shadow_alpha = (160.0 * (1.0 - j_f / thick_f).powi(2)) as u8;
                let highlight_alpha = (60.0 * (1.0 - j_f / thick_f).powi(2)) as u8;
                
                // Bottom Shadow
                if y_end > j {
                    for x in 0..width {
                        self.internal_blend_pixel(img.get_pixel_mut(x, y_end - 1 - j), [0, 0, 0, shadow_alpha]);
                    }
                }
                
                // Top Highlight
                if y_start + j < height {
                    for x in 0..width {
                        self.internal_blend_pixel(img.get_pixel_mut(x, y_start + j), [255, 255, 255, highlight_alpha]);
                    }
                }
                
                // Left Highlight
                if j < width {
                    for y in y_start..y_end {
                        self.internal_blend_pixel(img.get_pixel_mut(j, y), [255, 255, 255, highlight_alpha]);
                    }
                }
                
                // Right Shadow
                if width > 1 + j {
                    for y in y_start..y_end {
                        self.internal_blend_pixel(img.get_pixel_mut(width - 1 - j, y), [0, 0, 0, shadow_alpha]);
                    }
                }
            }
            
            // Crease gap
            if i < h_bounds.len() - 2 {
                let y = y_end;
                if y < height {
                    for x in 0..width {
                        img.put_pixel(x, y, Rgba([0, 0, 0, 255]));
                        if y + 1 < height {
                            self.internal_blend_pixel(img.get_pixel_mut(x, y + 1), [255, 255, 255, 40]);
                        }
                    }
                }
            }
        }
        
        for position in v_creases {
            let x = (width as f64 * position) as u32;
            if x > 0 && x < width - 1 {
                for y in 0..height {
                    self.internal_blend_pixel(img.get_pixel_mut(x - 1, y), [255, 255, 255, 60]);
                    img.put_pixel(x, y, Rgba([0, 0, 0, 100]));
                    if x + 1 < width {
                        img.put_pixel(x + 1, y, Rgba([0, 0, 0, 100]));
                    }
                }
            }
        }

        Ok(PyBytes::new_bound(py, img.as_raw()))
    }

    /// Generates a high-fidelity procedural Robertson screw head.
    fn generate_screw<'py>(&self, py: Python<'py>, size: u32, config: &Bound<'_, PyDict>) -> PyResult<Bound<'py, PyBytes>> {
        let padding = (size as f64 * 0.4) as u32;
        let canvas_dim = size + padding * 2;
        let center = canvas_dim as f64 / 2.0;
        let radius = size as f64 / 2.0;
        
        let mut img = RgbaImage::new(canvas_dim, canvas_dim);
        
        let head_type: String = config.get_item("type")?.and_then(|v| v.extract().ok()).unwrap_or_else(|| "fillister".to_string());
        let rotation_deg: f64 = config.get_item("angle")?.and_then(|v| v.extract().ok()).unwrap_or(0.0);
        let rotation_rad = rotation_deg * PI / 180.0;
        
        let damage_intensity: f64 = config.get_item("damage")?.and_then(|v| v.extract().ok()).unwrap_or(0.0);
        let rust_intensity: f64 = config.get_item("rust")?.and_then(|v| v.extract().ok()).unwrap_or(0.0);
        
        let material_finish: String = config.get_item("finish")?.and_then(|v| v.extract().ok()).unwrap_or_else(|| "chrome".to_string());
        let base_color_hex: String = config.get_item("color")?.and_then(|v| v.extract().ok()).unwrap_or_else(|| {
            match material_finish.as_str() {
                "chrome" => "#e0e0e0".to_string(),
                _ => "#222222".to_string(),
            }
        });
        
        let base_rgb = self.convert_hex_to_rgb(&base_color_hex);
        
        let mut rng = StdRng::seed_from_u64(size as u64 + (rotation_deg as u64 * 123));

        // --- 1. Drop Shadow (Basic Circular) ---
        if head_type == "fillister" {
            let offset_x = (size as f64 * 0.15) as f64;
            let offset_y = (size as f64 * 0.15) as f64;
            let shadow_radius = radius;
            let shadow_center_x = center + offset_x;
            let shadow_center_y = center + offset_y;
            
            for y in 0..canvas_dim {
                for x in 0..canvas_dim {
                    let dx = x as f64 - shadow_center_x;
                    let dy = y as f64 - shadow_center_y;
                    let dist = (dx*dx + dy*dy).sqrt();
                    if dist <= shadow_radius {
                        let falloff = 1.0 - (dist / shadow_radius);
                        let alpha = (150.0 * falloff.powi(2)) as u8;
                        img.put_pixel(x, y, Rgba([0, 0, 0, alpha]));
                    }
                }
            }
        }

        // --- 2. Head Geometry and Lighting ---
        let perlin = Perlin::new(1234);
        
        for y in 0..canvas_dim {
            for x in 0..canvas_dim {
                let dx = x as f64 - center;
                let dy = y as f64 - center;
                let dist = (dx*dx + dy*dy).sqrt();
                
                if dist <= radius {
                    let mut light_factor = 1.0;
                    if head_type == "fillister" {
                        let specular_offset = radius * 0.3;
                        let lx = dx + specular_offset;
                        let ly = dy + specular_offset;
                        let ldist = (lx*lx + ly*ly).sqrt();
                        light_factor = 0.5 + 0.5 * (1.0 - (ldist / (radius * 1.5)).clamp(0.0, 1.0));
                    } else {
                        light_factor = 0.7;
                    }
                    
                    let mut r = (base_rgb[0] as f64 * light_factor) as u8;
                    let mut g = (base_rgb[1] as f64 * light_factor) as u8;
                    let mut b = (base_rgb[2] as f64 * light_factor) as u8;
                    
                    // Robertson Void
                    let drive_size = radius * 0.55;
                    let rx = dx * rotation_rad.cos() - dy * rotation_rad.sin();
                    let ry = dx * rotation_rad.sin() + dy * rotation_rad.cos();
                    
                    if rx.abs() < drive_size / 2.0 && ry.abs() < drive_size / 2.0 {
                        r = 20; g = 20; b = 20;
                        let edge_thresh = 1.0;
                        if ry < -drive_size/2.0 + edge_thresh { r = 100; g = 100; b = 100; }
                        else if rx < -drive_size/2.0 + edge_thresh { r = 80; g = 80; b = 80; }
                        else if rx > drive_size/2.0 - edge_thresh { r = 10; g = 10; b = 10; }
                        else if ry > drive_size/2.0 - edge_thresh { r = 0; g = 0; b = 0; }
                    } else if damage_intensity > 0.0 {
                        if rng.gen_bool(damage_intensity * 0.02) {
                            r = 200; g = 200; b = 200;
                        }
                    }
                    
                    if rust_intensity > 0.0 {
                        let r_noise = perlin.get([x as f64 * 0.2, y as f64 * 0.2]);
                        if r_noise > 1.0 - rust_intensity {
                            r = 130; g = 60; b = 20;
                        }
                    }

                    // Compositionite
                    let pixel = img.get_pixel(x, y).0;
                    if pixel[3] == 0 {
                        img.put_pixel(x, y, Rgba([r, g, b, 255]));
                    } else {
                        let new_r = (r as u16 * 255 + pixel[0] as u16 * (255 - 255)) / 255;
                        let new_g = (g as u16 * 255 + pixel[1] as u16 * (255 - 255)) / 255;
                        let new_b = (b as u16 * 255 + pixel[2] as u16 * (255 - 255)) / 255;
                        img.put_pixel(x, y, Rgba([new_r as u8, new_g as u8, new_b as u8, 255]));
                    }
                }
            }
        }

        Ok(PyBytes::new_bound(py, img.as_raw()))
    }
}

impl PatternEngine {
    fn internal_draw_line(&self, img: &mut RgbaImage, x1: f64, y1: f64, x2: f64, y2: f64, color: [u8; 4]) {
        let dx = (x2 - x1).abs();
        let dy = (y2 - y1).abs();
        let sx = if x1 < x2 { 1.0 } else { -1.0 };
        let sy = if y1 < y2 { 1.0 } else { -1.0 };
        let mut error_accumulator = dx - dy;

        let mut x = x1;
        let mut y = y1;

        loop {
            if x >= 0.0 && x < img.width() as f64 && y >= 0.0 && y < img.height() as f64 {
                img.put_pixel(x as u32, y as u32, Rgba(color));
            }

            if (x - x2).abs() < 0.1 && (y - y2).abs() < 0.1 { break; }
            let e2 = 2.0 * error_accumulator;
            if e2 > -dy {
                error_accumulator -= dy;
                x += sx;
            }
            if e2 < dx {
                error_accumulator += dx;
                y += sy;
            }
        }
    }

    fn internal_blend_pixel(&self, pixel: &mut Rgba<u8>, source: [u8; 4]) {
        let alpha_src = source[3] as f32 / 255.0;
        let alpha_dst = pixel[3] as f32 / 255.0;
        
        let out_alpha = alpha_src + alpha_dst * (1.0 - alpha_src);
        if out_alpha > 0.0 {
            pixel[0] = ((source[0] as f32 * alpha_src + pixel[0] as f32 * alpha_dst * (1.0 - alpha_src)) / out_alpha) as u8;
            pixel[1] = ((source[1] as f32 * alpha_src + pixel[1] as f32 * alpha_dst * (1.0 - alpha_src)) / out_alpha) as u8;
            pixel[2] = ((source[2] as f32 * alpha_src + pixel[2] as f32 * alpha_dst * (1.0 - alpha_src)) / out_alpha) as u8;
            pixel[3] = (out_alpha * 255.0) as u8;
        }
    }

    fn convert_hex_to_rgb(&self, hex_string: &str) -> [u8; 3] {
        let hex = hex_string.trim_start_matches('#');
        if hex.len() != 6 {
            return [128, 128, 128];
        }
        let r = u8::from_str_radix(&hex[0..2], 16).unwrap_or(128);
        let g = u8::from_str_radix(&hex[2..4], 16).unwrap_or(128);
        let b = u8::from_str_radix(&hex[4..6], 16).unwrap_or(128);
        [r, g, b]
    }
}

#[pymodule]
pub fn oapatternengine_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PatternEngine>()?;
    Ok(())
}
