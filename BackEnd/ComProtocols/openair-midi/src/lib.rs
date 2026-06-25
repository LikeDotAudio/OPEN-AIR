use midir::{MidiInput, MidiInputConnection, Ignore};
use serde_json::{json, Value};
use tokio::sync::mpsc;
use std::sync::{Arc, Mutex};
use std::error::Error;

/// The unified internal state format for MIDI events
#[derive(Debug, Clone)]
pub struct MidiEvent {
    pub address: String,
    pub value: Value,
}

pub struct MidiAgent {
    pub target_port_name: Option<String>,
    // Hold onto the connection to keep it alive
    _conn: Arc<Mutex<Option<MidiInputConnection<()>>>>,
}

impl MidiAgent {
    pub fn new(target_port_name: Option<String>) -> Self {
        Self {
            target_port_name,
            _conn: Arc::new(Mutex::new(None)),
        }
    }

    /// Starts the MIDI Listener as a background task.
    /// It sends incoming unified JSON events to the provided MPSC Sender.
    pub async fn start(&self, tx: mpsc::Sender<MidiEvent>) -> Result<(), Box<dyn Error + Send + Sync>> {
        let mut midi_in = MidiInput::new("OPEN-AIR MIDI Input")
            .map_err(|e| -> Box<dyn Error + Send + Sync> { e.to_string().into() })?;
        midi_in.ignore(Ignore::None);
        
        let ports = midi_in.ports();
        if ports.is_empty() {
            println!("🎹❌ [MIDI AGENT] No MIDI input ports available.");
            return Ok(());
        }

        // Auto-select the port based on name, or just use the first one available
        let port = match &self.target_port_name {
            Some(name) => {
                let mut found = None;
                for p in &ports {
                    if let Ok(port_name) = midi_in.port_name(p) {
                        if port_name.contains(name) {
                            found = Some(p.clone());
                            break;
                        }
                    }
                }
                found.unwrap_or_else(|| ports[0].clone())
            }
            None => ports[0].clone(),
        };

        let port_name = midi_in.port_name(&port)
            .map_err(|e| -> Box<dyn Error + Send + Sync> { e.to_string().into() })?;
        println!("🎹 [MIDI AGENT] Connecting to port: {}", port_name);

        let tx_clone = tx.clone();
        
        // The `midir` connect call runs its own dedicated OS thread internally.
        // We capture the events and bridge them back into the Tokio async world using `mpsc::Sender`
        let conn_in = midi_in.connect(
            &port,
            "OPEN-AIR-Input-Connection",
            move |stamp, message, _| {
                // message is usually [status, data1, data2]
                if message.is_empty() { return; }

                let status = message[0];
                let channel = status & 0x0F;
                let command = status & 0xF0;

                // Create a generic JSON representation of the MIDI event
                let value = json!({
                    "timestamp": stamp,
                    "status": status,
                    "channel": channel,
                    "command": command,
                    "data1": message.get(1).copied().unwrap_or(0),
                    "data2": message.get(2).copied().unwrap_or(0),
                    "raw": message,
                });

                let event = MidiEvent {
                    address: format!("Channel/{}/Command/{}", channel, command),
                    value,
                };

                // Because we're in a sync callback, we use `try_send` 
                // to push the event into the async tokio mpsc channel.
                let _ = tx_clone.try_send(event);
            },
            (),
        ).map_err(|e| -> Box<dyn Error + Send + Sync> {
            e.to_string().into()
        })?;

        // Store the connection so it is not dropped and closed.
        let mut conn_lock = self._conn.lock().unwrap();
        *conn_lock = Some(conn_in);

        Ok(())
    }
}

#[cfg(feature = "python")]
pub mod oa_midi_engine_rs;

#[cfg(feature = "python")]
pub mod oa_midi_mapper_rs;
