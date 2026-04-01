// oaStateCache/Core/oaDiskFlusher_rs/src/lib.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260401.1200.1

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyBool, PyFloat, PyInt, PyString, PyBytes};
use serde_json::{Value, Map};
use std::path::PathBuf;
use std::io::Write;
use std::thread;

#[pyclass]
struct DiskFlusher {
    last_state: Option<Value>,
}

impl DiskFlusher {
    /// Recursively converts a Python object to a serde_json::Value.
    /// This MUST be called while holding the GIL.
    fn py_to_value(&self, obj: &Bound<'_, PyAny>) -> PyResult<Value> {
        if let Ok(dict) = obj.downcast::<PyDict>() {
            let mut map = Map::new();
            for (key, val) in dict.iter() {
                let k_str = key.to_string();
                let v_val = self.py_to_value(&val)?;
                map.insert(k_str, v_val);
            }
            Ok(Value::Object(map))
        } else if let Ok(list) = obj.downcast::<PyList>() {
            let mut vec = Vec::new();
            for item in list.iter() {
                vec.push(self.py_to_value(&item)?);
            }
            Ok(Value::Array(vec))
        } else if let Ok(s) = obj.downcast::<PyString>() {
            Ok(Value::String(s.to_string()))
        } else if let Ok(b) = obj.downcast::<PyBool>() {
            Ok(Value::Bool(b.is_true()))
        } else if let Ok(i) = obj.downcast::<PyInt>() {
            Ok(Value::Number(serde_json::Number::from(i.extract::<i64>()?)))
        } else if let Ok(f) = obj.downcast::<PyFloat>() {
            if let Some(num) = serde_json::Number::from_f64(f.value()) {
                Ok(Value::Number(num))
            } else {
                Ok(Value::Null)
            }
        } else if let Ok(bytes) = obj.downcast::<PyBytes>() {
            let b_slice = bytes.as_bytes();
            if let Ok(s) = std::str::from_utf8(b_slice) {
                Ok(Value::String(s.to_string()))
            } else {
                Ok(Value::String(hex::encode(b_slice)))
            }
        } else if obj.is_none() {
            Ok(Value::Null)
        } else {
            Ok(Value::String(obj.to_string()))
        }
    }
}

#[pymethods]
impl DiskFlusher {
    #[new]
    fn new() -> Self {
        DiskFlusher {
            last_state: None,
        }
    }

    /// Asynchronously diffs, serializes, and flushes the state to disk.
    fn flush_async(&mut self, _py: Python<'_>, data: Bound<'_, PyDict>, filepath: String) -> PyResult<()> {
        // 1. Convert PyDict to Value (GIL required)
        let new_state = self.py_to_value(&data.as_any())?;

        // 2. Diffing logic
        if let Some(ref last) = self.last_state {
            if last == &new_state {
                return Ok(());
            }
        }

        // 3. Update last state
        self.last_state = Some(new_state.clone());

        // 4. Spawn background thread for I/O
        thread::spawn(move || {
            let path = PathBuf::from(filepath);
            let temp_dir = path.parent().unwrap_or(&path);
            
            let res = (|| -> Result<(), Box<dyn std::error::Error>> {
                let mut temp_f = tempfile::NamedTempFile::new_in(temp_dir)?;
                let json_data = serde_json::to_vec(&new_state)?;
                temp_f.write_all(&json_data)?;
                temp_f.persist(&path)?;
                Ok(())
            })();

            if let Err(e) = res {
                eprintln!("🧠💾❌ [ERROR] Rust DiskFlusher failed: {}", e);
            }
        });

        Ok(())
    }
}

#[pymodule]
fn oadiskflusher_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<DiskFlusher>()?;
    Ok(())
}
