// oaComBroker/Methods/oaCoreRouter_rs/mod.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260413.0010.1
//
// Description: High-performance asynchronous message router. Utilizes Rust's 
// lock-free crossbeam channels to manage inbound and outbound traffic between
// Python protocol managers and the central MQTT bus without blocking the GIL.

use pyo3::prelude::*;
use crossbeam_channel::{unbounded, Receiver, Sender};

#[pyclass]
struct CoreRouter {
    // Unbounded channels are used to prevent backpressure from stalling the 
    // protocol managers. The memory overhead is acceptable as the Python-side
    // supervisor (openair.py) monitors queue lengths for system health.
    inbound_transmitter: Sender<Py<PyAny>>,
    inbound_receiver: Receiver<Py<PyAny>>,
    outbound_transmitter: Sender<Py<PyAny>>,
    outbound_receiver: Receiver<Py<PyAny>>,
}

#[pymethods]
impl CoreRouter {
    #[new]
    fn new() -> Self {
        let (inbound_transmitter, inbound_receiver) = unbounded();
        let (outbound_transmitter, outbound_receiver) = unbounded();
        CoreRouter {
            inbound_transmitter,
            inbound_receiver,
            outbound_transmitter,
            outbound_receiver,
        }
    }

    // Inbound traffic (Protocol -> Global Bus)
    fn push_inbound(&self, message: Py<PyAny>) {
        // Send is non-blocking on unbounded channels. Failure to send implies
        // a catastrophic channel closure, handled at the supervisor level.
        let _ = self.inbound_transmitter.send(message);
    }

    fn pop_inbound(&self, py: Python<'_>) -> Option<Py<PyAny>> {
        // try_recv ensures we don't hang the calling thread if no messages are pending.
        self.inbound_receiver.try_recv().ok().map(|message| message.clone_ref(py))
    }

    // Outbound traffic (Global Bus -> Protocol)
    fn push_outbound(&self, message: Py<PyAny>) {
        let _ = self.outbound_transmitter.send(message);
    }

    fn pop_outbound(&self, py: Python<'_>) -> Option<Py<PyAny>> {
        self.outbound_receiver.try_recv().ok().map(|message| message.clone_ref(py))
    }

    // Queue monitoring for performance metrics (PPS/BPS) and watchdog safety checks.
    fn inbound_len(&self) -> usize {
        self.inbound_receiver.len()
    }

    fn outbound_len(&self) -> usize {
        self.outbound_receiver.len()
    }
}

#[pymodule]
pub fn oacorerouter_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<CoreRouter>()?;
    Ok(())
}
