/**
 * Header: mod.rs
 * Purpose: mod.rs implementation.
 * Description: Logic and implementation for mod.rs implementation.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// oaComSNMP/Methods/oaSNMPAgent_rs/mod.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260413.1400.1
//
// Description: Native SNMP agent responder. Manages OID trees 
// and MIB responses in Rust to ensure consistent performance 
// regardless of Python GIL load.

use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::collections::BTreeMap;
use std::sync::{Arc, Mutex};

#[pyclass]
struct SnmpAgent {
    tree: Arc<Mutex<BTreeMap<Vec<u32>, String>>>,
}

#[pymethods]
impl SnmpAgent {
    #[new]
    fn new() -> Self {
        SnmpAgent {
            tree: Arc::new(Mutex::new(BTreeMap::new())),
        }
    }

    fn update_oid(&self, oid: String, value: String) {
        let mut tree = self.tree.lock().unwrap();
        let parsed_oid = parse_oid(&oid);
        tree.insert(parsed_oid, value);
    }

    fn get_oid(&self, oid: String) -> Option<String> {
        let tree = self.tree.lock().unwrap();
        let parsed_oid = parse_oid(&oid);
        tree.get(&parsed_oid).cloned()
    }

    fn get_next(&self, py: Python<'_>, oid: String) -> Option<Py<PyAny>> {
        let tree = self.tree.lock().unwrap();
        let parsed_oid = parse_oid(&oid);
        
        // Find the first OID strictly greater than the target
        for (o, v) in tree.range(parsed_oid.clone()..) {
            if o > &parsed_oid {
                let dict = PyDict::new_bound(py);
                let _ = dict.set_item("oid", format_oid(o));
                let _ = dict.set_item("value", v);
                return Some(dict.into_any().unbind());
            }
        }
        None
    }

    fn clear(&self) {
        let mut tree = self.tree.lock().unwrap();
        tree.clear();
    }
}

// Inline comment: Logic for parse_oid
fn parse_oid(oid: &str) -> Vec<u32> {
    oid.trim_matches('.')
        .split('.')
        .filter_map(|s| s.parse::<u32>().ok())
        .collect()
}

// Inline comment: Logic for format_oid
fn format_oid(oid: &[u32]) -> String {
    let parts: Vec<String> = oid.iter().map(|n| n.to_string()).collect();
    format!(".{}", parts.join("."))
}

#[pymodule]
// Inline comment: Logic for oasnmpagent_rs
pub fn oasnmpagent_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<SnmpAgent>()?;
    Ok(())
}
