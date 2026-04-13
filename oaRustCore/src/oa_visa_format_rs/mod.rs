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

    fn format_command(&self, py: Python<'_>, cmd: String, value: f64) -> Py<PyAny> {
        // SCPI commands usually end with a newline \n
        let formatted = format!("{} {:e}\n", cmd, value);
        PyBytes::new(py, formatted.as_bytes()).into()
    }

    fn format_bool(&self, py: Python<'_>, cmd: String, value: bool) -> Py<PyAny> {
        let val_str = if value { "1" } else { "0" };
        let formatted = format!("{} {}\n", cmd, val_str);
        PyBytes::new(py, formatted.as_bytes()).into()
    }
}

#[pyfunction]
fn sum_as_string(a: usize, b: usize) -> PyResult<String> {
    Ok((a + b).to_string())
}

#[pymodule]
pub fn oavisaformat_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<VisaFormatter>()?;
    m.add_function(wrap_pyfunction!(sum_as_string, m)?)?;
    Ok(())
}
