/**
 * Header: mod.rs
 * Purpose: mod.rs implementation.
 * Description: Logic and implementation for mod.rs implementation.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// oaTranslator/Core/oaTranslatorCore_rs/mod.rs
// Author: Gemini Architect
// Version: 20260413.1400.1
//
// Description: The central translation and protocol bridge core. 
// Manages the conversion of disparate protocol messages (MQTT, OSC, MIDI) 
// into unified system state updates.

use pyo3::prelude::*;
use pyo3::types::PyDict;
use serde_json::Value;
use pythonize::{depythonize_bound, pythonize};
use std::collections::HashMap;
use dashmap::DashMap;
use std::sync::{Arc, Mutex};

#[pyclass]
struct SplinkerLock {
    locked: Arc<Mutex<bool>>,
}

#[pymethods]
impl SplinkerLock {
    #[new]
    fn new() -> Self {
        SplinkerLock { locked: Arc::new(Mutex::new(false)) }
    }

    fn acquire(&self) -> bool {
        let mut l = self.locked.lock().unwrap();
        if *l { return false; }
        *l = true;
        true
    }

    fn release(&self) {
        let mut l = self.locked.lock().unwrap();
        *l = false;
    }

    fn __enter__(&self) {
        // Simple blocking acquire for context manager
        loop {
            let mut l = self.locked.lock().unwrap();
            if !*l {
                *l = true;
                break;
            }
            drop(l);
            std::thread::yield_now();
        }
    }

    fn __exit__(&self, _ty: Py<PyAny>, _value: Py<PyAny>, _traceback: Py<PyAny>) {
        self.release();
    }
}

#[pyclass]
struct SettleLock {
    locked: Arc<Mutex<bool>>,
}

#[pymethods]
impl SettleLock {
    #[new]
    fn new() -> Self {
        SettleLock { locked: Arc::new(Mutex::new(false)) }
    }

    fn acquire(&self) -> bool {
        let mut l = self.locked.lock().unwrap();
        if *l { return false; }
        *l = true;
        true
    }

    fn release(&self) {
        let mut l = self.locked.lock().unwrap();
        *l = false;
    }

    fn __enter__(&self) {
        loop {
            let mut l = self.locked.lock().unwrap();
            if !*l {
                *l = true;
                break;
            }
            drop(l);
            std::thread::yield_now();
        }
    }

    fn __exit__(&self, _ty: Py<PyAny>, _value: Py<PyAny>, _traceback: Py<PyAny>) {
        self.release();
    }
}

#[pyclass]
struct WidgetRegistry {
    widgets: DashMap<String, Py<PyDict>>,
    topic_map: DashMap<String, String>,
}

#[pymethods]
impl WidgetRegistry {
    #[new]
    fn new() -> Self {
        WidgetRegistry {
            widgets: DashMap::new(),
            topic_map: DashMap::new(),
        }
    }

    fn register(&self, widget_id: String, info: Py<PyDict>, py: Python<'_>) -> PyResult<()> {
        let topic: String = info.bind(py).get_item("topic")?
            .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyKeyError, _>("topic missing in info"))?
            .extract()?;
        self.widgets.insert(widget_id.clone(), info);
        self.topic_map.insert(topic, widget_id);
        Ok(())
    }

    fn is_registered(&self, widget_id: String) -> bool {
        self.widgets.contains_key(&widget_id)
    }

    fn get_topic(&self, widget_id: String) -> Option<String> {
        self.widgets.get(&widget_id).and_then(|info| {
            Python::with_gil(|py| {
                info.bind(py).get_item("topic").ok().flatten().and_then(|v| v.extract().ok())
            })
        })
    }

    fn get_info(&self, py: Python<'_>, widget_id: String) -> Option<Py<PyDict>> {
        self.widgets.get(&widget_id).map(|v| v.clone_ref(py))
    }

    fn get_widget_id_by_topic(&self, topic: String) -> Option<String> {
        self.topic_map.get(&topic).map(|v| v.clone())
    }

    fn all_widgets<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let result = PyDict::new_bound(py);
        for entry in self.widgets.iter() {
            result.set_item(entry.key(), entry.value().bind(py).clone())?;
        }
        Ok(result)
    }

    fn all_topics<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let result = PyDict::new_bound(py);
        for entry in self.topic_map.iter() {
            result.set_item(entry.key(), entry.value().clone())?;
        }
        Ok(result)
    }
}

// Inline comment: Logic for internal_diff_values
fn internal_diff_values(path: &str, old: &Value, new: &Value, diffs: &mut HashMap<String, Value>) {
    match (old, new) {
        (Value::Object(old_obj), Value::Object(new_obj)) => {
            for (key, new_v) in new_obj {
                let new_path = if path.is_empty() { key.clone() } else { format!("{}/{}", path, key) };
                if let Some(old_v) = old_obj.get(key) {
                    internal_diff_values(&new_path, old_v, new_v, diffs);
                } else {
                    diffs.insert(new_path, new_v.clone());
                }
            }
        }
        (old_v, new_v) if old_v != new_v => {
            diffs.insert(path.to_string(), new_v.clone());
        }
        _ => {}
    }
}

#[pyclass]
struct JSONDiffer;

#[pymethods]
impl JSONDiffer {
    #[new]
    fn new() -> Self {
        JSONDiffer
    }

    /// Compares two dictionaries and returns a dictionary of differences.
    fn compare<'py>(&self, py: Python<'py>, old: &Bound<'py, PyDict>, new: &Bound<'py, PyDict>) -> PyResult<Bound<'py, PyDict>> {
        let old_val: Value = depythonize_bound(old.clone().into_any()).map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
        let new_val: Value = depythonize_bound(new.clone().into_any()).map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
        
        let mut diffs = HashMap::new();
        internal_diff_values("", &old_val, &new_val, &mut diffs);
        
        let result = PyDict::new_bound(py);
        for (key, value) in diffs {
            result.set_item(key, pythonize(py, &value).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?)?;
        }
        Ok(result)
    }
}

#[pymodule]
// Inline comment: Logic for oatranslatorcore_rs
pub fn oatranslatorcore_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<SplinkerLock>()?;
    m.add_class::<SettleLock>()?;
    m.add_class::<WidgetRegistry>()?;
    m.add_class::<JSONDiffer>()?;
    Ok(())
}
