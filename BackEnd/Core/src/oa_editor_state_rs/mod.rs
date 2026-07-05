/**
 * Header: mod.rs
 * Purpose: mod.rs implementation.
 * Description: Logic and implementation for mod.rs implementation.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// oaGuiEditorWYSIWYG/Core/oaEditorState_rs/mod.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260413.1400.1
//
// Description: State manager for the WYSIWYG editor. Manages 
// local UI state and interactive element properties in Rust.

use pyo3::prelude::*;
use pyo3::types::PyString;
use parking_lot::RwLock;
use std::sync::Arc;
use serde_json::Value;

#[pyclass]
struct EditorState {
    data: Arc<RwLock<Value>>,
}

#[pymethods]
impl EditorState {
    #[new]
    fn new() -> Self {
        EditorState {
            data: Arc::new(RwLock::new(serde_json::json!({}))),
        }
    }

    /// Initializes the state with a JSON string to avoid PyO3 object translation overhead
    fn initialize(&self, json_str: String) -> PyResult<()> {
        let parsed: Value = serde_json::from_str(&json_str).unwrap_or_else(|_| serde_json::json!({}));
        let mut data = self.data.write();
        *data = parsed;
        Ok(())
    }

    /// Returns the entire state as a JSON string
    fn get_state(&self) -> PyResult<String> {
        let data = self.data.read();
        Ok(serde_json::to_string(&*data).unwrap_or_else(|_| "{}".to_string()))
    }

    /// Updates a specific path in the state tree
    fn update_state(&self, path: Vec<String>, new_json_str: String) -> PyResult<()> {
        let new_val: Value = serde_json::from_str(&new_json_str).unwrap_or_else(|_| serde_json::json!(null));
        let mut data = self.data.write();

        if path.is_empty() {
            *data = new_val;
            return Ok(());
        }

        let mut current = &mut *data;
        
        for (i, key) in path.iter().enumerate() {
            if i == path.len() - 1 {
                // We are at the end, insert or replace
                if let Some(obj) = current.as_object_mut() {
                    obj.insert(key.clone(), new_val.clone());
                } else {
                    // Not an object, we need to convert it to one
                    *current = serde_json::json!({});
                    current.as_object_mut().unwrap().insert(key.clone(), new_val.clone());
                }
            } else {
                // Navigate deeper, creating objects if necessary
                if !current.is_object() {
                    *current = serde_json::json!({});
                }
                
                let obj = current.as_object_mut().unwrap();
                if !obj.contains_key(key) {
                    obj.insert(key.clone(), serde_json::json!({}));
                }
                
                // Rust borrow checker requires this dance
                current = current.get_mut(key).unwrap();
            }
        }

        Ok(())
    }

    fn reset(&self) {
        let mut data = self.data.write();
        *data = serde_json::json!({});
    }
}

#[pymodule]
// Inline comment: Logic for oaeditorstate_rs
pub fn oaeditorstate_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<EditorState>()?;
    Ok(())
}
