// oaComBroker/Methods/oaCoreRouter-rs/src/lib.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260402.0015.1

use pyo3::prelude::*;
use crossbeam_channel::{unbounded, Receiver, Sender};

#[pyclass]
struct CoreRouter {
    inbound_tx: Sender<PyObject>,
    inbound_rx: Receiver<PyObject>,
    outbound_tx: Sender<PyObject>,
    outbound_rx: Receiver<PyObject>,
}

#[pymethods]
impl CoreRouter {
    #[new]
    fn new() -> Self {
        let (in_tx, in_rx) = unbounded();
        let (out_tx, out_rx) = unbounded();
        CoreRouter {
            inbound_tx: in_tx,
            inbound_rx: in_rx,
            outbound_tx: out_tx,
            outbound_rx: out_rx,
        }
    }

    fn push_inbound(&self, msg: PyObject) {
        let _ = self.inbound_tx.send(msg);
    }

    fn pop_inbound(&self, _py: Python<'_>) -> Option<PyObject> {
        self.inbound_rx.try_recv().ok()
    }

    fn push_outbound(&self, msg: PyObject) {
        let _ = self.outbound_tx.send(msg);
    }

    fn pop_outbound(&self, _py: Python<'_>) -> Option<PyObject> {
        self.outbound_rx.try_recv().ok()
    }

    fn inbound_len(&self) -> usize {
        self.inbound_rx.len()
    }

    fn outbound_len(&self) -> usize {
        self.outbound_rx.len()
    }
}

#[pyfunction]
fn sum_as_string(a: usize, b: usize) -> PyResult<String> {
    Ok((a + b).to_string())
}

#[pymodule]
fn oacorerouter_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<CoreRouter>()?;
    m.add_function(wrap_pyfunction!(sum_as_string, m)?)?;
    Ok(())
}
