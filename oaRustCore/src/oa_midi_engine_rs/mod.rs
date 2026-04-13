// oaComMidi/Methods/oaMidiEngine-rs/src/lib.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260403.2300.1

use pyo3::prelude::*;
use pyo3::types::{PyList, PyDict, PyBytes};
use midir::{MidiInput, MidiOutput, MidiInputConnection, MidiOutputConnection};
use crossbeam_channel::{unbounded, Receiver};
use std::sync::Mutex;

#[pyclass]
struct MidiEngine {
    input_conn: Mutex<Option<MidiInputConnection<()>>>,
    output_conn: Mutex<Option<MidiOutputConnection>>,
    receiver: Mutex<Receiver<MidiEvent>>,
}

struct MidiEvent {
    timestamp: u64,
    data: Vec<u8>,
}

#[pymethods]
impl MidiEngine {
    #[new]
    fn new() -> Self {
        let (_, rx) = unbounded();
        MidiEngine {
            input_conn: Mutex::new(None),
            output_conn: Mutex::new(None),
            receiver: Mutex::new(rx),
        }
    }

    fn list_inputs(&self) -> PyResult<Vec<String>> {
        let midi_in = MidiInput::new("OPEN-AIR MIDI Input List").map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        let ports = midi_in.ports();
        let names: Vec<String> = ports.iter().map(|p| midi_in.port_name(p).unwrap_or_default()).collect();
        Ok(names)
    }

    fn list_outputs(&self) -> PyResult<Vec<String>> {
        let midi_out = MidiOutput::new("OPEN-AIR MIDI Output List").map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        let ports = midi_out.ports();
        let names: Vec<String> = ports.iter().map(|p| midi_out.port_name(p).unwrap_or_default()).collect();
        Ok(names)
    }

    fn open_input(&self, port_index: usize) -> PyResult<()> {
        let midi_in = MidiInput::new("OPEN-AIR MIDI Input").map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        let ports = midi_in.ports();
        if port_index >= ports.len() {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>("Port index out of range"));
        }
        
        let (tx, rx) = unbounded();
        {
            let mut receiver_lock = self.receiver.lock().unwrap();
            *receiver_lock = rx;
        }
        
        let port = &ports[port_index];
        let conn = midi_in.connect(port, "OPEN-AIR-Input-Connection", move |ts, data, _| {
            let _ = tx.send(MidiEvent { timestamp: ts, data: data.to_vec() });
        }, ()).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        
        let mut conn_lock = self.input_conn.lock().unwrap();
        *conn_lock = Some(conn);
        Ok(())
    }

    fn get_buffered_events<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyList>> {
        let list = PyList::empty(py);
        let receiver = self.receiver.lock().unwrap();
        while let Ok(event) = receiver.try_recv() {
            let dict = PyDict::new(py);
            dict.set_item("timestamp", event.timestamp)?;
            dict.set_item("data", PyBytes::new(py, &event.data))?;
            list.append(dict)?;
        }
        Ok(list)
    }

    fn close(&self) {
        let mut in_lock = self.input_conn.lock().unwrap();
        *in_lock = None;
        let mut out_lock = self.output_conn.lock().unwrap();
        *out_lock = None;
    }
}

#[pymodule]
pub fn oamidiengine_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<MidiEngine>()?;
    Ok(())
}
