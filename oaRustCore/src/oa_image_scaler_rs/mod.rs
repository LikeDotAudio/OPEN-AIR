use pyo3::prelude::*;

#[pyfunction]
fn hello() -> PyResult<String> {
    Ok("Hello from oaImageScaler-rs!".to_string())
}

#[pymodule]
fn oaImageScaler_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(hello, m)?)?;
    Ok(())
}
