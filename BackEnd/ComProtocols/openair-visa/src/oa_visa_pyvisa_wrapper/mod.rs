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
use pyo3::types::PyDict;

// Inline comment: Logic for execute_write
pub fn execute_write(py: Python<'_>, resource_name: &str, command: &str) -> PyResult<()> {
    let pyvisa = py.import_bound("pyvisa")?;
    let rm = pyvisa.getattr("ResourceManager")?.call1(("@py",)).or_else(|_| pyvisa.getattr("ResourceManager")?.call0())?;
    
    let kwargs = PyDict::new_bound(py);
    kwargs.set_item("open_timeout", 1500)?;
    
    let inst = rm.call_method("open_resource", (resource_name,), Some(&kwargs))?;
    inst.setattr("timeout", 1500)?;
    inst.call_method1("write", (command,))?;
    inst.call_method0("close")?;
    Ok(())
}

// Inline comment: Logic for execute_query
pub fn execute_query(py: Python<'_>, resource_name: &str, command: &str) -> PyResult<String> {
    let pyvisa = py.import_bound("pyvisa")?;
    let rm = pyvisa.getattr("ResourceManager")?.call1(("@py",)).or_else(|_| pyvisa.getattr("ResourceManager")?.call0())?;
    
    let kwargs = PyDict::new_bound(py);
    kwargs.set_item("open_timeout", 1500)?;
    
    let inst = rm.call_method("open_resource", (resource_name,), Some(&kwargs))?;
    inst.setattr("timeout", 1500)?;
    inst.setattr("read_termination", "\n")?;
    inst.setattr("write_termination", "\n")?;
    
    let res: String = inst.call_method1("query", (command,))?.extract()?;
    inst.call_method0("close")?;
    Ok(res)
}

// Inline comment: Logic for execute_status_and_error
pub fn execute_status_and_error(py: Python<'_>, resource_name: &str) -> PyResult<(String, String)> {
    let pyvisa = py.import_bound("pyvisa")?;
    let rm = pyvisa.getattr("ResourceManager")?.call1(("@py",)).or_else(|_| pyvisa.getattr("ResourceManager")?.call0())?;
    
    let kwargs = PyDict::new_bound(py);
    kwargs.set_item("open_timeout", 1500)?;
    
    let inst = rm.call_method("open_resource", (resource_name,), Some(&kwargs))?;
    inst.setattr("timeout", 1500)?;
    inst.setattr("read_termination", "\n")?;
    inst.setattr("write_termination", "\n")?;
    
    let status = inst.call_method1("query", ("*STB?",))
        .and_then(|res| res.extract::<String>())
        .unwrap_or_else(|_| "Unknown".to_string());
        
    let error = inst.call_method1("query", (":SYST:ERR?",))
        .and_then(|res| res.extract::<String>())
        .unwrap_or_else(|_| "Unknown".to_string());
        
    inst.call_method0("close")?;
    Ok((status, error))
}
