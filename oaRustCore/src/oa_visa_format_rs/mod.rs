// oaComVisa/Methods/oaVisaFormat_rs/mod.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260413.1400.1
//
// Description: VISA data formatter. Converts raw instrument 
// responses into standardized engineering units and JSON structures.

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
        PyBytes::new_bound(py, formatted.as_bytes()).into_any().unbind()
    }

    fn format_bool(&self, py: Python<'_>, cmd: String, value: bool) -> Py<PyAny> {
        let val_str = if value { "1" } else { "0" };
        let formatted = format!("{} {}\n", cmd, val_str);
        PyBytes::new_bound(py, formatted.as_bytes()).into_any().unbind()
    }
}

#[pymodule]
pub fn oavisaformat_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<VisaFormatter>()?;
    Ok(())
}
