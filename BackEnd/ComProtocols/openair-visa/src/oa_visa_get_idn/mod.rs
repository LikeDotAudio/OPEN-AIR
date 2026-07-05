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
use crate::oa_visa_known_devices;
use crate::oa_visa_pyvisa_wrapper::execute_query;

// Inline comment: Logic for identify_device
pub fn identify_device(py: Python<'_>, resource_name: &str) -> PyResult<PyObject> {
    let idn = execute_query(py, resource_name, "*IDN?").unwrap_or_else(|_| "".to_string());
    
    let idn = idn.trim().to_string();
    let parts: Vec<&str> = idn.split(',').map(|s| s.trim()).collect();
    let manufacturer = parts.get(0).unwrap_or(&"Unknown").to_string();
    let model = parts.get(1).unwrap_or(&"Unknown").to_string();
    let serial = parts.get(2).unwrap_or(&"").to_string();
    let firmware = parts.get(3).unwrap_or(&"").to_string();

    let (device_type, notes) = oa_visa_known_devices::get_device_info(&model);

    let dict = pyo3::types::PyDict::new_bound(py);
    dict.set_item("manufacturer", manufacturer)?;
    dict.set_item("model", model)?;
    dict.set_item("serial", serial)?;
    dict.set_item("firmware", firmware)?;
    dict.set_item("device_type", &device_type)?;
    dict.set_item("notes", &notes)?;
    dict.set_item("raw_idn", idn)?;
    dict.set_item("resource", resource_name)?;

    Ok(dict.into())
}
