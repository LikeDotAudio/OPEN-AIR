// oaGuiElements/Methods/oaNeedleGeometry_rs/src/lib.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260401.1000.1

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use std::f64::consts::PI;

// --- Constants from Python constants.py ---
const SAFE_MARGIN: f64 = 10.0;

// Squircle / Squectangle Constants
const SQUIRCLE_N: f64 = 3.5;
const SQUIRCLE_WIDTH_FACTOR: f64 = 1.0;
const SQUIRCLE_HEIGHT_FACTOR: f64 = 1.0;
const SQUECTANGLE_WIDTH_FACTOR: f64 = 1.7;
const SQUECTANGLE_HEIGHT_FACTOR: f64 = 0.85;
const SQUIRCLE_STEPS: usize = 40;

// Crest Constants
const CREST_CURVE_STEPS: usize = 15;
const CREST_TOP_WIDTH_FACTOR: f64 = 1.5;
const CREST_TOP_HEIGHT_FACTOR: f64 = 1.76;
const CREST_BOTTOM_HEIGHT_FACTOR: f64 = 0.6;

// Cylinder / Hotdog Constants
const HOTDOG_WIDTH_STRAIGHT: f64 = 1.9;
const HOTDOG_CAP_RADIUS: f64 = 1.01;
const HOTDOG_CAP_CENTER_Y: f64 = 1.01;

const CYLINDER_WIDTH_STRAIGHT: f64 = 1.2;
const CYLINDER_CAP_RADIUS: f64 = 0.65;
const CYLINDER_CAP_CENTER_Y: f64 = 0.6;
const CYLINDER_STEPS: usize = 10;

// Gem Constants
const GEM_WIDTH_FACTOR: f64 = 0.51;
const GEM_BASE_HEIGHT: f64 = 0.3;
const GEM_SHOULDER_WIDTH: f64 = 0.69;
const GEM_SHOULDER_HEIGHT: f64 = 0.6;
const GEM_PEAK_HEIGHT: f64 = 0.98;

// Stereo Diamond Constants
const STEREO_DIAMOND_WIDTH: f64 = 1.4;
const STEREO_DIAMOND_HEIGHT: f64 = 1.0;
const STEREO_DIAMOND_FLAT_WIDTH: f64 = 0.6;

// Intersecting Overlay Constants
const INTERSECTING_OVERLAY_WIDTH: f64 = 1.77;
const INTERSECTING_OVERLAY_HEIGHT: f64 = 1.0;
const INTERSECTING_OVERLAY_SKEW: f64 = 0.3;
const INTERSECTING_OVERLAY_CUTOUT_RADIUS: f64 = 0.4;

// Triangle Constants
const TRIANGLE_BASE_WIDTH: f64 = 1.8;
const TRIANGLE_PEAK_HEIGHT: f64 = 1.7;

// Pyramid Constants
const PYRAMID_BASE_WIDTH: f64 = 1.8;
const PYRAMID_PEAK_HEIGHT: f64 = 1.7;

// Hex Constants
const HEX_MID_WIDTH: f64 = 1.8;
const HEX_MID_HEIGHT: f64 = 0.8;
const HEX_TOP_WIDTH: f64 = 1.2;
const HEX_TOP_HEIGHT: f64 = 1.8;

// Trapezoid/Badge Constants
const TRAPEZOID_TOP_WIDTH: f64 = 1.6;
const TRAPEZOID_TOP_HEIGHT: f64 = 1.6;
const TRAPEZOID_BOTTOM_WIDTH: f64 = 1.3;

// Expansion Factors
const GEM_BEZEL_EXPANSION: f64 = 3.06;
const HEX_BEZEL_EXPANSION: f64 = 1.4;
const OCTAGON_BEZEL_EXPANSION: f64 = 1.4;
const TRIANGLE_BEZEL_EXPANSION: f64 = 4.32;
const PARKING_METER_BEZEL_EXPANSION: f64 = 4.32;
const PYRAMID_BEZEL_EXPANSION: f64 = 4.32;

// Shadow Constants
const MAX_SHADOW_X: f64 = 6.0;
const MAX_SHADOW_Y: f64 = 6.0;

#[pyclass]
struct NeedleGeometry;

#[pymethods]
impl NeedleGeometry {
    #[new]
    fn new() -> Self {
        NeedleGeometry
    }

    fn get_bezel_points<'py>(&self, py: Python<'py>, cx: f64, cy: f64, w: f64, h: f64, shape: &str, line_width: f64, shrink_px: f64) -> PyResult<(Bound<'py, PyList>, bool)> {
        let (radius, global_y_shift, shape_key) = self.get_scaling_params(w, h, shape, line_width);
        
        let m_w = self.get_multiplier_w(&shape_key);
        let m_h = self.get_multiplier_h(&shape_key);
        let mut adj_radius = radius - (shrink_px / m_w.max(m_h));
        if adj_radius < 1.0 { adj_radius = 1.0; }

        let (pts, is_smooth) = match shape_key.as_str() {
            "gem" => self._get_gem(adj_radius, global_y_shift),
            "super_gem" => self._get_super_gem(adj_radius, global_y_shift),
            "parking_meter" => self._get_parking_meter(adj_radius, global_y_shift),
            "octagon" => self._get_octagon(adj_radius, global_y_shift),
            "triangle" => self._get_triangle(adj_radius, global_y_shift),
            "pyramid" => self._get_pyramid(adj_radius, global_y_shift),
            "cylinder" | "hotdog" => self._get_hotdog_cylinder(adj_radius, global_y_shift, &shape_key),
            "hex" => self._get_hex(adj_radius, global_y_shift),
            "squectangle" => self._get_squectangle(adj_radius, global_y_shift),
            "squimonde" => self._get_squimonde(adj_radius, global_y_shift),
            "squircle" => self._get_squircle(adj_radius, global_y_shift),
            "trapezoid" | "badge" => self._get_trapezoid(adj_radius, global_y_shift),
            "crest" => self._get_crest(adj_radius, global_y_shift),
            "stereo_diamond" => self._get_stereo_diamond(adj_radius, global_y_shift),
            "intersecting_overlay" => self._get_intersecting_overlay(adj_radius, global_y_shift),
            _ => (Vec::new(), false),
        };

        let flat_pts = PyList::empty_bound(py);
        for (px, py_val) in pts {
            let _ = flat_pts.append(cx + px);
            let _ = flat_pts.append(cy - py_val);
        }

        Ok((flat_pts, is_smooth))
    }

    fn calculate_shadow_geometry<'py>(&self, py: Python<'py>, cx: f64, cy: f64, config: &Bound<'py, PyDict>) -> PyResult<Bound<'py, PyDict>> {
        let val: f64 = config.get_item("val")?.unwrap().extract()?;
        let min_val: f64 = config.get_item("min_val")?.unwrap().extract()?;
        let max_val: f64 = config.get_item("max_val")?.unwrap().extract()?;
        let start_angle_deg: f64 = config.get_item("start_angle_deg")?.unwrap().extract()?;
        let end_angle_deg: f64 = config.get_item("end_angle_deg")?.unwrap().extract()?;
        let extent_deg: f64 = config.get_item("extent_deg")?.unwrap().extract()?;
        let main_arc_radius: f64 = config.get_item("main_arc_radius")?.unwrap().extract()?;
        let text_offset_from_arc: f64 = config.get_item("text_offset_from_arc")?.unwrap().extract()?;
        let style: String = config.get_item("style")?.unwrap().extract()?;
        let thick: f64 = config.get_item("thick")?.unwrap().extract()?;
        let counter_clockwise: bool = config.get_item("counter_clockwise")?.unwrap().extract()?;
        let pivot_size: f64 = config.get_item("pivot_size")?.unwrap().extract()?;
        let needle_scale: f64 = config.get_item("needle_scale")?.map(|v| v.extract().unwrap_or(1.0)).unwrap_or(1.0);

        let bounded_val = val.clamp(min_val, max_val);
        let range_val = max_val - min_val;
        let norm_val = if range_val != 0.0 { (bounded_val - min_val) / range_val } else { 0.0 };

        let angle_deg = if counter_clockwise {
            end_angle_deg + (norm_val * extent_deg)
        } else {
            start_angle_deg - (norm_val * extent_deg)
        };

        let angle_rad = angle_deg * PI / 180.0;
        let length = (main_arc_radius + text_offset_from_arc - 2.0) * needle_scale;
        
        let tip_x = cx + length * angle_rad.cos();
        let tip_y = cy - length * angle_rad.sin();

        let result = PyDict::new_bound(py);
        let coords_list = PyList::empty_bound(py);
        
        let get_shadow_pt = |px: f64, py_val: f64| -> (f64, f64) {
            let d = ((px - cx).powi(2) + (py_val - cy).powi(2)).sqrt();
            let factor = (d / length).clamp(0.0, 1.0);
            (px + MAX_SHADOW_X * factor, py_val + MAX_SHADOW_Y * factor)
        };

        match style.as_str() {
            "teardrop" | "spade" => {
                let d1 = length * 0.75;
                let d2 = length * 0.875;
                let p1x = cx + d1 * angle_rad.cos();
                let p1y = cy - d1 * angle_rad.sin();
                let p2x = cx + d2 * angle_rad.cos();
                let p2y = cy - d2 * angle_rad.sin();
                let bulb_w = thick * 2.5;
                let perp_angle = angle_rad + (PI / 2.0);
                let bx = cx + (d1 - thick) * angle_rad.cos();
                let by = cy - (d1 - thick) * angle_rad.sin();
                let mid_dist = (d1 + d2) / 2.0;
                let mx = cx + mid_dist * angle_rad.cos();
                let my = cy - mid_dist * angle_rad.sin();
                let s1x = mx + bulb_w * perp_angle.cos();
                let s1y = my - bulb_w * perp_angle.sin();
                let s2x = mx - bulb_w * perp_angle.cos();
                let s2y = my + bulb_w * perp_angle.sin();

                let sc = get_shadow_pt(cx, cy);
                let sp1 = get_shadow_pt(p1x, p1y);
                let sb = get_shadow_pt(bx, by);
                let ss1 = get_shadow_pt(s1x, s1y);
                let sp2 = get_shadow_pt(p2x, p2y);
                let ss2 = get_shadow_pt(s2x, s2y);
                let stip = get_shadow_pt(tip_x, tip_y);

                result.set_item("line1", vec![sc.0, sc.1, sp1.0, sp1.1])?;
                result.set_item("poly", vec![sb.0, sb.1, ss1.0, ss1.1, sp2.0, sp2.1, ss2.0, ss2.1])?;
                result.set_item("line2", vec![sp2.0, sp2.1, stip.0, stip.1])?;
                result.set_item("type", "teardrop")?;
            },
            "knife-edge" | "taper" => {
                let perp_angle = angle_rad + (PI / 2.0);
                let base_rad = if style == "taper" { pivot_size / 2.0 } else { thick * 1.5 };
                let bx1 = cx + base_rad * perp_angle.cos();
                let by1 = cy - base_rad * perp_angle.sin();
                let bx2 = cx - base_rad * perp_angle.cos();
                let by2 = cy + base_rad * perp_angle.sin();
                
                let sb1 = get_shadow_pt(bx1, by1);
                let sb2 = get_shadow_pt(bx2, by2);
                let stip = get_shadow_pt(tip_x, tip_y);
                
                let _ = coords_list.append(sb1.0); let _ = coords_list.append(sb1.1);
                let _ = coords_list.append(stip.0); let _ = coords_list.append(stip.1);
                let _ = coords_list.append(sb2.0); let _ = coords_list.append(sb2.1);
                result.set_item("coords", coords_list)?;
                result.set_item("type", "polygon")?;
            },
            "baton" => {
                let perp_angle = angle_rad + (PI / 2.0);
                let ox = (thick / 2.0) * perp_angle.cos();
                let oy = (thick / 2.0) * perp_angle.sin();
                
                let s1 = get_shadow_pt(cx + ox, cy - oy);
                let s2 = get_shadow_pt(tip_x + ox, tip_y - oy);
                let s3 = get_shadow_pt(tip_x - ox, tip_y + oy);
                let s4 = get_shadow_pt(cx - ox, cy + oy);
                
                let _ = coords_list.append(s1.0); let _ = coords_list.append(s1.1);
                let _ = coords_list.append(s2.0); let _ = coords_list.append(s2.1);
                let _ = coords_list.append(s3.0); let _ = coords_list.append(s3.1);
                let _ = coords_list.append(s4.0); let _ = coords_list.append(s4.1);
                result.set_item("coords", coords_list)?;
                result.set_item("type", "polygon")?;
            },
            _ => { // line
                let sc = get_shadow_pt(cx, cy);
                let stip = get_shadow_pt(tip_x, tip_y);
                let _ = coords_list.append(sc.0); let _ = coords_list.append(sc.1);
                let _ = coords_list.append(stip.0); let _ = coords_list.append(stip.1);
                result.set_item("coords", coords_list)?;
                result.set_item("type", "line")?;
            }
        }
        
        Ok(result)
    }
}

impl NeedleGeometry {
    fn get_scaling_params(&self, w: f64, h: f64, shape: &str, line_width: f64) -> (f64, f64, String) {
        let mut shape_key = shape.to_lowercase();
        if !self.has_multiplier(&shape_key) {
            if shape_key == "triangle" || shape_key == "pyramid" { shape_key = "triangle".to_string(); }
            else if shape_key == "cylinder" || shape_key == "hotdog" { shape_key = if shape_key == "hotdog" { "hotdog".to_string() } else { "cylinder".to_string() }; }
            else if shape_key == "trapezoid" || shape_key == "badge" { shape_key = "trapezoid".to_string(); }
            else { shape_key = "default".to_string(); }
        }

        let m_w = self.get_multiplier_w(&shape_key);
        let m_h = self.get_multiplier_h(&shape_key);
        let y_shift_factor = self.get_y_shift(&shape_key);

        let avail_w = (w / 2.0) - (line_width / 2.0) - SAFE_MARGIN;
        let avail_h = h - (line_width / 2.0) - SAFE_MARGIN;
        
        let radius = (avail_w / m_w).min(avail_h / m_h);
        let global_y_shift = y_shift_factor * radius;
        
        (radius, global_y_shift, shape_key)
    }

    fn has_multiplier(&self, shape: &str) -> bool {
        match shape {
            "gem" | "super_gem" | "triangle" | "parking_meter" | "pyramid" | "hotdog" | "cylinder" | "hex" | "octagon" | "squircle" | "squimonde" | "squectangle" | "trapezoid" | "badge" | "crest" | "stereo_diamond" | "intersecting_overlay" | "default" => true,
            _ => false
        }
    }

    fn get_multiplier_w(&self, shape: &str) -> f64 {
        match shape {
            "gem" => 1.9, "super_gem" => 1.9, "triangle" => 2.0, "parking_meter" => 2.0, "pyramid" => 2.0,
            "hotdog" => 2.91, "cylinder" => 1.85, "hex" => 2.52, "octagon" => 1.5, "squircle" => 1.2,
            "squimonde" => 1.9, "squectangle" => 1.7, "trapezoid" | "badge" => 1.8, "crest" => 1.5,
            "stereo_diamond" => 3.5, "intersecting_overlay" => 4.0, _ => 1.5
        }
    }

    fn get_multiplier_h(&self, shape: &str) -> f64 {
        match shape {
            "gem" => 2.4, "super_gem" => 2.4, "triangle" => 2.0, "parking_meter" => 2.5, "pyramid" => 2.0,
            "hotdog" => 3.5, "cylinder" => 1.3, "hex" => 2.6, "octagon" => 1.5, "squircle" => 3.5,
            "squimonde" => 1.9, "squectangle" => 2.1, "trapezoid" | "badge" => 2.6, "crest" => 2.1,
            "stereo_diamond" => 2.5, "intersecting_overlay" => 2.25, _ => 1.5
        }
    }

    fn get_y_shift(&self, shape: &str) -> f64 {
        match shape {
            "hotdog" => 1.30, "pyramid" => 0.5, "triangle" => 0.5, "parking_meter" => 0.5, "hex" => 0.5,
            "octagon" => 0.9, "squircle" => 0.4, "squimonde" => 0.014, "squectangle" => 0.4, "crest" => 0.2,
            "badge" | "trapezoid" => 0.3, "gem" => 0.5, "super_gem" => 0.5, _ => 0.0
        }
    }

    fn _get_gem(&self, radius: f64, global_y_shift: f64) -> (Vec<(f64, f64)>, bool) {
        let gem_rad = radius * GEM_BEZEL_EXPANSION;
        let pts = vec![
            (0.0, GEM_BASE_HEIGHT * gem_rad + global_y_shift),
            (GEM_WIDTH_FACTOR * gem_rad, GEM_BASE_HEIGHT * gem_rad + global_y_shift),
            (GEM_SHOULDER_WIDTH * gem_rad, GEM_SHOULDER_HEIGHT * gem_rad + global_y_shift),
            (0.0, GEM_PEAK_HEIGHT * gem_rad + global_y_shift),
            (-GEM_SHOULDER_WIDTH * gem_rad, GEM_SHOULDER_HEIGHT * gem_rad + global_y_shift),
            (-GEM_WIDTH_FACTOR * gem_rad, GEM_BASE_HEIGHT * gem_rad + global_y_shift)
        ];
        (pts, false)
    }

    fn _get_super_gem(&self, radius: f64, global_y_shift: f64) -> (Vec<(f64, f64)>, bool) {
        let gem_rad = radius * GEM_BEZEL_EXPANSION;
        let pts = vec![
            (0.0, -(GEM_BASE_HEIGHT * gem_rad) + global_y_shift),
            (GEM_WIDTH_FACTOR * gem_rad, -(GEM_BASE_HEIGHT * gem_rad) + global_y_shift),
            (GEM_SHOULDER_WIDTH * gem_rad, -(GEM_SHOULDER_HEIGHT * gem_rad) + global_y_shift),
            (0.0, -(GEM_PEAK_HEIGHT * gem_rad) + global_y_shift),
            (-GEM_SHOULDER_WIDTH * gem_rad, -(GEM_SHOULDER_HEIGHT * gem_rad) + global_y_shift),
            (-GEM_WIDTH_FACTOR * gem_rad, -(GEM_BASE_HEIGHT * gem_rad) + global_y_shift)
        ];
        (pts, false)
    }

    fn _get_parking_meter(&self, radius: f64, global_y_shift: f64) -> (Vec<(f64, f64)>, bool) {
        let pm_rad = radius * PARKING_METER_BEZEL_EXPANSION;
        let w_val = TRIANGLE_BASE_WIDTH * pm_rad;
        let h_val = TRIANGLE_PEAK_HEIGHT * pm_rad;
        let arc_radius = (w_val.powi(2) + h_val.powi(2)).sqrt();
        let ang_start = h_val.atan2(w_val);
        let ang_end = h_val.atan2(-w_val);
        let mut pts = vec![(0.0, 0.0 + global_y_shift)];
        let steps = 20;
        for i in 0..=steps {
            let ang = ang_start + (ang_end - ang_start) * (i as f64 / steps as f64);
            let px = arc_radius * ang.cos();
            let py = arc_radius * ang.sin() + global_y_shift;
            pts.push((px, py));
        }
        (pts, false)
    }

    fn _get_octagon(&self, radius: f64, global_y_shift: f64) -> (Vec<(f64, f64)>, bool) {
        let oct_rad = radius * OCTAGON_BEZEL_EXPANSION;
        let mut pts = Vec::new();
        for i in 0..8 {
            let ang = (22.5 + (i as f64 * 45.0)) * PI / 180.0;
            let px = oct_rad * ang.cos();
            let py = oct_rad * ang.sin() + global_y_shift;
            pts.push((px, py));
        }
        (pts, false)
    }

    fn _get_triangle(&self, radius: f64, global_y_shift: f64) -> (Vec<(f64, f64)>, bool) {
        let tri_rad = radius * TRIANGLE_BEZEL_EXPANSION;
        let pts = vec![
            (0.0, 0.0 + global_y_shift),
            (TRIANGLE_BASE_WIDTH * tri_rad, TRIANGLE_PEAK_HEIGHT * tri_rad + global_y_shift),
            (-TRIANGLE_BASE_WIDTH * tri_rad, TRIANGLE_PEAK_HEIGHT * tri_rad + global_y_shift)
        ];
        (pts, false)
    }

    fn _get_pyramid(&self, radius: f64, global_y_shift: f64) -> (Vec<(f64, f64)>, bool) {
        let py_rad = radius * PYRAMID_BEZEL_EXPANSION;
        let pts = vec![
            (0.0, PYRAMID_PEAK_HEIGHT * py_rad + global_y_shift),
            (PYRAMID_BASE_WIDTH * py_rad, 0.0 + global_y_shift),
            (-PYRAMID_BASE_WIDTH * py_rad, 0.0 + global_y_shift)
        ];
        (pts, false)
    }

    fn _get_hotdog_cylinder(&self, radius: f64, global_y_shift: f64, shape_key: &str) -> (Vec<(f64, f64)>, bool) {
        let (w_straight, r_cap, cap_center_y) = if shape_key == "hotdog" {
            (HOTDOG_WIDTH_STRAIGHT * radius, HOTDOG_CAP_RADIUS * radius, HOTDOG_CAP_CENTER_Y * radius)
        } else {
            (CYLINDER_WIDTH_STRAIGHT * radius, CYLINDER_CAP_RADIUS * radius, CYLINDER_CAP_CENTER_Y * radius)
        };
        
        let mut pts = vec![(0.0, 0.0 + global_y_shift), (w_straight, 0.0 + global_y_shift)];
        let steps = CYLINDER_STEPS;
        for i in 0..=steps {
            let ang = (-90.0 + (180.0 * i as f64 / steps as f64)) * PI / 180.0;
            let px = w_straight + r_cap * ang.cos();
            let py = cap_center_y + r_cap * ang.sin();
            pts.push((px, py + global_y_shift));
        }
        for i in 0..=steps {
            let ang = (90.0 + (180.0 * i as f64 / steps as f64)) * PI / 180.0;
            let px = -w_straight + r_cap * ang.cos();
            let py = cap_center_y + r_cap * ang.sin();
            pts.push((px, py + global_y_shift));
        }
        pts.push((0.0, 0.0 + global_y_shift));
        (pts, false)
    }

    fn _get_hex(&self, radius: f64, global_y_shift: f64) -> (Vec<(f64, f64)>, bool) {
        let hex_rad = radius * HEX_BEZEL_EXPANSION;
        let pts = vec![
            (0.0, 0.0 + global_y_shift),
            (HEX_TOP_WIDTH * hex_rad, 0.0 + global_y_shift),
            (HEX_MID_WIDTH * hex_rad, HEX_MID_HEIGHT * hex_rad + global_y_shift),
            (HEX_TOP_WIDTH * hex_rad, HEX_TOP_HEIGHT * hex_rad + global_y_shift),
            (-HEX_TOP_WIDTH * hex_rad, HEX_TOP_HEIGHT * hex_rad + global_y_shift),
            (-HEX_MID_WIDTH * hex_rad, HEX_MID_HEIGHT * hex_rad + global_y_shift),
            (-HEX_TOP_WIDTH * hex_rad, 0.0 + global_y_shift)
        ];
        (pts, false)
    }

    fn _get_squectangle(&self, radius: f64, global_y_shift: f64) -> (Vec<(f64, f64)>, bool) {
        let mut pts = Vec::new();
        let n = SQUIRCLE_N;
        let w_sq = SQUECTANGLE_WIDTH_FACTOR * radius;
        let h_sq = SQUECTANGLE_HEIGHT_FACTOR * radius;
        let steps = SQUIRCLE_STEPS;
        for i in 0..=steps {
            let t = -PI/2.0 + (2.0 * PI * i as f64 / steps as f64);
            let c = t.cos();
            let s = t.sin();
            let x = w_sq * (if c >= 0.0 { 1.0 } else { -1.0 }) * (c.abs().powf(2.0/n));
            let y_raw = h_sq * (if s >= 0.0 { 1.0 } else { -1.0 }) * (s.abs().powf(2.0/n));
            pts.push((x, y_raw + h_sq + global_y_shift));
        }
        (pts, true)
    }

    fn _get_squimonde(&self, radius: f64, global_y_shift: f64) -> (Vec<(f64, f64)>, bool) {
        let mut pts = Vec::new();
        let n = SQUIRCLE_N;
        let w_sq = SQUIRCLE_WIDTH_FACTOR * radius;
        let h_sq = SQUIRCLE_HEIGHT_FACTOR * radius;
        let steps = SQUIRCLE_STEPS;
        let rot_angle = PI / 4.0;
        let cos_r = rot_angle.cos();
        let sin_r = rot_angle.sin();
        for i in 0..=steps {
            let t = -PI/2.0 + (2.0 * PI * i as f64 / steps as f64);
            let c = t.cos();
            let s = t.sin();
            let x_raw = w_sq * (if c >= 0.0 { 1.0 } else { -1.0 }) * (c.abs().powf(2.0/n));
            let y_raw = h_sq * (if s >= 0.0 { 1.0 } else { -1.0 }) * (s.abs().powf(2.0/n));
            let x_rot = x_raw * cos_r - y_raw * sin_r;
            let y_rot = x_raw * sin_r + y_raw * cos_r;
            pts.push((x_rot, y_rot + h_sq + global_y_shift));
        }
        (pts, true)
    }

    fn _get_squircle(&self, radius: f64, global_y_shift: f64) -> (Vec<(f64, f64)>, bool) {
        let mut pts = Vec::new();
        let n = SQUIRCLE_N;
        let w_sq = SQUIRCLE_WIDTH_FACTOR * radius;
        let h_sq = SQUIRCLE_HEIGHT_FACTOR * radius;
        let steps = SQUIRCLE_STEPS;
        for i in 0..=steps {
            let t = -PI/2.0 + (2.0 * PI * i as f64 / steps as f64);
            let c = t.cos();
            let s = t.sin();
            let x = w_sq * (if c >= 0.0 { 1.0 } else { -1.0 }) * (c.abs().powf(2.0/n));
            let y_raw = h_sq * (if s >= 0.0 { 1.0 } else { -1.0 }) * (s.abs().powf(2.0/n));
            pts.push((x, y_raw + h_sq + global_y_shift));
        }
        (pts, true)
    }

    fn _get_trapezoid(&self, radius: f64, global_y_shift: f64) -> (Vec<(f64, f64)>, bool) {
        let pts = vec![
            (0.0, 0.0 + global_y_shift),
            (TRAPEZOID_BOTTOM_WIDTH * radius, 0.0 + global_y_shift),
            (TRAPEZOID_TOP_WIDTH * radius, TRAPEZOID_TOP_HEIGHT * radius + global_y_shift),
            (-TRAPEZOID_TOP_WIDTH * radius, TRAPEZOID_TOP_HEIGHT * radius + global_y_shift),
            (-TRAPEZOID_BOTTOM_WIDTH * radius, 0.0 + global_y_shift)
        ];
        (pts, false)
    }

    fn _get_crest(&self, radius: f64, global_y_shift: f64) -> (Vec<(f64, f64)>, bool) {
        let mut pts = vec![(0.0, 0.0 + global_y_shift)];
        let curve_steps = CREST_CURVE_STEPS;
        for i in 1..=curve_steps {
            let y_u = CREST_BOTTOM_HEIGHT_FACTOR * radius * (i as f64 / curve_steps as f64);
            let x_u = CREST_TOP_WIDTH_FACTOR * radius * (y_u / (CREST_BOTTOM_HEIGHT_FACTOR * radius)).sqrt();
            pts.push((x_u, y_u + global_y_shift));
        }
        pts.push((CREST_TOP_WIDTH_FACTOR * radius, CREST_TOP_HEIGHT_FACTOR * radius + global_y_shift));
        pts.push((-CREST_TOP_WIDTH_FACTOR * radius, CREST_TOP_HEIGHT_FACTOR * radius + global_y_shift));
        pts.push((-CREST_TOP_WIDTH_FACTOR * radius, CREST_BOTTOM_HEIGHT_FACTOR * radius + global_y_shift));
        for i in (0..curve_steps).rev() {
            let mut y_u = CREST_BOTTOM_HEIGHT_FACTOR * radius * (i as f64 / curve_steps as f64);
            if y_u < 0.01 { y_u = 0.0; }
            let x_u = CREST_TOP_WIDTH_FACTOR * radius * (y_u / (CREST_BOTTOM_HEIGHT_FACTOR * radius)).sqrt();
            pts.push((-x_u, y_u + global_y_shift));
        }
        (pts, false)
    }

    fn _get_stereo_diamond(&self, radius: f64, global_y_shift: f64) -> (Vec<(f64, f64)>, bool) {
        let w_sd = STEREO_DIAMOND_WIDTH * radius;
        let h_sd = STEREO_DIAMOND_HEIGHT * radius;
        let fw = STEREO_DIAMOND_FLAT_WIDTH * radius;
        let pts = vec![
            (fw, h_sd + global_y_shift),
            (w_sd, 0.0 + global_y_shift),
            (fw, -h_sd + global_y_shift),
            (-fw, -h_sd + global_y_shift),
            (-w_sd, 0.0 + global_y_shift),
            (-fw, h_sd + global_y_shift)
        ];
        (pts, false)
    }

    fn _get_intersecting_overlay(&self, radius: f64, global_y_shift: f64) -> (Vec<(f64, f64)>, bool) {
        let w_io = INTERSECTING_OVERLAY_WIDTH * radius;
        let h_io = INTERSECTING_OVERLAY_HEIGHT * radius;
        let skew = INTERSECTING_OVERLAY_SKEW * radius;
        let cr = INTERSECTING_OVERLAY_CUTOUT_RADIUS * radius;
        let mut pts = vec![
            (-w_io + skew, h_io + global_y_shift),
            (w_io + skew, h_io + global_y_shift),
            (w_io - skew, -h_io + global_y_shift)
        ];
        let steps = 20;
        for i in 0..=steps {
            let ang = PI + (PI * i as f64 / steps as f64);
            let px = (w_io - skew) + cr * ang.cos();
            let py = (-h_io) + cr * ang.sin() + global_y_shift;
            pts.push((px, py));
        }
        pts.push((-w_io - skew, -h_io + global_y_shift));
        (pts, false)
    }
}

#[pymodule]
fn oaneedlegeometry_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<NeedleGeometry>()?;
    Ok(())
}
