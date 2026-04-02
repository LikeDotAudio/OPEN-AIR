// oaGuiElements/Methods/oaScrewGenerator_rs/src/lib.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260402.0005.1

use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict};
use image::{Rgba, RgbaImage};
use rand::{Rng, SeedableRng};
use rand::rngs::StdRng;
use noise::{NoiseFn, Perlin};
use std::f64::consts::PI;

#[pyclass]
struct ScrewGenerator;

#[pymethods]
impl ScrewGenerator {
    #[new]
    fn new() -> Self {
        ScrewGenerator
    }

    /// Generates a high-fidelity procedural Robertson screw head.
    /// Returns raw RGBA bytes.
    fn generate_screw(&self, py: Python<'_>, size: u32, config: &Bound<'_, PyDict>) -> PyResult<(PyObject, u32)> {
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
                        // Domed light highlight (shifted top-left)
                        let specular_offset = radius * 0.3;
                        let lx = dx + specular_offset;
                        let ly = dy + specular_offset;
                        let ldist = (lx*lx + ly*ly).sqrt();
                        light_factor = 0.5 + 0.5 * (1.0 - (ldist / (radius * 1.5)).clamp(0.0, 1.0));
                    } else {
                        // Countersunk (flatter)
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
                        // In the void
                        r = 20; g = 20; b = 20;
                        
                        // Directional walls
                        let edge_thresh = 1.0;
                        if ry < -drive_size/2.0 + edge_thresh { // North
                            r = 100; g = 100; b = 100;
                        } else if rx < -drive_size/2.0 + edge_thresh { // West
                            r = 80; g = 80; b = 80;
                        } else if rx > drive_size/2.0 - edge_thresh { // East
                            r = 10; g = 10; b = 10;
                        } else if ry > drive_size/2.0 - edge_thresh { // South
                            r = 0; g = 0; b = 0;
                        }
                    } else {
                        // Surface Scratches
                        if damage_intensity > 0.0 {
                            if rng.gen_bool(damage_intensity * 0.02) {
                                r = 200; g = 200; b = 200;
                            }
                        }
                    }
                    
                    // Rust Noise
                    if rust_intensity > 0.0 {
                        let r_noise = perlin.get([x as f64 * 0.2, y as f64 * 0.2]);
                        if r_noise > 1.0 - rust_intensity {
                            r = 130; g = 60; b = 20;
                        }
                    }

                    // Composite over shadow
                    let mut pixel = img.get_pixel(x, y).0;
                    let alpha_src = 255u8;
                    let alpha_dst = pixel[3];
                    
                    // Simple alpha composite
                    if alpha_dst == 0 {
                        img.put_pixel(x, y, Rgba([r, g, b, 255]));
                    } else {
                        // Blend (approximate)
                        let new_r = (r as u16 * alpha_src as u16 + pixel[0] as u16 * (255 - alpha_src) as u16) / 255;
                        let new_g = (g as u16 * alpha_src as u16 + pixel[1] as u16 * (255 - alpha_src) as u16) / 255;
                        let new_b = (b as u16 * alpha_src as u16 + pixel[2] as u16 * (255 - alpha_src) as u16) / 255;
                        img.put_pixel(x, y, Rgba([new_r as u8, new_g as u8, new_b as u8, 255]));
                    }
                }
            }
        }

        Ok((PyBytes::new_bound(py, img.as_raw()).into(), canvas_dim))
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
fn oascrewgenerator_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<ScrewGenerator>()?;
    Ok(())
}
