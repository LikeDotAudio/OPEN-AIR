// oaGuiBackground/Methods/oaPatternEngine_rs/src/lib.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260331.2300.3

use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict};
use image::{Rgba, RgbaImage, GrayImage, Luma, imageops};
use rand::{Rng, SeedableRng};
use rand::rngs::StdRng;
use noise::{NoiseFn, Perlin};
use rayon::prelude::*;
use std::f64::consts::PI;

#[pyclass]
struct PatternEngine;

#[pymethods]
impl PatternEngine {
    #[new]
    fn new() -> Self {
        PatternEngine
    }

    /// Generates directional streaks (brushed metal effect).
    fn generate_streaks(&self, py: Python<'_>, width: u32, height: u32, vertical: bool, sigma: f64, seed: u32) -> PyObject {
        let perlin = Perlin::new(seed);

        let (src_w, src_h) = if vertical {
            (width, 5.max(height / 100))
        } else {
            (5.max(width / 100), height)
        };

        let mut img = GrayImage::new(src_w, src_h);
        for (x, y, pixel) in img.enumerate_pixels_mut() {
            let val = perlin.get([x as f64 * sigma * 0.01, y as f64 * sigma * 0.01]);
            let norm_val = ((val + 1.0) * 127.5) as u8;
            *pixel = Luma([norm_val]);
        }

        let resized = imageops::resize(&img, width, height, imageops::FilterType::Lanczos3);
        
        let mut rgba = RgbaImage::new(width, height);
        for (x, y, pixel) in rgba.enumerate_pixels_mut() {
            let gray = resized.get_pixel(x, y)[0];
            *pixel = Rgba([gray, gray, gray, 255]);
        }

        PyBytes::new_bound(py, rgba.as_raw()).into()
    }

    /// Generates a hammered metal texture.
    fn generate_hammered(&self, py: Python<'_>, width: u32, height: u32, seed: u32) -> PyObject {
        let raw_pixels: Vec<u8> = (0..height).into_par_iter().flat_map(|y| {
            let mut row = Vec::with_capacity((width * 4) as usize);
            let perlin_inner = Perlin::new(seed);
            let dimple_perlin = Perlin::new(seed + 1);
            
            for x in 0..width {
                let base = perlin_inner.get([x as f64 * 0.1, y as f64 * 0.1]);
                let dimples = dimple_perlin.get([x as f64 * 0.02, y as f64 * 0.02]);
                
                let combined = (base * 0.7 + dimples * 0.3 + 1.0) * 127.5;
                let val = combined.clamp(0.0, 255.0) as u8;
                
                row.push(val); row.push(val); row.push(val); row.push(255);
            }
            row
        }).collect();

        PyBytes::new_bound(py, &raw_pixels).into()
    }

    /// Generates a high-fidelity procedural Robertson screw head.
    fn generate_screw(&self, py: Python<'_>, size: u32, config: &Bound<'_, PyDict>) -> PyResult<PyObject> {
        let padding = (size as f32 * 0.4) as u32;
        let canvas_dim = size + padding * 2;
        let center = canvas_dim as f32 / 2.0;
        let radius = size as f32 / 2.0;
        
        let mut img = RgbaImage::new(canvas_dim, canvas_dim);
        
        let head_type: String = config.get_item("type")?.and_then(|v| v.extract().ok()).unwrap_or_else(|| "fillister".to_string());
        let rotation_deg: f32 = config.get_item("angle")?.and_then(|v| v.extract().ok()).unwrap_or(0.0);
        let rotation_rad = rotation_deg * PI as f32 / 180.0;
        
        let damage: f32 = config.get_item("damage")?.and_then(|v| v.extract().ok()).unwrap_or(0.0);
        let rust: f32 = config.get_item("rust")?.and_then(|v| v.extract().ok()).unwrap_or(0.0);
        
        let mut rng = StdRng::seed_from_u64(size as u64);

        for y in 0..canvas_dim {
            for x in 0..canvas_dim {
                let dx = x as f32 - center;
                let dy = y as f32 - center;
                let dist = (dx*dx + dy*dy).sqrt();
                
                if dist > radius && dist < radius + 5.0 {
                    let alpha = (150.0 * (1.0 - (dist - radius) / 5.0)) as u8;
                    img.put_pixel(x, y, Rgba([0, 0, 0, alpha]));
                }

                if dist <= radius {
                    let mut light = 128.0;
                    if head_type == "fillister" {
                        let lx = dx + radius * 0.3;
                        let ly = dy + radius * 0.3;
                        let ldist = (lx*lx + ly*ly).sqrt();
                        light = 255.0 - (ldist / radius * 127.0);
                    } else {
                        light = 180.0;
                    }
                    
                    let drive_size = radius * 0.55;
                    let rx = dx * rotation_rad.cos() + dy * rotation_rad.sin();
                    let ry = -dx * rotation_rad.sin() + dy * rotation_rad.cos();
                    
                    let mut final_color = [light as u8, light as u8, light as u8, 255];
                    
                    if rx.abs() < drive_size / 2.0 && ry.abs() < drive_size / 2.0 {
                        final_color = [20, 20, 20, 255];
                        if rx.abs() > (drive_size / 2.0) - 1.0 || ry.abs() > (drive_size / 2.0) - 1.0 {
                            if rx < 0.0 || ry < 0.0 {
                                final_color = [100, 100, 100, 255];
                            }
                        }
                    } else {
                        if damage > 0.0 {
                            if rng.gen_bool(damage as f64 * 0.05) {
                                final_color = [200, 200, 200, 255];
                            }
                        }
                    }
                    
                    if rust > 0.0 {
                        let perlin = Perlin::new(1234);
                        let r_noise = perlin.get([x as f64 * 0.5, y as f64 * 0.5]);
                        if r_noise > 1.0 - (rust as f64) {
                            final_color = [130, 60, 20, 255];
                        }
                    }

                    img.put_pixel(x, y, Rgba(final_color));
                }
            }
        }

        Ok(PyBytes::new_bound(py, img.as_raw()).into())
    }
}

#[pymodule]
fn oapatternengine_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PatternEngine>()?;
    Ok(())
}
