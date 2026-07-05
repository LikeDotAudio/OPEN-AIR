/**
 * Header: mod.rs
 * Purpose: mod.rs implementation.
 * Description: Logic and implementation for mod.rs implementation.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// oaGuiElements/Methods/oaCMDPMath_rs/mod.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260413.1400.1
//
// Description: Specialized math library for CMDP (Control Message 
// Display Protocol). Handles coordinate transformations and 
// fader-curve calculations.

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use std::f64::consts::PI;

#[pyclass]
struct CMDPMath;

#[pymethods]
impl CMDPMath {
    #[new]
    fn new() -> Self {
        CMDPMath
    }

    fn calculate_rotated_point(&self, px: f64, py: f64, cx: f64, cy: f64, cos_t: f64, sin_t: f64) -> (f64, f64) {
        let delta_x = px - cx;
        let delta_y = py - cy;
        (
            cos_t * delta_x - sin_t * delta_y + cx,
            sin_t * delta_x + cos_t * delta_y + cy
        )
    }

    fn calculate_position(&self, angle_deg: f64, distance: f64, center_x: f64, center_y: f64) -> (f64, f64) {
        let rad = angle_deg * PI / 180.0;
        (
            center_x + distance * rad.cos(),
            center_y + distance * rad.sin()
        )
    }

    fn calculate_angle(&self, px: f64, py: f64, cx: f64, cy: f64) -> f64 {
        (py - cy).atan2(px - cx) * 180.0 / PI
    }

    fn calculate_projection(&self, dx: f64, dy: f64, angle_deg: f64) -> f64 {
        let rad = angle_deg * PI / 180.0;
        dx * rad.cos() + dy * rad.sin()
    }

    fn calculate_fader_geometry<'py>(&self, py: Python<'py>, config: &Bound<'py, PyDict>) -> PyResult<Bound<'py, PyDict>> {
        let center_x: f64 = config.get_item("center_x")?.unwrap().extract()?;
        let center_y: f64 = config.get_item("center_y")?.unwrap().extract()?;
        let track_length: f64 = config.get_item("track_length")?.unwrap().extract()?;
        let angle: f64 = config.get_item("angle")?.unwrap().extract()?;
        let val_curr: f64 = config.get_item("val_curr")?.unwrap().extract()?;
        let val_min: f64 = config.get_item("val_min")?.unwrap().extract()?;
        let val_max: f64 = config.get_item("val_max")?.unwrap().extract()?;
        let rot_curr: f64 = config.get_item("rot_curr")?.unwrap().extract()?;
        
        let hitbox_width: f64 = config.get_item("hitbox_width")?.unwrap().extract()?;
        let hitbox_padding: f64 = config.get_item("hitbox_padding")?.unwrap().extract()?;
        let tick_count: usize = config.get_item("tick_count")?.unwrap().extract()?;
        let tick_inner_offset: f64 = config.get_item("tick_inner_offset")?.unwrap().extract()?;
        let tick_outer_offset: f64 = config.get_item("tick_outer_offset")?.unwrap().extract()?;
        let cap_radius: f64 = config.get_item("cap_radius")?.unwrap().extract()?;
        
        let t_ang_rad = (angle + 90.0) * PI / 180.0;
        let cos_t = t_ang_rad.cos();
        let sin_t = t_ang_rad.sin();

        let result = PyDict::new_bound(py);

        // 1. Hitbox Points
        let mut hitbox_pts = Vec::with_capacity(8);
        let hp1 = self.calculate_rotated_point(center_x - hitbox_width/2.0, center_y - track_length/2.0 - hitbox_padding, center_x, center_y, cos_t, sin_t);
        let hp2 = self.calculate_rotated_point(center_x + hitbox_width/2.0, center_y - track_length/2.0 - hitbox_padding, center_x, center_y, cos_t, sin_t);
        let hp3 = self.calculate_rotated_point(center_x + hitbox_width/2.0, center_y + track_length/2.0 + hitbox_padding, center_x, center_y, cos_t, sin_t);
        let hp4 = self.calculate_rotated_point(center_x - hitbox_width/2.0, center_y + track_length/2.0 + hitbox_padding, center_x, center_y, cos_t, sin_t);
        hitbox_pts.extend_from_slice(&[hp1.0, hp1.1, hp2.0, hp2.1, hp3.0, hp3.1, hp4.0, hp4.1]);
        result.set_item("hitbox", hitbox_pts)?;

        // 2. Track Points
        let timestamp = self.calculate_rotated_point(center_x, center_y - track_length/2.0, center_x, center_y, cos_t, sin_t);
        let te = self.calculate_rotated_point(center_x, center_y + track_length/2.0, center_x, center_y, cos_t, sin_t);
        result.set_item("track", vec![timestamp.0, timestamp.1, te.0, te.1])?;

        // 3. Tick Points
        let mut tick_pts = Vec::with_capacity(tick_count * 4);
        let tick_divisor = (tick_count - 1) as f64;
        for i in 0..tick_count {
            let local_y = (-track_length/2.0) + ((i as f64 / tick_divisor) * track_length);
            let t_start = self.calculate_rotated_point(center_x - tick_inner_offset, center_y + local_y, center_x, center_y, cos_t, sin_t);
            let t_end = self.calculate_rotated_point(center_x - tick_outer_offset, center_y + local_y, center_x, center_y, cos_t, sin_t);
            tick_pts.extend_from_slice(&[t_start.0, t_start.1, t_end.0, t_end.1]);
        }
        result.set_item("ticks", tick_pts)?;

        // 4. Cap Center
        let denom = val_max - val_min;
        let v_norm = if denom != 0.0 { (val_curr - val_min) / denom } else { 0.0 };
        let cap_center = self.calculate_rotated_point(center_x, center_y + (-track_length/2.0) + (v_norm * track_length), center_x, center_y, cos_t, sin_t);
        result.set_item("cap_center", vec![cap_center.0, cap_center.1])?;

        // 5. Potentiometer Pointer
        let pot_start_angle: f64 = 225.0;
        let pot_extent_max: f64 = 270.0;
        let percent_max: f64 = 100.0;
        let pot_degree = pot_start_angle - (rot_curr / percent_max) * pot_extent_max;
        let pot_rad = pot_degree * PI / 180.0;
        let pointer_x = cap_center.0 + (cap_radius - 2.0) * pot_rad.cos();
        let pointer_y = cap_center.1 - (cap_radius - 2.0) * pot_rad.sin();
        result.set_item("pointer", vec![cap_center.0, cap_center.1, pointer_x, pointer_y])?;
        result.set_item("pot_degree", pot_degree)?;

        // 6. Label Position
        let global_center_x: f64 = config.get_item("global_center_x")?.unwrap().extract()?;
        let global_center_y: f64 = config.get_item("global_center_y")?.unwrap().extract()?;
        let far_radius: f64 = config.get_item("far_radius")?.unwrap().extract()?;
        let label_offset_base: f64 = config.get_item("label_offset_base")?.unwrap().extract()?;
        let label_offset_step: f64 = config.get_item("label_offset_step")?.unwrap().extract()?;
        let widget_id: usize = config.get_item("widget_id")?.unwrap().extract()?;
        
        let label_dist = far_radius + label_offset_base + ((widget_id % 2) as f64) * label_offset_step;
        let label_rad = angle * PI / 180.0;
        let label_x = global_center_x + label_dist * label_rad.cos();
        let label_y = global_center_y + label_dist * label_rad.sin();
        result.set_item("label_pos", vec![label_x, label_y])?;

        Ok(result)
    }
}

#[pymodule]
// Inline comment: Logic for oacmdpmath_rs
pub fn oacmdpmath_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<CMDPMath>()?;
    Ok(())
}
