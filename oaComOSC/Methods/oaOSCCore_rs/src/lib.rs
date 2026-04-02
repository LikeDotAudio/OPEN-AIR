// oaComOSC/Methods/oaOSCCore_rs/src/lib.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260401.1500.3

use pyo3::prelude::*;
use pyo3::types::PyDict;
use rosc::{OscPacket, OscType};
use std::net::UdpSocket;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::thread;

#[pyclass]
struct OscServer {
    running: Arc<AtomicBool>,
    handle: Option<thread::JoinHandle<()>>,
}

#[pymethods]
impl OscServer {
    #[new]
    fn new() -> Self {
        OscServer {
            running: Arc::new(AtomicBool::new(false)),
            handle: None,
        }
    }

    fn start(&mut self, host: String, port: u16, callback: PyObject) -> PyResult<()> {
        if self.running.load(Ordering::SeqCst) {
            return Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("Server already running"));
        }

        let addr = format!("{}:{}", host, port);
        let socket = UdpSocket::bind(&addr).map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyIOError, _>(format!("Failed to bind to {}: {}", addr, e))
        })?;

        // Set read timeout so we can check the running flag
        socket.set_read_timeout(Some(std::time::Duration::from_millis(500))).map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyIOError, _>(format!("Failed to set socket timeout: {}", e))
        })?;

        let running = self.running.clone();
        running.store(true, Ordering::SeqCst);

        let handle = thread::spawn(move || {
            let mut buf = [0u8; 65535];
            while running.load(Ordering::SeqCst) {
                match socket.recv_from(&mut buf) {
                    Ok((size, _addr)) => {
                        let packet = rosc::decoder::decode_udp(&buf[..size]);
                        match packet {
                            Ok((_, packet)) => {
                                handle_packet(packet, &callback);
                            }
                            Err(e) => {
                                eprintln!("📡⚙️❌ [OSC-RS] Decode error: {:?}", e);
                            }
                        }
                    }
                    Err(e) if e.kind() == std::io::ErrorKind::WouldBlock => {
                        // Timeout reached, loop and check running flag
                    }
                    Err(e) => {
                        eprintln!("📡⚙️❌ [OSC-RS] Socket error: {:?}", e);
                        break;
                    }
                }
            }
            running.store(false, Ordering::SeqCst);
        });

        self.handle = Some(handle);
        Ok(())
    }

    fn stop(&mut self) -> PyResult<()> {
        self.running.store(false, Ordering::SeqCst);
        if let Some(handle) = self.handle.take() {
            let _ = handle.join();
        }
        Ok(())
    }

    fn is_running(&self) -> bool {
        self.running.load(Ordering::SeqCst)
    }
}

fn handle_packet(packet: OscPacket, callback: &PyObject) {
    match packet {
        OscPacket::Message(msg) => {
            dispatch_message(msg.addr, msg.args, callback);
        }
        OscPacket::Bundle(bundle) => {
            for packet in bundle.content {
                handle_packet(packet, callback);
            }
        }
    }
}

fn dispatch_message(addr: String, args: Vec<OscType>, callback: &PyObject) {
    Python::with_gil(|py| {
        let py_args = pyo3::types::PyList::empty_bound(py);
        for arg in args {
            match arg {
                OscType::Int(i) => { let _ = py_args.append(i); }
                OscType::Float(f) => { let _ = py_args.append(f); }
                OscType::String(s) => { let _ = py_args.append(s); }
                OscType::Blob(b) => { let _ = py_args.append(pyo3::types::PyBytes::new_bound(py, &b)); }
                OscType::Long(l) => { let _ = py_args.append(l); }
                OscType::Double(d) => { let _ = py_args.append(d); }
                OscType::Char(c) => { let _ = py_args.append(c.to_string()); }
                OscType::Color(c) => {
                    let dict = PyDict::new_bound(py);
                    let _ = dict.set_item("r", c.red);
                    let _ = dict.set_item("g", c.green);
                    let _ = dict.set_item("b", c.blue);
                    let _ = dict.set_item("a", c.alpha);
                    let _ = py_args.append(dict);
                }
                OscType::Midi(m) => {
                    let dict = PyDict::new_bound(py);
                    let _ = dict.set_item("port", m.port);
                    let _ = dict.set_item("status", m.status);
                    let _ = dict.set_item("data1", m.data1);
                    let _ = dict.set_item("data2", m.data2);
                    let _ = py_args.append(dict);
                }
                OscType::Bool(b) => { let _ = py_args.append(b); }
                OscType::Nil => { let _ = py_args.append(py.None()); }
                OscType::Inf => { let _ = py_args.append("INFINITY"); }
                OscType::Time(t) => {
                    let dict = PyDict::new_bound(py);
                    let _ = dict.set_item("seconds", t.seconds);
                    let _ = dict.set_item("fraction", t.fractional);
                    let _ = py_args.append(dict);
                }
                _ => { let _ = py_args.append("UNKNOWN_TYPE"); }
            }
        }
        
        let _ = callback.call1(py, (addr, py_args));
    });
}

#[pymodule]
fn oaosccore_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<OscServer>()?;
    Ok(())
}
