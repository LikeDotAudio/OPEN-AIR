// oaGuiElements/Methods/oaNeedleEngine_rs/src/lib.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260331.2355.1

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use std::f64::consts::PI;

#[pyclass]
struct NeedleEngine;

#[pymethods]
impl NeedleEngine {
    #[new]
    fn new() -> Self {
        NeedleEngine
    }

    /// Calculates coordinates for a needle given a configuration dictionary.
    fn calculate_geometry<'py>(&self, py: Python<'py>, cx: f64, cy: f64, config: &Bound<'py, PyDict>) -> PyResult<Bound<'py, PyDict>> {
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
        result.set_item("tip_x", tip_x)?;
        result.set_item("tip_y", tip_y)?;
        result.set_item("angle_rad", angle_rad)?;

        let coords_list = PyList::empty_bound(py);
        let mut draw_type = "line";

        match style.as_str() {
            "taper" => {
                draw_type = "polygon";
                let perp_angle = angle_rad + (PI / 2.0);
                let base_rad = pivot_size / 2.0;
                let bx1 = cx + base_rad * perp_angle.cos();
                let by1 = cy - base_rad * perp_angle.sin();
                let bx2 = cx - base_rad * perp_angle.cos();
                let by2 = cy + base_rad * perp_angle.sin();
                
                let _ = coords_list.append(bx1);
                let _ = coords_list.append(by1);
                let _ = coords_list.append(tip_x);
                let _ = coords_list.append(tip_y);
                let _ = coords_list.append(bx2);
                let _ = coords_list.append(by2);
            },
            "knife-edge" => {
                draw_type = "polygon";
                let perp_angle = angle_rad + (PI / 2.0);
                let base_rad = thick * 1.5;
                let bx1 = cx + base_rad * perp_angle.cos();
                let by1 = cy - base_rad * perp_angle.sin();
                let bx2 = cx - base_rad * perp_angle.cos();
                let by2 = cy + base_rad * perp_angle.sin();
                
                let _ = coords_list.append(bx1);
                let _ = coords_list.append(by1);
                let _ = coords_list.append(tip_x);
                let _ = coords_list.append(tip_y);
                let _ = coords_list.append(bx2);
                let _ = coords_list.append(by2);
            },
            "baton" => {
                draw_type = "polygon";
                let perp_angle = angle_rad + (PI / 2.0);
                let off_x = (thick / 2.0) * perp_angle.cos();
                let off_y = (thick / 2.0) * perp_angle.sin();
                
                let _ = coords_list.append(cx + off_x);
                let _ = coords_list.append(cy - off_y);
                let _ = coords_list.append(tip_x + off_x);
                let _ = coords_list.append(tip_y - off_y);
                let _ = coords_list.append(tip_x - off_x);
                let _ = coords_list.append(tip_y + off_y);
                let _ = coords_list.append(cx - off_x);
                let _ = coords_list.append(cy + off_y);
            },
            "teardrop" | "spade" => {
                // Teardrop has complex mixed line and polygon in Python.
                // We'll return the base line coordinates and a "complex" draw type flag
                // so Python can do the specific canvas calls with the pre-calculated points.
                draw_type = "complex_teardrop";
                
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
                
                result.set_item("p1x", p1x)?; result.set_item("p1y", p1y)?;
                result.set_item("p2x", p2x)?; result.set_item("p2y", p2y)?;
                result.set_item("bx", bx)?; result.set_item("by", by)?;
                result.set_item("s1x", s1x)?; result.set_item("s1y", s1y)?;
                result.set_item("s2x", s2x)?; result.set_item("s2y", s2y)?;
            },
            "hollow-diamond" => {
                draw_type = "complex_hollow_diamond";
                
                let d_mid = length * 0.8;
                let d_start = length * 0.6;
                let perp_angle = angle_rad + (PI / 2.0);
                let width = thick * 4.0;
                
                let mx = cx + d_mid * angle_rad.cos();
                let my = cy - d_mid * angle_rad.sin();
                let sx = cx + d_start * angle_rad.cos();
                let sy = cy - d_start * angle_rad.sin();
                
                let p1x = mx + width * perp_angle.cos();
                let p1y = my - width * perp_angle.sin();
                let p2x = mx - width * perp_angle.cos();
                let p2y = my + width * perp_angle.sin();
                
                let i_width = width * 0.6;
                let i_start = d_start + (thick * 2.0);
                let i_tip_dist = length - (thick * 2.0);
                
                let itx = cx + i_tip_dist * angle_rad.cos();
                let ity = cy - i_tip_dist * angle_rad.sin();
                let ip1x = mx + i_width * perp_angle.cos();
                let ip1y = my - i_width * perp_angle.sin();
                let ip2x = mx - i_width * perp_angle.cos();
                let ip2y = my + i_width * perp_angle.sin();
                
                let cutout_sx = sx + (thick * 2.0) * angle_rad.cos();
                let cutout_sy = sy - (thick * 2.0) * angle_rad.sin();
                
                result.set_item("mx", mx)?; result.set_item("my", my)?;
                result.set_item("sx", sx)?; result.set_item("sy", sy)?;
                result.set_item("p1x", p1x)?; result.set_item("p1y", p1y)?;
                result.set_item("p2x", p2x)?; result.set_item("p2y", p2y)?;
                result.set_item("itx", itx)?; result.set_item("ity", ity)?;
                result.set_item("ip1x", ip1x)?; result.set_item("ip1y", ip1y)?;
                result.set_item("ip2x", ip2x)?; result.set_item("ip2y", ip2y)?;
                result.set_item("cutout_sx", cutout_sx)?; result.set_item("cutout_sy", cutout_sy)?;
            },
            _ => { // line
                let _ = coords_list.append(cx);
                let _ = coords_list.append(cy);
                let _ = coords_list.append(tip_x);
                let _ = coords_list.append(tip_y);
            }
        }

        result.set_item("draw_type", draw_type)?;
        result.set_item("coords", coords_list)?;
        result.set_item("length", length)?;

        Ok(result)
    }
}

#[pymodule]
fn oaneedleengine_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<NeedleEngine>()?;
    Ok(())
}
