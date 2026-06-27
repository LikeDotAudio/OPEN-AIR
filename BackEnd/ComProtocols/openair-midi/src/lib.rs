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
    // Hold onto the input connections to keep them alive
    _conn_in: Arc<Mutex<Vec<MidiInputConnection<()>>>>,
    // Hold onto the output connections so we can send messages
    pub conn_out: Arc<Mutex<Vec<midir::MidiOutputConnection>>>,
}

impl MidiAgent {
    pub fn new(target_port_name: Option<String>) -> Self {
        Self {
            target_port_name,
            _conn_in: Arc::new(Mutex::new(Vec::new())),
            conn_out: Arc::new(Mutex::new(Vec::new())),
        }
    }

    pub async fn start(&self, tx: mpsc::Sender<MidiEvent>) -> Result<(), Box<dyn Error + Send + Sync>> {
        let midi_in_list = MidiInput::new("OPEN-AIR MIDI Input List")
            .map_err(|e| -> Box<dyn Error + Send + Sync> { e.to_string().into() })?;
        
        let ports = midi_in_list.ports();
        if ports.is_empty() {
            println!("🎹❌ [MIDI AGENT] No MIDI input ports available.");
            return Ok(());
        }

        let mut connections = Vec::new();

        for (i, p) in ports.iter().enumerate() {
            if let Some(name) = &self.target_port_name {
                if let Ok(port_name) = midi_in_list.port_name(p) {
                    if !port_name.contains(name) {
                        continue;
                    }
                }
            }

            let mut midi_in = MidiInput::new(&format!("OPEN-AIR MIDI Input {}", i))
                .map_err(|e| -> Box<dyn Error + Send + Sync> { e.to_string().into() })?;
            midi_in.ignore(Ignore::None);

            let mi_ports = midi_in.ports();
            if i < mi_ports.len() {
                let port = &mi_ports[i];
                let port_name = midi_in.port_name(port).unwrap_or_else(|_| "Unknown".to_string());
                println!("🎹 [MIDI AGENT] Connecting to port {}: {}", i, port_name);

                let tx_clone = tx.clone();
                let conn_in = midi_in.connect(
                    port,
                    &format!("OPEN-AIR-Input-Connection-{}", i),
                    move |stamp, message, _| {
                        if message.is_empty() { return; }

                        let status = message[0];
                        let channel = status & 0x0F;
                        let command = status & 0xF0;

                        let value = json!({
                            "timestamp": stamp,
                            "status": status,
                            "channel": channel,
                            "command": command,
                            "data1": message.get(1).copied().unwrap_or(0),
                            "data2": message.get(2).copied().unwrap_or(0),
                            "raw": message,
                            "port_index": i,
                        });

                        let event = MidiEvent {
                            address: format!("Dev{}/Channel/{}/Command/{}", i, channel, command),
                            value,
                        };

                        let _ = tx_clone.try_send(event);
                    },
                    (),
                ).map_err(|e| -> Box<dyn Error + Send + Sync> { e.to_string().into() })?;

                connections.push(conn_in);
            }
        }

        let mut conn_lock = self._conn_in.lock().unwrap();
        *conn_lock = connections;

        // Output Connections
        let midi_out_list = midir::MidiOutput::new("OPEN-AIR MIDI Output List")
            .map_err(|e| -> Box<dyn Error + Send + Sync> { e.to_string().into() })?;
            
        let out_ports = midi_out_list.ports();
        let mut out_connections = Vec::new();
        
        for (i, p) in out_ports.iter().enumerate() {
            if let Some(name) = &self.target_port_name {
                if let Ok(port_name) = midi_out_list.port_name(p) {
                    if !port_name.contains(name) {
                        continue;
                    }
                }
            }

            let midi_out = midir::MidiOutput::new(&format!("OPEN-AIR MIDI Output {}", i))
                .map_err(|e| -> Box<dyn Error + Send + Sync> { e.to_string().into() })?;
                
            let mo_ports = midi_out.ports();
            if i < mo_ports.len() {
                let port = &mo_ports[i];
                let conn_out = midi_out.connect(port, &format!("OPEN-AIR-Output-Connection-{}", i))
                    .map_err(|e| -> Box<dyn Error + Send + Sync> { e.to_string().into() })?;
                out_connections.push(conn_out);
            }
        }
        
        let mut out_lock = self.conn_out.lock().unwrap();
        *out_lock = out_connections;

        Ok(())
    }

    pub fn send(&self, port_index: usize, data: &[u8]) -> Result<(), Box<dyn Error + Send + Sync>> {
        let mut out_lock = self.conn_out.lock().unwrap();
        if port_index < out_lock.len() {
            out_lock[port_index].send(data).map_err(|e| -> Box<dyn Error + Send + Sync> { e.to_string().into() })?;
        }
        Ok(())
    }
}

#[cfg(feature = "python")]
pub mod oa_midi_engine_rs;

#[cfg(feature = "python")]
pub mod oa_midi_mapper_rs;

pub mod oa_midi_scan;
pub mod oa_midi_listen;
pub mod oa_midi_mqtt_publish;
pub mod oa_midi_mqtt_listen;
