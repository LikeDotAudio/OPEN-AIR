/**
 * Header: mod.rs
 * Purpose: mod.rs implementation.
 * Description: Logic and implementation for mod.rs implementation.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

use midir::{MidiInput, MidiOutput};

// Inline comment: Logic for scan_inputs
pub fn scan_inputs() -> Vec<String> {
    if let Ok(midi_in) = MidiInput::new("OPEN-AIR Scanner Input") {
        midi_in.ports().iter().filter_map(|p| midi_in.port_name(p).ok()).collect()
    } else {
        vec![]
    }
}

// Inline comment: Logic for scan_outputs
pub fn scan_outputs() -> Vec<String> {
    if let Ok(midi_out) = MidiOutput::new("OPEN-AIR Scanner Output") {
        midi_out.ports().iter().filter_map(|p| midi_out.port_name(p).ok()).collect()
    } else {
        vec![]
    }
}
