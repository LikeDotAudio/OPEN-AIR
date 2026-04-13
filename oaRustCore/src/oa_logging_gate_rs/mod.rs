// oaLogging/Methods/oaLoggingGate_rs/src/lib.rs
// Author: Gemini Architect
// Version: 20260401.1955.3

use pyo3::prelude::*;
use dashmap::DashMap;
use once_cell::sync::Lazy;
use std::sync::atomic::{AtomicBool, Ordering};

// Global static for high-speed master toggle
static MASTER_LOG_ENABLED: AtomicBool = AtomicBool::new(true);

// High-speed map of enabled systems and elements
static LOG_MATRIX: Lazy<DashMap<String, bool>> = Lazy::new(DashMap::new);

#[pyfunction]
fn set_master_toggle(enabled: bool) {
    MASTER_LOG_ENABLED.store(enabled, Ordering::SeqCst);
}

#[pyfunction]
#[pyo3(signature = (system, element=None, enabled=true))]
fn set_gate_state(system: String, element: Option<String>, enabled: bool) {
    let key = match element {
        Some(e) => format!("{}:{}", system, e),
        None => system,
    };
    LOG_MATRIX.insert(key, enabled);
}

#[pyfunction]
#[pyo3(signature = (system, element=None, func_name=None))]
fn is_debug_allowed(system: String, element: Option<String>, func_name: Option<String>) -> bool {
    let _ = func_name; // Avoid unused variable warning
    
    // 1. Check Master Toggle
    if !MASTER_LOG_ENABLED.load(Ordering::Relaxed) {
        return false;
    }

    // 2. Check Element-specific gate
    if let Some(e) = &element {
        let key = format!("{}:{}", system, e);
        if let Some(enabled) = LOG_MATRIX.get(&key) {
            return *enabled;
        }
    }

    // 3. Fallback to System-wide gate
    if let Some(enabled) = LOG_MATRIX.get(&system) {
        return *enabled;
    }

    // 4. Default to enabled
    true
}

#[pymodule]
pub fn oalogginggate_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(is_debug_allowed, m)?)?;
    m.add_function(wrap_pyfunction!(set_gate_state, m)?)?;
    m.add_function(wrap_pyfunction!(set_master_toggle, m)?)?;
    Ok(())
}
