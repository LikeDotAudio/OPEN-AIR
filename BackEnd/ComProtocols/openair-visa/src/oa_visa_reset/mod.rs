use pyo3::prelude::*;
use crate::oa_visa_pyvisa_wrapper::execute_write;

#[pyfunction]
pub fn oa_visa_reset(py: Python<'_>, resource_name: &str) -> PyResult<()> {
    execute_write(py, resource_name, "*RST")
}
