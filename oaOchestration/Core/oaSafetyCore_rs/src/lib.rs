// oaOchestration/Core/oaSafetyCore_rs/src/lib.rs
// Author: Gemini Iron Oxide Architect
// Version: 20260401.2355.3

use pyo3::prelude::*;
use pyo3::types::PyDict;
use serde_json::Value;

#[pyfunction]
fn validate_json(data: &Bound<'_, PyDict>) -> PyResult<bool> {
    // 1. Convert PyDict to JSON string (clone the bound reference for pythonize)
    let json_str: String = pythonize::depythonize_bound(data.as_any().clone())
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyTypeError, _>(format!("Serialization error: {}", e)))?;

    // 2. Parse into Serde Value to ensure strict JSON compliance
    let _: Value = serde_json::from_str(&json_str)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Invalid JSON structure: {}", e)))?;

    Ok(true)
}

#[pymodule]
fn oasafetycore_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(validate_json, m)?)?;
    Ok(())
}
