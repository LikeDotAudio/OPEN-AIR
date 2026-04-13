// oaStateCache/Methods/oaStateRegistry-rs/src/lib.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260331.1840.1

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use dashmap::DashMap;
use pyo3::IntoPyObjectExt;

#[pyclass]
struct StateRegistryCore {
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
        self.cache.get(&topic).map(|v| v.value().clone_ref(py))
    }

    fn exists(&self, topic: String) -> bool {
        self.cache.contains_key(&topic)
    }

    fn remove(&self, py: Python<'_>, topic: String) -> Option<Py<PyAny>> {
        self.cache.remove(&topic).map(|(_, v)| v.clone_ref(py))
    }

    fn clear(&self) {
        self.cache.clear();
    }

    fn len(&self) -> usize {
        self.cache.len()
    }

    fn should_update(&self, py: Python<'_>, topic: String, incoming_payload: Py<PyAny>) -> bool {
        let cached = match self.cache.get(&topic) {
            Some(v) => v,
            None => return true, // Not in cache
        };

        // Comparison logic matching state_comparator.py
        let incoming = incoming_payload.bind(py);
        let cached_val = cached.value().bind(py);

        // 1. Timestamp comparison
        if let (Ok(incoming_ts), Ok(cached_ts)) = (incoming.get_item("ts"), cached_val.get_item("ts")) {
            if let (Ok(i_ts), Ok(c_ts)) = (incoming_ts.extract::<f64>(), cached_ts.extract::<f64>()) {
                if i_ts > c_ts { return true; }
                if i_ts <= c_ts { return false; }
            }
        }

        // 2. Full content comparison
        // We use Python's equality check here, but it's executed within the Rust extension.
        // For deep comparison of massive objects, we could use serde_json diffing.
        incoming.ne(cached_val).unwrap_or(true)
    }

    fn items(&self, py: Python<'_>) -> PyResult<Py<PyList>> {
        let list = PyList::empty(py);
        for entry in self.cache.iter() {
            let pair = (entry.key().clone(), entry.value().clone_ref(py));
            list.append(pair.into_bound_py_any(py)?)?;
        }
        Ok(list.unbind())
    }

    fn keys(&self, py: Python<'_>) -> PyResult<Py<PyList>> {
        let list = PyList::empty(py);
        for entry in self.cache.iter() {
            list.append(entry.key().clone().into_bound_py_any(py)?)?;
        }
        Ok(list.unbind())
    }

    fn to_dict(&self, py: Python<'_>) -> PyResult<Py<PyDict>> {
        let dict = PyDict::new(py);
        for entry in self.cache.iter() {
            dict.set_item(entry.key(), entry.value().clone_ref(py))?;
        }
        Ok(dict.unbind())
    }
}

#[pyfunction]
fn sum_as_string(a: usize, b: usize) -> PyResult<String> {
    Ok((a + b).to_string())
}

#[pymodule]
fn oastateregistry_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<StateRegistryCore>()?;
    m.add_function(wrap_pyfunction!(sum_as_string, m)?)?;
    Ok(())
}
