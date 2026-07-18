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

// Inline comment: Logic for get_device_info
pub fn get_device_info(model: &str) -> (String, String) {
    let mut known_devices: HashMap<String, DeviceInfo> = HashMap::new();
    
    // Try to load from the working directory first, then fallback to a specific path
    let paths = [
        "assets/visa_devices.json",
        "../assets/visa_devices.json",
        "/usr/local/share/openair/assets/visa_devices.json"
    ];
    
    for path in paths.iter() {
        if let Ok(content) = fs::read_to_string(path) {
            if let Ok(parsed) = serde_json::from_str::<HashMap<String, DeviceInfo>>(&content) {
                known_devices = parsed;
                break;
            }
        }
    }
    
    if let Some(info) = known_devices.get(model) {
        (info.device_type.clone(), info.notes.clone())
    } else {
        ("Unknown Instrument".to_string(), "Not in Knowledge Base".to_string())
    }
}
