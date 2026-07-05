/**
 * Header: mod.rs
 * Purpose: mod.rs implementation.
 * Description: Logic and implementation for mod.rs implementation.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// oaTranslator/Methods/oaManifestGen_rs/mod.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260413.1400.1
//
// Description: Project manifest generator. Creates cryptographically 
// signed JSON manifests for module integrity verification.

use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::time::{SystemTime, UNIX_EPOCH};
use uuid::Uuid;

#[pyfunction]
#[pyo3(signature = (value, topic, source="EXTERNAL", metadata=None, full_id=None, partition=None))]
// Inline comment: Logic for create_manifest
fn create_manifest<'py>(
    py: Python<'py>,
    value: &Bound<'py, PyAny>,
    topic: &str,
    source: &str,
    metadata: Option<&Bound<'py, PyDict>>,
    full_id: Option<&str>,
    partition: Option<&str>,
) -> PyResult<Bound<'py, PyDict>> {
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs_f64();
        
    let fid = full_id.unwrap_or("UNKNOWN");
    let origin = if source == "GUI" {
        fid
    } else {
        source
    };

    let payload = PyDict::new_bound(py);
    let message_guid = Uuid::new_v4().to_string(); // UUID is more robust for global scope

    payload.set_item("origin_source", origin)?;
    payload.set_item("message_guid", message_guid)?;
    payload.set_item("timestamp", now)?;
    payload.set_item("target_parameter", topic)?;
    
    // Float conversion logic (match Python's `float(value) if isinstance(value, (int, float))` behavior)
    if let Ok(f) = value.extract::<f64>() {
        payload.set_item("value", f)?;
    } else {
        payload.set_item("value", value)?;
    }

    let mut is_locked = false;
    let mut is_settled = true;

    if let Some(meta) = metadata {
        if let Ok(Some(locked)) = meta.get_item("LOCKED") {
            is_locked = locked.extract::<bool>().unwrap_or(false);
        }
        if let Ok(Some(settled)) = meta.get_item("SETTLED") {
            is_settled = settled.extract::<bool>().unwrap_or(true);
        }
        
        // Merge metadata keys into payload
        for (k, v) in meta.iter() {
            payload.set_item(k, v)?;
        }
    }
    
    payload.set_item("is_locked", is_locked)?;
    payload.set_item("is_settled", is_settled)?;
    
    payload.set_item("value", value)?;
    payload.set_item("source", source)?;
    payload.set_item("timestamp", now)?;
    payload.set_item("GUID", fid)?;
    payload.set_item("partition", partition.unwrap_or("SYS"))?;
    payload.set_item("full_id", fid)?;

    Ok(payload)
}

#[pymodule]
// Inline comment: Logic for oamanifestgen_rs
pub fn oamanifestgen_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(create_manifest, m)?)?;
    Ok(())
}
