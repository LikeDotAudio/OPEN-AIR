/**
 * Header: mod.rs
 * Purpose: mod.rs implementation.
 * Description: Logic and implementation for mod.rs implementation.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// oaStateCache/Methods/oaStateRegistry_rs/mod.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260413.0010.1
//
// Description: Thread-safe global state cache. Manages the system-wide
// "Single Source of Truth" state tree in Rust using DashMap to allow 
// concurrent updates from multiple protocol bridges (MIDI, OSC, MQTT) 
// without GIL contention.

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use dashmap::DashMap;

#[pyclass]
struct StateRegistryCore {
    // DashMap is employed to ensure that high-frequency updates (e.g., 60Hz 
    // metering or smooth fader movement) can occur on separate protocol 
    // threads without locking the entire state tree.
    cache: DashMap<String, Py<PyAny>>,
}

#[pymethods]
impl StateRegistryCore {
    #[new]
    fn new() -> Self {
        StateRegistryCore {
            cache: DashMap::new(),
        }
    }

    // Standard CRUD operations for the state tree. Each update is atomic
    // at the DashMap level, ensuring data consistency across bridges.
    fn set(&self, topic: String, value: Py<PyAny>) {
        self.cache.insert(topic, value);
    }

    fn update(&self, items: &Bound<'_, PyDict>) -> PyResult<()> {
        for (topic, value) in items.iter() {
            let topic: String = topic.extract()?;
            self.cache.insert(topic, value.unbind());
        }
        Ok(())
    }

    fn get(&self, py: Python<'_>, topic: String) -> Option<Py<PyAny>> {
        self.cache.get(&topic).map(|value_entry| value_entry.value().clone_ref(py))
    }

    fn exists(&self, topic: String) -> bool {
        self.cache.contains_key(&topic)
    }

    fn remove(&self, py: Python<'_>, topic: String) -> Option<Py<PyAny>> {
        self.cache.remove(&topic).map(|(_, value_entry)| value_entry.clone_ref(py))
    }

    fn clear(&self) {
        self.cache.clear();
    }

    fn len(&self) -> usize {
        self.cache.len()
    }

    // should_update implements a high-performance "Delta Engine." It prevents
    // redundant MQTT publications and GUI re-renders by discarding incoming 
    // payloads that match the existing cached state or have older timestamps.
    fn should_update(&self, py: Python<'_>, topic: String, incoming_payload: Py<PyAny>) -> bool {
        let cached = match self.cache.get(&topic) {
            Some(value_entry) => value_entry,
            None => return true, // New topics always trigger an update.
        };

        let incoming = incoming_payload.bind(py);
        let cached_val = cached.value().bind(py);

        // 1. Timestamp Guard: Protects against out-of-order network messages
        // by ensuring only newer data (based on UTP/Epoch) can overwrite state.
        if let (Ok(incoming_timestamp), Ok(cached_timestamp)) = (incoming.get_item("timestamp"), cached_val.get_item("timestamp")) {
            if let (Ok(i_timestamp), Ok(c_timestamp)) = (incoming_timestamp.extract::<f64>(), cached_timestamp.extract::<f64>()) {
                if i_timestamp > c_timestamp { return true; }
                if i_timestamp <= c_timestamp { return false; }
            }
        }

        // 2. Value Guard: Only proceed if the data content has changed.
        // For complex structures, Python's native equality is used via PyO3 to
        // handle nested dictionaries and lists reliably.
        incoming.ne(cached_val).unwrap_or(true)
    }

    fn items<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyList>> {
        let list = PyList::empty_bound(py);
        for entry in self.cache.iter() {
            let pair = (entry.key().clone(), entry.value().bind(py).clone());
            list.append(pair)?;
        }
        Ok(list)
    }

    fn keys<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyList>> {
        let list = PyList::empty_bound(py);
        for entry in self.cache.iter() {
            list.append(entry.key().clone())?;
        }
        Ok(list)
    }

    fn to_dict<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let dict = PyDict::new_bound(py);
        for entry in self.cache.iter() {
            dict.set_item(entry.key(), entry.value().bind(py).clone())?;
        }
        Ok(dict)
    }
}

#[pymodule]
// Inline comment: Logic for oastateregistry_rs
pub fn oastateregistry_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<StateRegistryCore>()?;
    Ok(())
}
