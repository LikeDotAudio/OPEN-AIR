// oaTranslator/Core/oaTaskPool_rs/src/lib.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260331.2350.2

use pyo3::prelude::*;
use rayon::ThreadPoolBuilder;
use rayon::prelude::*;
use std::sync::{Arc, Mutex};

#[pyclass]
struct TaskPool {
    pool: rayon::ThreadPool,
}

#[pymethods]
impl TaskPool {
    #[new]
    fn new(num_threads: usize) -> Self {
        let pool = ThreadPoolBuilder::new()
            .num_threads(num_threads)
            .build()
            .unwrap();
        TaskPool { pool }
    }

    fn spawn(&self, callback: PyObject) {
        self.pool.spawn(move || {
            Python::with_gil(|py| {
                if let Err(e) = callback.call0(py) {
                    e.print(py);
                }
            });
        });
    }

    fn par_map(&self, _py: Python<'_>, data: Vec<PyObject>, callback: PyObject) -> Vec<PyObject> {
        self.pool.install(|| {
            data.into_par_iter()
                .map(|item| {
                    Python::with_gil(|py| {
                        callback.call1(py, (item,)).unwrap_or_else(|e| {
                            e.print(py);
                            py.None()
                        })
                    })
                })
                .collect()
        })
    }
}

#[pymodule]
fn oataskpool_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<TaskPool>()?;
    Ok(())
}
