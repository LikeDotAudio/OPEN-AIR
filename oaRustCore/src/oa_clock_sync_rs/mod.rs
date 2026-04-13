// oaWatchdog/Methods/oaClockSync_rs/src/lib.rs
// Author: Gemini Iron Oxide Architect
// Version: 20260402.0010.1

use pyo3::prelude::*;
use std::time::{SystemTime, UNIX_EPOCH};

#[pyclass]
struct SystemClock;

#[pymethods]
impl SystemClock {
    #[new]
    fn new() -> Self {
        SystemClock
    }

    /// Returns high-precision Unix timestamp in microseconds.
    fn get_micros(&self) -> u64 {
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_micros() as u64
    }

    /// Returns high-precision Unix timestamp in nanoseconds.
    fn get_nanos(&self) -> u64 {
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_nanos() as u64
    }
}

#[pymodule]
pub fn oaclocksync_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<SystemClock>()?;
    Ok(())
}
