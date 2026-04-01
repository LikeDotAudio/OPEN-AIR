// oaComVisa/Methods/oaVisaFormat-rs/src/lib.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260331.2020.1

use pyo3::prelude::*;
use pyo3::types::PyBytes;

#[pyclass]
struct VisaFormatter;

#[pymethods]
impl VisaFormatter {
    #[new]
    fn new() -> Self {
        VisaFormatter
    }

    fn format_command(&self, py: Python<'_>, cmd: String, value: f64) -> PyObject {
        // SCPI commands usually end with a newline \n
        let formatted = format!("{} {:e}\n", cmd, value);
        PyBytes::new_bound(py, formatted.as_bytes()).into()
    }

    fn format_bool(&self, py: Python<'_>, cmd: String, value: bool) -> PyObject {
        let val_str = if value { "1" } else { "0" };
        let formatted = format!("{} {}\n", cmd, val_str);
        PyBytes::new_bound(py, formatted.as_bytes()).into()
    }
}

#[pymodule]
fn oavisaformat_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<VisaFormatter>()?;
    Ok(())
}
