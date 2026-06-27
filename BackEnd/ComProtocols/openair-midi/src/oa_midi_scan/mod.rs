use midir::{MidiInput, MidiOutput};

pub fn scan_inputs() -> Vec<String> {
    if let Ok(midi_in) = MidiInput::new("OPEN-AIR Scanner Input") {
        midi_in.ports().iter().filter_map(|p| midi_in.port_name(p).ok()).collect()
    } else {
        vec![]
    }
}

pub fn scan_outputs() -> Vec<String> {
    if let Ok(midi_out) = MidiOutput::new("OPEN-AIR Scanner Output") {
        midi_out.ports().iter().filter_map(|p| midi_out.port_name(p).ok()).collect()
    } else {
        vec![]
    }
}
