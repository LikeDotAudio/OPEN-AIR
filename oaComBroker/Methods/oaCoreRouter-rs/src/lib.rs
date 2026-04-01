// oaComBroker/Methods/oaCoreRouter-rs/src/lib.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260331.1900.1

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use crossbeam_channel::{unbounded, Receiver, Sender};
use std::sync::Arc;
use pyo3::IntoPyObjectExt;

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

    fn pop_inbound(&self, py: Python<'_>) -> Option<PyObject> {
        // Non-blocking pop for simplicity in this bridge phase
        self.inbound_rx.try_recv().ok()
    }

    fn push_outbound(&self, msg: PyObject) {
        let _ = self.outbound_tx.send(msg);
    }

    fn pop_outbound(&self, py: Python<'_>) -> Option<PyObject> {
        self.outbound_rx.try_recv().ok()
    }

    fn inbound_len(&self) -> usize {
        self.inbound_rx.len()
    }

    fn outbound_len(&self) -> usize {
        self.outbound_rx.len()
    }
}

#[pymodule]
fn oacorerouter_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<CoreRouter>()?;
    Ok(())
}
