/**
 * Header: mod.rs
 * Purpose: mod.rs implementation.
 * Description: Logic and implementation for mod.rs implementation.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

use midir::{MidiInput, MidiInputConnection};

// Inline comment: Logic for listen_to_port
pub fn listen_to_port(port_name: &str) -> Option<MidiInputConnection<()>> {
    let mut midi_in = MidiInput::new("OPEN-AIR Listener").ok()?;
    midi_in.ignore(midir::Ignore::None);
    
    let ports = midi_in.ports();
    let port = ports.iter().find(|p| midi_in.port_name(p).unwrap_or_default().contains(port_name))?;
    
    midi_in.connect(port, "OPEN-AIR-Input-Connection", move |stamp, message, _| {
        // Just print for the tester for now
        if !message.is_empty() {
            println!("🎹 [MIDI EVENT] time: {}, data: {:?}", stamp, message);
        }
    }, ()).ok()
}
