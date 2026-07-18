/**
 * Header: mod.rs
 * Purpose: mod.rs implementation.
 * Description: Logic and implementation for mod.rs implementation.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

use serde::Deserialize;
use std::collections::HashMap;
use std::fs;

#[derive(Deserialize)]
struct DeviceInfo {
    #[serde(rename = "type")]
    device_type: String,
    notes: String,
}

/// The knowledge base compiled into the binary — the guaranteed fallback.
/// The on-disk copy (openair-visa/assets/visa_devices.json) wins when found,
/// so devices can be added without recompiling.
const EMBEDDED_KB: &str = include_str!("../../assets/visa_devices.json");

fn load_kb() -> HashMap<String, DeviceInfo> {
    // On-disk copies, in order: next to cwd (running from the crate dir),
    // then walking UP from cwd to find the repo-layout path — the old
    // cwd-only lookup is why every instrument showed "Unknown Instrument"
    // when the orchestrator ran from the repo root.
    let mut candidates: Vec<std::path::PathBuf> = vec!["assets/visa_devices.json".into()];
    if let Ok(mut dir) = std::env::current_dir() {
        loop {
            candidates.push(dir.join("BackEnd/ComProtocols/openair-visa/assets/visa_devices.json"));
            if !dir.pop() {
                break;
            }
        }
    }
    for path in candidates {
        if let Ok(content) = fs::read_to_string(&path) {
            if let Ok(parsed) = serde_json::from_str::<HashMap<String, DeviceInfo>>(&content) {
                return parsed;
            }
        }
    }
    serde_json::from_str(EMBEDDED_KB).unwrap_or_default()
}

// Inline comment: Logic for get_device_info
pub fn get_device_info(model: &str) -> (String, String) {
    let known_devices = load_kb();
    if let Some(info) = known_devices.get(model) {
        (info.device_type.clone(), info.notes.clone())
    } else {
        ("Unknown Instrument".to_string(), "Not in Knowledge Base".to_string())
    }
}
