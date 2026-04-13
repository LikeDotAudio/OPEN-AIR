// oaComBroker/Methods/oaCoreRouter_rs/src/lib.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260402.0015.2

use pyo3::prelude::*;
use crossbeam_channel::{unbounded, Receiver, Sender};

#[pyclass]
struct CoreRouter {
    inbound_tx: Sender<Py<PyAny>>,
    inbound_rx: Receiver<Py<PyAny>>,
    outbound_tx: Sender<Py<PyAny>>,
    outbound_rx: Receiver<Py<PyAny>>,
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

    fn push_inbound(&self, msg: Py<PyAny>) {
        let _ = self.inbound_tx.send(msg);
    }

    fn pop_inbound(&self, py: Python<'_>) -> Option<Py<PyAny>> {
        self.inbound_rx.try_recv().ok().map(|msg| msg.clone_ref(py))
    }

    fn push_outbound(&self, msg: Py<PyAny>) {
        let _ = self.outbound_tx.send(msg);
    }

    fn pop_outbound(&self, py: Python<'_>) -> Option<Py<PyAny>> {
        self.outbound_rx.try_recv().ok().map(|msg| msg.clone_ref(py))
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
