/**
 * Header: mod.rs
 * Purpose: mod.rs implementation.
 * Description: Logic and implementation for mod.rs implementation.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

use pyo3::prelude::*;
use crate::oa_visa_pyvisa_wrapper::execute_write;

#[pyfunction]
// Inline comment: Logic for oa_visa_reset
pub fn oa_visa_reset(py: Python<'_>, resource_name: &str) -> PyResult<()> {
    execute_write(py, resource_name, "*RST")
}
