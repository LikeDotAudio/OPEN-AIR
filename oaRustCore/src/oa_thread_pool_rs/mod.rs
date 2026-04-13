// oaThreadManager/Methods/oaThreadPool_rs/src/lib.rs
// Author: Gemini Iron Oxide Architect
// Version: 20260402.0010.1

use pyo3::prelude::*;
use pyo3::types::PyList;
use rayon::prelude::*;

#[pyclass]
struct NativeThreadPool;

#[pymethods]
impl NativeThreadPool {
    #[new]
    fn new() -> Self {
        NativeThreadPool
    }

    /// Example of parallel numeric processing bypassing the GIL.
    fn parallel_sum(&self, data: Vec<f64>) -> f64 {
        data.par_iter().sum()
    }

    /// Performs a parallel operation on a list of floats and returns results.
    fn parallel_multiply(&self, data: Vec<f64>, factor: f64) -> Vec<f64> {
        data.par_iter().map(|&x| x * factor).collect()
    }
}

#[pymodule]
pub fn oathreadpool_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<NativeThreadPool>()?;
    Ok(())
}
