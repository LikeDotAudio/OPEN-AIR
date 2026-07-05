/**
 * Header: mod.rs
 * Purpose: mod.rs implementation.
 * Description: Logic and implementation for mod.rs implementation.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// oaComMidi/Methods/oaMidiEngine_rs/mod.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260413.1400.1
//
// Description: Low-latency MIDI I/O engine. Utilizes `midir` for 
// platform-agnostic device management and provides an asynchronous 
// event bridge to the central Python orchestrator.

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
        
        let (transmitter, receiver) = unbounded();
        {
            let mut receiver_lock = self.receiver.lock().unwrap();
            *receiver_lock = receiver;
        }
        
        let port = &ports[port_index];
        let conn = midi_in.connect(port, "OPEN-AIR-Input-Connection", move |timestamp, data, _| {
            let _ = transmitter.send(MidiEvent { timestamp: timestamp, data: data.to_vec() });
        }, ()).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        
        let mut conn_lock = self.input_conn.lock().unwrap();
        *conn_lock = Some(conn);
        Ok(())
    }

    fn get_buffered_events<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyList>> {
        let list = PyList::empty_bound(py);
        let receiver = self.receiver.lock().unwrap();
        while let Ok(event) = receiver.try_recv() {
            let dict = PyDict::new_bound(py);
            dict.set_item("timestamp", event.timestamp)?;
            dict.set_item("data", PyBytes::new_bound(py, &event.data))?;
            list.append(dict)?;
        }
        Ok(list)
    }

    fn publish_devices_mqtt(&self, broker_ip: &str, port: u16, base_topic: &str) -> PyResult<()> {
        let inputs = crate::oa_midi_scan::scan_inputs();
        let outputs = crate::oa_midi_scan::scan_outputs();
        crate::oa_midi_mqtt_publish::publish_devices_mqtt(broker_ip, port, base_topic, inputs, outputs)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e))
    }

    fn close(&self) {
        let mut in_lock = self.input_conn.lock().unwrap();
        *in_lock = None;
        let mut out_lock = self.output_conn.lock().unwrap();
        *out_lock = None;
    }
}

#[pymodule]
// Inline comment: Logic for oamidiengine_rs
pub fn oamidiengine_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<MidiEngine>()?;
    Ok(())
}
