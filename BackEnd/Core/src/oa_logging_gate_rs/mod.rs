/**
 * Header: mod.rs
 * Purpose: mod.rs implementation.
 * Description: Logic and implementation for mod.rs implementation.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// oaLogging/Methods/oaLoggingGate_rs/mod.rs
// Author: Gemini Architect
// Version: 20260413.0010.1
//
// Description: High-speed native logging filter. Intercepts Python logger 
// calls to determine if a message should reach a sink based on a global 
// matrix. This offloads string-formatting and log-IO from the Python side 
// for disabled trace levels.

use pyo3::prelude::*;
use dashmap::DashMap;
use once_cell::sync::Lazy;
use std::sync::atomic::{AtomicBool, Ordering};

// AtomicBool is used for the master toggle to ensure thread-safe, zero-lock 
// evaluation during high-frequency log bursts (e.g., protocol firehose).
static MASTER_LOG_ENABLED: AtomicBool = AtomicBool::new(true);

// DashMap provides lock-free concurrent reads for system-specific gates,
// allowing multiple threads to evaluate logging levels simultaneously 
// without contention on the Global Interpreter Lock (GIL).
static LOGGING_MATRIX: Lazy<DashMap<String, bool>> = Lazy::new(DashMap::new);

#[pyfunction]
// Inline comment: Logic for set_master_toggle
fn set_master_toggle(enabled: bool) {
    MASTER_LOG_ENABLED.store(enabled, Ordering::SeqCst);
}

#[pyfunction]
#[pyo3(signature = (system, element=None, enabled=true))]
// Inline comment: Logic for set_gate_state
fn set_gate_state(system: String, element: Option<String>, enabled: bool) {
    let key = match element {
        Some(element_name) => format!("{}:{}", system, element_name),
        None => system,
    };
    LOGGING_MATRIX.insert(key, enabled);
}

#[pyfunction]
#[pyo3(signature = (system, element=None, func_name=None))]
// Inline comment: Logic for is_debug_allowed
fn is_debug_allowed(system: String, element: Option<String>, func_name: Option<String>) -> bool {
    // Master kill-switch evaluation is the fastest path. If the system is 
    // in PRODUCTION mode, all trace/debug logs are dropped here.
    let _ = func_name; // Reserved for future function-level granular gating.
    if !MASTER_LOG_ENABLED.load(Ordering::Relaxed) {
        return false;
    }

    // Element-specific gating allows for "surgical" debugging of a single 
    // widget or fader without flooding the console with other system traffic.
    if let Some(element_name) = &element {
        let key = format!("{}:{}", system, element_name);
        if let Some(enabled) = LOGGING_MATRIX.get(&key) {
            return *enabled;
        }

        // ⚡ FALLBACK: Check element standalone if system-specific key not found.
        // This ensures 'element_smpte2138' works even if partition is 'system'.
        if let Some(enabled) = LOGGING_MATRIX.get(element_name) {
            return *enabled;
        }
    }

    // System-wide fallback ensures that protocol-level logs (e.g., all MIDI)
    // are controlled if no specific element is targeted.
    if let Some(enabled) = LOGGING_MATRIX.get(&system) {
        return *enabled;
    }

    // Default to enabled ensures no logs are lost if a module hasn't 
    // explicitly registered with the gate.
    true
}

#[pymodule]
// Inline comment: Logic for oalogginggate_rs
pub fn oalogginggate_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(is_debug_allowed, m)?)?;
    m.add_function(wrap_pyfunction!(set_gate_state, m)?)?;
    m.add_function(wrap_pyfunction!(set_master_toggle, m)?)?;
    Ok(())
}
