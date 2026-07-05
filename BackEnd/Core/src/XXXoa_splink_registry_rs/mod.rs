/**
 * Header: mod.rs
 * Purpose: mod.rs implementation.
 * Description: Logic and implementation for mod.rs implementation.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// oaSplinker/Core/oaSplinkRegistry_rs/mod.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260413.1400.1
//
// Description: Thread-safe SPLINK registration store. Manages 
// active cross-fades and parameter links using DashMap for 
// concurrent protocol access.

use pyo3::prelude::*;
use pyo3::types::PyDict;
use dashmap::DashMap;
use std::sync::Arc;
use std::time::{SystemTime, UNIX_EPOCH};

#[pyclass]
struct SplinkRegistry {
    // topic -> list of splinks
    registry: Arc<DashMap<String, Vec<Py<PyAny>>>>,
    // splink_id -> is_currently_processing (Atomic lock replacement)
    processing_state: Arc<DashMap<String, bool>>,
    // (timestamp_ms, topic, splink_id) -> seen
    event_cache: Arc<DashMap<(u64, String, String), bool>>,
    // splink_id -> list of recent timestamps
    event_counters: Arc<DashMap<String, Vec<f64>>>,
}

#[pymethods]
impl SplinkRegistry {
    #[new]
    fn new() -> Self {
        SplinkRegistry {
            registry: Arc::new(DashMap::new()),
            processing_state: Arc::new(DashMap::new()),
            event_cache: Arc::new(DashMap::new()),
            event_counters: Arc::new(DashMap::new()),
        }
    }

    fn add_splink(&self, topic: String, splink: Py<PyAny>) {
        let mut entry = self.registry.entry(topic).or_insert_with(Vec::new);
        entry.push(splink);
    }

    fn get_splinks_for_topic(&self, py: Python<'_>, topic: String) -> Vec<Py<PyAny>> {
        self.registry.get(&topic)
            .map(|v| v.iter().map(|s| s.clone_ref(py)).collect())
            .unwrap_or_default()
    }

    fn all_splinks(&self, py: Python<'_>) -> Vec<Py<PyAny>> {
        let mut all = Vec::new();
        for r in self.registry.iter() {
            all.extend(r.value().iter().map(|s| s.clone_ref(py)));
        }
        all
    }

    fn get_splink_by_id(&self, py: Python<'_>, splink_id: String) -> Option<Py<PyAny>> {
        for r in self.registry.iter() {
            for s in r.value() {
                if let Ok(dict) = s.downcast_bound::<PyDict>(py) {
                    if let Ok(Some(id)) = dict.get_item("id") {
                        if let Ok(id_str) = id.extract::<String>() {
                            if id_str == splink_id {
                                return Some(s.clone_ref(py));
                            }
                        }
                    }
                }
            }
        }
        None
    }

    fn update_splink(&self, py: Python<'_>, splink_id: String, new_data: Py<PyAny>) {
        let mut target_topic = None;
        for r in self.registry.iter() {
            for s in r.value() {
                if let Ok(dict) = s.downcast_bound::<PyDict>(py) {
                    if let Ok(Some(id)) = dict.get_item("id") {
                        if let Ok(id_str) = id.extract::<String>() {
                            if id_str == splink_id {
                                target_topic = Some(r.key().clone());
                                break;
                            }
                        }
                    }
                }
            }
            if target_topic.is_some() { break; }
        }

        if let Some(topic) = target_topic {
            if let Some(mut entry) = self.registry.get_mut(&topic) {
                for s in entry.iter_mut() {
                    let found = if let Ok(dict) = s.downcast_bound::<PyDict>(py) {
                        if let Ok(Some(id)) = dict.get_item("id") {
                            if let Ok(id_str) = id.extract::<String>() {
                                id_str == splink_id
                            } else { false }
                        } else { false }
                    } else { false };

                    if found {
                        *s = new_data.clone_ref(py);
                        break;
                    }
                }
            }
        }
    }

    fn delete_splink(&self, py: Python<'_>, splink_id: String) {
        let mut target_topic = None;
        for r in self.registry.iter() {
            for s in r.value() {
                let found = if let Ok(dict) = s.downcast_bound::<PyDict>(py) {
                    if let Ok(Some(id)) = dict.get_item("id") {
                        if let Ok(id_str) = id.extract::<String>() {
                            id_str == splink_id
                        } else { false }
                    } else { false }
                } else { false };

                if found {
                    target_topic = Some(r.key().clone());
                    break;
                }
            }
            if target_topic.is_some() { break; }
        }

        if let Some(topic) = target_topic {
            if let Some(mut entry) = self.registry.get_mut(&topic) {
                entry.retain(|s| {
                    if let Ok(dict) = s.downcast_bound::<PyDict>(py) {
                        if let Ok(Some(id)) = dict.get_item("id") {
                            if let Ok(id_str) = id.extract::<String>() {
                                return id_str != splink_id;
                            }
                        }
                    }
                    true
                });
            }
        }
    }

    fn try_acquire_execution_lock(&self, splink_id: String) -> bool {
        let mut state = self.processing_state.entry(splink_id).or_insert(false);
        if *state {
            false
        } else {
            *state = true;
            true
        }
    }

    fn release_execution_lock(&self, splink_id: String) {
        self.processing_state.insert(splink_id, false);
    }

    fn mark_event_processed(&self, ts_ms: u64, topic: String, splink_id: String) -> bool {
        let key = (ts_ms, topic, splink_id);
        if self.event_cache.contains_key(&key) {
            true
        } else {
            self.event_cache.insert(key, true);
            if self.event_cache.len() > 10000 {
                self.event_cache.clear();
            }
            false
        }
    }

    fn check_panic_threshold(&self, splink_id: String, threshold: usize) -> bool {
        let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs_f64();
        let mut entry = self.event_counters.entry(splink_id).or_insert_with(Vec::new);
        
        entry.push(now);
        entry.retain(|&t| now - t < 1.0);
        
        entry.len() > threshold
    }

    fn clear(&self) {
        self.registry.clear();
        self.processing_state.clear();
        self.event_cache.clear();
        self.event_counters.clear();
    }

    fn len(&self) -> usize {
        self.registry.len()
    }

    fn topics(&self) -> Vec<String> {
        self.registry.iter().map(|r| r.key().clone()).collect()
    }
}

#[pymodule]
// Inline comment: Logic for oasplinkregistry_rs
pub fn oasplinkregistry_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<SplinkRegistry>()?;
    Ok(())
}
