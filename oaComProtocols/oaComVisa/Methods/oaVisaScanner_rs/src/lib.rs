// oaComVisa/Methods/oaVisaScanner_rs/src/lib.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260401.1600.1

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use tokio::net::TcpStream;
use tokio::time::{timeout, Duration};
use futures::future::join_all;

#[pyclass]
struct VisaScanner;

#[pymethods]
impl VisaScanner {
    #[new]
    fn new() -> Self {
        VisaScanner
    }

    /// Concurrently checks a list of TCP targets for reachability.
    /// targets: List of tuples (ip, port)
    /// timeout_ms: Timeout in milliseconds for each connection attempt
    fn check_reachability<'py>(&self, py: Python<'py>, targets: Vec<(String, u16)>, timeout_ms: u64) -> PyResult<Bound<'py, PyList>> {
        let rt = tokio::runtime::Runtime::new().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to create tokio runtime: {}", e))
        })?;

        let results = rt.block_on(async {
            let futures = targets.into_iter().map(|(ip, port)| {
                async move {
                    let addr = format!("{}:{}", ip, port);
                    match timeout(Duration::from_millis(timeout_ms), TcpStream::connect(&addr)).await {
                        Ok(Ok(_)) => Some((ip, port, true)),
                        _ => Some((ip, port, false)),
                    }
                }
            });
            join_all(futures).await
        });

        let py_results = PyList::empty(py);
        for res in results {
            if let Some((ip, port, reachable)) = res {
                let dict = PyDict::new(py);
                let _ = dict.set_item("ip", ip);
                let _ = dict.set_item("port", port);
                let _ = dict.set_item("reachable", reachable);
                let _ = py_results.append(dict);
            }
        }

        Ok(py_results)
    }
}

#[pymodule]
fn oavisascanner_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<VisaScanner>()?;
    Ok(())
}
