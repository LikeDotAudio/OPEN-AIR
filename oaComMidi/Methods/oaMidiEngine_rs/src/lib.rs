// oaComMidi/Methods/oaMidiEngine-rs/src/lib.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260331.1720.1

use pyo3::prelude::*;
use pyo3::types::{PyList, PyDict, PyBytes};
use midir::{MidiInput, MidiOutput, MidiInputConnection, MidiOutputConnection};
use crossbeam_channel::{unbounded, Receiver, Sender};
use std::sync::{Arc, Mutex};

#[pyclass]
struct MidiEngine {
    input_conn: Option<MidiInputConnection<()>>,
    output_conn: Option<MidiOutputConnection>,
    receiver: Receiver<MidiEvent>,
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
            input_conn: None,
            output_conn: None,
            receiver: rx,
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

    fn open_input(&mut self, port_index: usize) -> PyResult<()> {
        let midi_in = MidiInput::new("OPEN-AIR MIDI Input").map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        let ports = midi_in.ports();
        if port_index >= ports.len() {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>("Port index out of range"));
        }
        
        let (tx, rx) = unbounded();
        self.receiver = rx;
        
        let port = &ports[port_index];
        let conn = midi_in.connect(port, "OPEN-AIR-Input-Connection", move |ts, data, _| {
            let _ = tx.send(MidiEvent { timestamp: ts, data: data.to_vec() });
        }, ()).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        
        self.input_conn = Some(conn);
        Ok(())
    }

    fn get_buffered_events<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyList>> {
        let list = PyList::empty_bound(py);
        while let Ok(event) = self.receiver.try_recv() {
            let dict = PyDict::new_bound(py);
            dict.set_item("timestamp", event.timestamp)?;
            dict.set_item("data", PyBytes::new_bound(py, &event.data))?;
            list.append(dict)?;
        }
        Ok(list)
    }

    fn close(&mut self) {
        self.input_conn = None;
        self.output_conn = None;
    }
}

#[pymodule]
fn oamidiengine_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<MidiEngine>()?;
    Ok(())
}
