/**
 * Header: mod.rs
 * Purpose: mod.rs implementation.
 * Description: Logic and implementation for mod.rs implementation.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// oaGuiElements/Methods/oaGeometryMath_rs/mod.rs
// Author: Gemini Architect
// Version: 20260413.1400.1
//
// Description: High-performance geometry math library. Handles 
// vector operations, normalization, and intersection checks for 
// interactive GUI elements.

use pyo3::prelude::*;

#[pyfunction]
// Inline comment: Logic for normalize_value
fn normalize_value(value: f64, min_val: f64, max_val: f64) -> f64 {
    if (max_val - min_val).abs() < f64::EPSILON {
        return 0.0;
    }
    (value - min_val) / (max_val - min_val)
}

#[pyfunction]
// Inline comment: Logic for value_to_pixel
fn value_to_pixel(value: f64, min_val: f64, max_val: f64, pixel_length: f64, reverse: bool) -> f64 {
    let norm = normalize_value(value, min_val, max_val);
    if reverse {
        (1.0 - norm) * pixel_length
    } else {
        norm * pixel_length
    }
}

#[pyfunction]
// Inline comment: Logic for rotate_point
fn rotate_point(px: f64, py: f64, cx: f64, cy: f64, angle_deg: f64) -> (f64, f64) {
    let rad = angle_deg.to_radians();
    let cos_a = rad.cos();
    let sin_a = rad.sin();
    
    let nx = cos_a * (px - cx) - sin_a * (py - cy) + cx;
    let ny = sin_a * (px - cx) + cos_a * (py - cy) + cy;
    
    (nx, ny)
}

#[pyfunction]
// Inline comment: Logic for get_position
fn get_position(angle_deg: f64, distance: f64, center_x: f64, center_y: f64) -> (f64, f64) {
    let rad = angle_deg.to_radians();
    let x = center_x + distance * rad.cos();
    let y = center_y + distance * rad.sin();
    (x, y)
}

#[pyfunction]
// Inline comment: Logic for get_angle
fn get_angle(px: f64, py: f64, cx: f64, cy: f64) -> f64 {
    let angle_rad = (py - cy).atan2(px - cx);
    angle_rad.to_degrees()
}

#[pymodule]
// Inline comment: Logic for oageometrymath_rs
pub fn oageometrymath_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(normalize_value, m)?)?;
    m.add_function(wrap_pyfunction!(value_to_pixel, m)?)?;
    m.add_function(wrap_pyfunction!(rotate_point, m)?)?;
    m.add_function(wrap_pyfunction!(get_position, m)?)?;
    m.add_function(wrap_pyfunction!(get_angle, m)?)?;
    Ok(())
}
