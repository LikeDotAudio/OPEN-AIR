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

    fn items(&self, py: Python<'_>) -> PyResult<Py<PyList>> {
        let list = PyList::empty(py);
        for entry in self.cache.iter() {
            let pair = (entry.key().clone(), entry.value().clone_ref(py));
            list.append(pair.into_py_any(py)?)?;
        }
        Ok(list.unbind())
    }

    fn keys(&self, py: Python<'_>) -> PyResult<Py<PyList>> {
        let list = PyList::empty(py);
        for entry in self.cache.iter() {
            list.append(entry.key().clone().into_py_any(py)?)?;
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

#[pymodule]
fn oastateregistry_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<StateRegistryCore>()?;
    Ok(())
}
