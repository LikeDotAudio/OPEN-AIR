// oaOchestration/Core/oaSafetyCore_rs/src/lib.rs
// Author: Gemini Iron Oxide Architect
// Version: 20260401.2355.4

use pyo3::prelude::*;
use pyo3::types::PyDict;
use serde_json::Value;
use pythonize::depythonize;

#[pyfunction]
fn validate_json(data: Bound<'_, PyDict>) -> PyResult<bool> {
    // 1. Convert PyDict to serde_json::Value (The correct way to validate structure)
    let val: Value = depythonize(&data.into_any())
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyTypeError, _>(format!("Serialization error: {}", e)))?;

    // 2. val is now a strictly compliant Serde Value. 
    // If it reached here, it's valid JSON data.
    let _ = val;

    Ok(true)
}

#[pymodule]
fn oasafetycore_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(validate_json, m)?)?;
    Ok(())
}
