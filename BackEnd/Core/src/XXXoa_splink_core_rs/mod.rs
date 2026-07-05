/**
 * Header: mod.rs
 * Purpose: mod.rs implementation.
 * Description: Logic and implementation for mod.rs implementation.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// oaSplinker/Methods/oaSplinkCore_rs/mod.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260413.1400.1
//
// Description: Native SPLINK calculation engine. Handles 
// high-frequency fader curves and parameter translation in Rust.

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyInt};

#[derive(Clone, Debug)]
enum HandlerType {
    Scale {
        s_min: f64,
        s_max: f64,
        d_min: f64,
        d_max: f64,
        is_int: bool,
    },
    Invert {
        min: f64,
        max: f64,
    },
    Deadband {
        threshold_percent: f64,
        max_value: f64,
    },
}

#[pyclass]
struct SplinkPipeline {
    handlers: Vec<HandlerType>,
}

#[pymethods]
impl SplinkPipeline {
    #[new]
    fn new(handler_configs: &Bound<'_, PyList>) -> PyResult<Self> {
        let mut handlers = Vec::new();

        for config in handler_configs.iter() {
            let config_dict = config.downcast::<PyDict>()?;
            
            let enabled: bool = config_dict.get_item("enabled")?
                .and_then(|v| v.extract().ok())
                .unwrap_or(false);
            
            if !enabled {
                continue;
            }

            let h_type: String = config_dict.get_item("type")?
                .and_then(|v| v.extract().ok())
                .unwrap_or_default();
            
            let params = config_dict.get_item("params")?
                .and_then(|v| v.downcast_into::<PyDict>().ok())
                .unwrap_or_else(|| PyDict::new_bound(config_dict.py()));

            match h_type.as_str() {
                "scale" => {
                    let s_min = params.get_item("source_min")?.and_then(|v| v.extract().ok()).unwrap_or(0.0);
                    let s_max = params.get_item("source_max")?.and_then(|v| v.extract().ok()).unwrap_or(100.0);
                    let d_min = params.get_item("dest_min")?.and_then(|v| v.extract().ok()).unwrap_or(0.0);
                    let d_max = params.get_item("dest_max")?.and_then(|v| v.extract().ok()).unwrap_or(255.0);
                    
                    let d_min_val = params.get_item("dest_min")?;
                    let d_max_val = params.get_item("dest_max")?;
                    let is_int = if let (Some(v1), Some(v2)) = (d_min_val, d_max_val) {
                        v1.is_instance_of::<PyInt>() && v2.is_instance_of::<PyInt>()
                    } else {
                        false
                    };

                    handlers.push(HandlerType::Scale { s_min, s_max, d_min, d_max, is_int });
                },
                "invert" => {
                    let min = params.get_item("min_value")?.and_then(|v| v.extract().ok()).unwrap_or(0.0);
                    let max = params.get_item("max_value")?.and_then(|v| v.extract().ok()).unwrap_or(1.0);
                    handlers.push(HandlerType::Invert { min, max });
                },
                "deadband" => {
                    let threshold_percent = params.get_item("threshold_percent")?.and_then(|v| v.extract().ok()).unwrap_or(1.0);
                    let max_value = params.get_item("max_value")?.and_then(|v| v.extract().ok()).unwrap_or(100.0);
                    handlers.push(HandlerType::Deadband { threshold_percent, max_value });
                },
                _ => {}
            }
        }

        Ok(SplinkPipeline { handlers })
    }

    fn process(&self, mut value: Py<PyAny>, _splink: &Bound<'_, PyDict>, state: &Bound<'_, PyDict>, direction: String) -> PyResult<Option<Py<PyAny>>> {
        let py = state.py();

        for handler in &self.handlers {
            match handler {
                HandlerType::Scale { s_min, s_max, d_min, d_max, is_int } => {
                    if let Ok(val_float) = value.extract::<f64>(py) {
                        let (src_in_min, src_in_max, dest_out_min, dest_out_max) = if direction == "REVERSE" {
                            (*d_min, *d_max, *s_min, *s_max)
                        } else {
                            (*s_min, *s_max, *d_min, *d_max)
                        };

                        let in_min = src_in_min.min(src_in_max);
                        let in_max = src_in_min.max(src_in_max);
                        let clamped_val = val_float.max(in_min).min(in_max);

                        let input_span = src_in_max - src_in_min;
                        let output_span = dest_out_max - dest_out_min;
                        
                        let scaled_value = if input_span == 0.0 {
                            dest_out_min
                        } else {
                            dest_out_min + (((clamped_val - src_in_min) / input_span) * output_span)
                        };

                        if *is_int {
                            value = (scaled_value.round() as i64).into_py(py);
                        } else {
                            value = scaled_value.into_py(py);
                        }
                    }
                },
                HandlerType::Invert { min, max } => {
                    if let Ok(val_bool) = value.extract::<bool>(py) {
                        value = (!val_bool).into_py(py);
                    } else if let Ok(val_float) = value.extract::<f64>(py) {
                        let inverted_val = (max + min) - val_float;
                        // Use Bound for downcasting to check for int
                        let value_bound = value.bind(py);
                        if value_bound.is_instance_of::<PyInt>() {
                            value = (inverted_val.round() as i64).into_py(py);
                        } else {
                            value = inverted_val.into_py(py);
                        }
                    }
                },
                HandlerType::Deadband { threshold_percent, max_value } => {
                    let last_val_opt = state.get_item("last_deadband_value")?;
                    
                    if let Some(last_val_any) = last_val_opt {
                        if let (Ok(val_float), Ok(last_val_float)) = (value.extract::<f64>(py), last_val_any.extract::<f64>()) {
                            let change_percent = if *max_value == 0.0 {
                                if val_float == last_val_float { 0.0 } else { 100.0 }
                            } else {
                                ((val_float - last_val_float).abs() / max_value) * 100.0
                            };

                            if change_percent < *threshold_percent {
                                return Ok(None); // Drop
                            }
                        } else if value.bind(py).to_string() == last_val_any.to_string() {
                            return Ok(None); // Drop
                        }
                    }
                    state.set_item("last_deadband_value", &value)?;
                },
            }
        }

        Ok(Some(value))
    }
}

#[pymodule]
// Inline comment: Logic for oasplinkcore_rs
pub fn oasplinkcore_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<SplinkPipeline>()?;
    Ok(())
}
