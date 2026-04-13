// oaComMQTT/Core/oaMQTTManager_rs/src/lib.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260331.2350.2

use pyo3::prelude::*;
use dashmap::DashMap;
use std::sync::Arc;

#[pyclass]
struct MqttRouter {
    // Exact matches: topic -> list of callbacks
    exact_matches: Arc<DashMap<String, Vec<Py<PyAny>>>>,
    // Wildcard matches: filter -> (regex, list of callbacks)
    wildcard_matches: Arc<DashMap<String, (String, Vec<Py<PyAny>>)>>,
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

    fn subscribe(&self, filter: String, callback: Py<PyAny>) {
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

    fn match_topic(&self, py: Python<'_>, topic: String) -> Vec<Py<PyAny>> {
        let mut matches = Vec::new();

        // 1. Exact match
        if let Some(callbacks) = self.exact_matches.get(&topic) {
            for cb in callbacks.iter() {
                matches.push(cb.clone_ref(py));
            }
        }

        // 2. Wildcard matches (Iterate and check regex)
        for r in self.wildcard_matches.iter() {
            let (regex_str, callbacks) = r.value();
            if matches_mqtt(regex_str, &topic) {
                for cb in callbacks.iter() {
                    matches.push(cb.clone_ref(py));
                }
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
    if let Ok(re) = regex::Regex::new(regex_str) {
        re.is_match(topic)
    } else {
        false
    }
}

#[pymodule]
pub fn oamqttmanager_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<MqttRouter>()?;
    Ok(())
}
