/**
 * Header: mod.rs
 * Purpose: mod.rs implementation.
 * Description: Logic and implementation for mod.rs implementation.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

use std::fs;

// Inline comment: Logic for discover_local_devices
pub fn discover_local_devices() -> Vec<String> {
    let mut resources = Vec::new();
    // List serial ports naively
    if let Ok(entries) = fs::read_dir("/dev") {
        for entry in entries.flatten() {
            let name = entry.file_name().to_string_lossy().into_owned();
            if name.starts_with("ttyUSB") || name.starts_with("ttyACM") {
                resources.push(format!("ASRL/dev/{}::INSTR", name));
            }
        }
    }
    resources
}
