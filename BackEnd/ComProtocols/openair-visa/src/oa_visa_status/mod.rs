use pyo3::prelude::*;
use crate::oa_visa_pyvisa_wrapper::execute_query;

#[pyfunction]
pub fn oa_visa_status(py: Python<'_>, resource_name: &str) -> PyResult<String> {
    execute_query(py, resource_name, "*STB?")
}
