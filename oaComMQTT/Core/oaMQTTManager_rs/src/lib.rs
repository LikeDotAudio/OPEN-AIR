// oaComMQTT/Core/oaMQTTManager_rs/src/lib.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260331.2350.1

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use std::collections::HashMap;
use dashmap::DashMap;
use std::sync::Arc;

#[pyclass]
struct MqttRouter {
    // Exact matches: topic -> list of callbacks
    exact_matches: Arc<DashMap<String, Vec<PyObject>>>,
    // Wildcard matches: filter -> (regex, list of callbacks)
    wildcard_matches: Arc<DashMap<String, (String, Vec<PyObject>)>>,
}

#[pymethods]
impl MqttRouter {
    #[new]
    fn new() -> Self {
        MqttRouter {
            exact_matches: Arc::new(DashMap::new()),
            wildcard_matches: Arc::new(DashMap::new()),
        }
    }

    fn subscribe(&self, filter: String, callback: PyObject) {
        if filter.contains('+') || filter.contains('#') {
            let mut entry = self.wildcard_matches.entry(filter.clone()).or_insert_with(|| {
                (mqtt_filter_to_regex(&filter), Vec::new())
            });
            entry.1.push(callback);
        } else {
            let mut entry = self.exact_matches.entry(filter).or_insert_with(Vec::new);
            entry.push(callback);
        }
    }

    fn unsubscribe(&self, filter: String) {
        self.exact_matches.remove(&filter);
        self.wildcard_matches.remove(&filter);
    }

    fn match_topic(&self, topic: String) -> Vec<PyObject> {
        let mut matches = Vec::new();

        // 1. Exact match
        if let Some(callbacks) = self.exact_matches.get(&topic) {
            matches.extend(callbacks.clone());
        }

        // 2. Wildcard matches (Iterate and check regex)
        // In a high-performance Trie impl, this would be faster.
        for r in self.wildcard_matches.iter() {
            let (regex_str, callbacks) = r.value();
            // Simple match for now. Real MQTT matching is more complex.
            if matches_mqtt(regex_str, &topic) {
                matches.extend(callbacks.clone());
            }
        }

        matches
    }

    fn clear(&self) {
        self.exact_matches.clear();
        self.wildcard_matches.clear();
    }
}

fn mqtt_filter_to_regex(filter: &str) -> String {
    let mut regex = filter.replace(".", "\\.");
    regex = regex.replace("+", "[^/]+");
    regex = regex.replace("#", ".*");
    format!("^{}$", regex)
}

fn matches_mqtt(regex_str: &str, topic: &str) -> bool {
    // Simple regex matching for POC.
    // Real implementation should use a specialized MQTT Trie.
    if let Ok(re) = regex::Regex::new(regex_str) {
        re.is_match(topic)
    } else {
        false
    }
}

#[pymodule]
fn oamqttmanager_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<MqttRouter>()?;
    Ok(())
}
