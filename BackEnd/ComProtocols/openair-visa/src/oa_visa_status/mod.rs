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
use crate::oa_visa_pyvisa_wrapper::execute_query;

#[pyfunction]
// Inline comment: Logic for oa_visa_status
pub fn oa_visa_status(py: Python<'_>, resource_name: &str) -> PyResult<String> {
    execute_query(py, resource_name, "*STB?")
}
