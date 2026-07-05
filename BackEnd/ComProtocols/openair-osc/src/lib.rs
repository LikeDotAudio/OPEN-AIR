/**
 * Header: lib.rs
 * Purpose: lib.rs implementation.
 * Description: Logic and implementation for lib.rs implementation.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

use rosc::{OscPacket, OscType};
use tokio::net::UdpSocket;
use tokio::sync::mpsc;
use serde_json::{json, Value};
use std::sync::Arc;

/// A simple structure to represent our unified internal state format
#[derive(Debug, Clone)]
pub struct OscEvent {
    pub address: String,
    pub value: Value,
}

pub struct OscAgent {
    pub host: String,
    pub port: u16,
}

impl OscAgent {
    pub fn new(host: String, port: u16) -> Self {
        Self { host, port }
    }

    /// Starts the OSC UDP Listener as a Tokio task
    /// It sends incoming unified JSON events to the provided MPSC Sender.
    pub async fn start(&self, tx: mpsc::Sender<OscEvent>) -> std::io::Result<()> {
        let addr = format!("{}:{}", self.host, self.port);
        let socket = UdpSocket::bind(&addr).await?;
        let socket = Arc::new(socket);

        println!("📡 [OSC AGENT] Listening on {}", addr);

        let socket_clone = socket.clone();
        tokio::spawn(async move {
            let mut buf = vec![0u8; 65535];
            loop {
                match socket_clone.recv_from(&mut buf).await {
                    Ok((size, _peer)) => {
                        if let Ok((_, packet)) = rosc::decoder::decode_udp(&buf[..size]) {
                            handle_packet(packet, &tx).await;
                        }
                    }
                    Err(e) => {
                        eprintln!("📡⚙️❌ [OSC AGENT] Socket receive error: {:?}", e);
                    }
                }
            }
        });

        Ok(())
    }
}

use std::pin::Pin;
use std::future::Future;

// Inline comment: Logic for handle_packet
fn handle_packet<'a>(
    packet: OscPacket,
    tx: &'a mpsc::Sender<OscEvent>,
) -> Pin<Box<dyn Future<Output = ()> + Send + 'a>> {
    Box::pin(async move {
        match packet {
            OscPacket::Message(message) => {
                if let Some(json_val) = convert_osc_args(message.args) {
                    let event = OscEvent {
                        address: message.addr,
                        value: json_val,
                    };
                    let _ = tx.send(event).await;
                }
            }
            OscPacket::Bundle(bundle) => {
                for sub_packet in bundle.content {
                    handle_packet(sub_packet, tx).await;
                }
            }
        }
    })
}

// Inline comment: Logic for convert_osc_args
fn convert_osc_args(args: Vec<OscType>) -> Option<Value> {
    if args.is_empty() {
        return None;
    }
    
    // If it's a single value, unwrap it from the array
    if args.len() == 1 {
        return Some(osc_type_to_json(&args[0]));
    }

    // Otherwise return a JSON array
    let json_array: Vec<Value> = args.iter().map(osc_type_to_json).collect();
    Some(json!(json_array))
}

// Inline comment: Logic for osc_type_to_json
fn osc_type_to_json(arg: &OscType) -> Value {
    match arg {
        OscType::Int(i) => json!(i),
        OscType::Float(f) => json!(f),
        OscType::String(s) => json!(s),
        OscType::Blob(_) => json!("[BLOB]"),
        OscType::Time(t) => json!({ "seconds": t.seconds, "fraction": t.fractional }),
        OscType::Long(l) => json!(l),
        OscType::Double(d) => json!(d),
        OscType::Char(c) => json!(c.to_string()),
        OscType::Color(c) => json!({ "r": c.red, "g": c.green, "b": c.blue, "a": c.alpha }),
        OscType::Midi(m) => json!({ "port": m.port, "status": m.status, "data1": m.data1, "data2": m.data2 }),
        OscType::Bool(b) => json!(b),
        OscType::Array(arr) => {
            let json_arr: Vec<Value> = arr.content.iter().map(osc_type_to_json).collect();
            json!(json_arr)
        }
        OscType::Nil => Value::Null,
        OscType::Inf => json!("INFINITY"),
    }
}

#[cfg(feature = "python")]
pub mod oa_osc_core_rs;
