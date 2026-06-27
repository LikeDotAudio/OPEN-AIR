use midir::{MidiInput, MidiInputConnection};

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
