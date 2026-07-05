/**
 * Header: mod.rs
 * Purpose: mod.rs implementation.
 * Description: Logic and implementation for mod.rs implementation.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// oaGuiElements/Methods/oaRotaryCore_rs/mod.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260413.1400.1
//
// Description: Native rotary encoder logic. Handles angle 
// calculations and ballistic smoothing for virtual knobs.

use pyo3::prelude::*;
use std::f64::consts::PI;

const FULL_CIRCLE_DEGREES: f64 = 360.0;

#[pyclass]
struct RotaryCore;

#[pymethods]
impl RotaryCore {
    #[new]
    fn new() -> Self {
        RotaryCore
    }

    fn calculate_angle(&self, value: f64, min_val: f64, max_val: f64, knob_style: &str) -> f64 {
        let range = if max_val > min_val { max_val - min_val } else { 1.0 };
        let norm_val = ((value - min_val) / range).clamp(0.0, 1.0);

        match knob_style {
            "panner" => {
                let mid_val = (min_val + max_val) / 2.0;
                let norm_from_center = (value - mid_val) / (range / 2.0);
                90.0 + (-1.0 * norm_from_center * 135.0)
            },
            "dial" => {
                let mut val_extent = -FULL_CIRCLE_DEGREES * norm_val;
                if val_extent.abs() >= FULL_CIRCLE_DEGREES {
                    val_extent = -359.9;
                }
                90.0 + val_extent
            },
            _ => { // standard
                240.0 + (-300.0 * norm_val)
            }
        }
    }

    fn get_poly_points(&self, center_x: f64, center_y: f64, radius: f64, sides: usize, start_angle: f64) -> Vec<f64> {
        let mut points = Vec::with_capacity(sides * 2);
        let angle_step = FULL_CIRCLE_DEGREES / (sides as f64);
        
        for i in 0..sides {
            let degrees = (i as f64) * angle_step + start_angle;
            let radians = degrees * PI / 180.0;
            points.push(center_x + radius * radians.cos());
            points.push(center_y - radius * radians.sin());
        }
        points
    }

    fn get_gear_points(&self, center_x: f64, center_y: f64, radius: f64, teeth: usize, notch_depth: f64, start_angle: f64) -> Vec<f64> {
        let points_per_tooth = 4;
        let num_segments = teeth * points_per_tooth;
        let inner_radius = radius * (1.0 - notch_depth);
        let angle_step = FULL_CIRCLE_DEGREES / (num_segments as f64);
        
        let mut points = Vec::with_capacity(num_segments * 2);
        
        for i in 0..num_segments {
            let degrees = (i as f64) * angle_step + start_angle;
            let radians = degrees * PI / 180.0;
            
            let tooth_state = i % 4;
            let current_radius = if tooth_state == 1 || tooth_state == 2 {
                radius
            } else {
                inner_radius
            };
            
            points.push(center_x + current_radius * radians.cos());
            points.push(center_y - current_radius * radians.sin());
        }
        points
    }
}

#[pymodule]
// Inline comment: Logic for oarotarycore_rs
pub fn oarotarycore_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<RotaryCore>()?;
    Ok(())
}
