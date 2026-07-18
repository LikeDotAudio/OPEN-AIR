/**
 * Header: main.rs
 * Purpose: main.rs implementation.
 * Description: Logic and implementation for main.rs implementation.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

mod api;
mod cli;
mod mqtt;

use axum::{
    extract::ws::{Message, WebSocket, WebSocketUpgrade},
    extract::State,
    response::IntoResponse,
    routing::get,
    Router,
};
use std::net::SocketAddr;
use std::sync::Arc;
use tokio::sync::broadcast;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use clap::Parser;
use std::path::PathBuf;
use tower_http::services::ServeDir;
use tower_http::cors::CorsLayer;
use axum::http::Method;

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct SystemState {
    pub topic: String,
    pub value: Value,
}

struct AppState {
    tx: broadcast::Sender<SystemState>,
}

#[tokio::main]
// Inline comment: Logic for main
async fn main() {
    let args = cli::Args::parse();
    println!("🚀 [RUST ORCHESTRATOR] Booting OPEN-AIR Native Core...");

    let root = std::env::current_dir().unwrap_or_else(|_| PathBuf::from("."));
    
    // MQTT Config Publisher
    mqtt::publish_protocol_configs(&root, args.no_mqtt);

    let (tx, _rx) = broadcast::channel::<SystemState>(1024);
    let app_state = Arc::new(AppState { tx: tx.clone() });

    let tx_clone_osc = tx.clone();
    tokio::spawn(async move {
        println!("🚀 [AGENT] Launching Native OSC Agent on 0.0.0.0:8000...");
        let osc_agent = openair_osc::OscAgent::new("0.0.0.0".to_string(), 8000);
        let (osc_tx, mut osc_rx) = tokio::sync::mpsc::channel(100);
        tokio::spawn(async move {
            let _ = osc_agent.start(osc_tx).await;
        });
        while let Some(osc_event) = osc_rx.recv().await {
            let system_event = SystemState {
                topic: format!("OpenAir/Protocol/GuiOsc/{}", osc_event.address),
                value: osc_event.value,
            };
            let _ = tx_clone_osc.send(system_event);
        }
    });

    let tx_clone_midi = tx.clone();
    tokio::spawn(async move {
        println!("🚀 [AGENT] Launching Native MIDI Agent...");
        
        let devices_task = tokio::task::spawn_blocking(|| {
            let inputs = openair_midi::oa_midi_scan::scan_inputs();
            let outputs = openair_midi::oa_midi_scan::scan_outputs();
            if !inputs.is_empty() || !outputs.is_empty() {
                let _ = openair_midi::oa_midi_mqtt_publish::publish_devices_mqtt(
                    "127.0.0.1", 
                    1883, 
                    "OpenAir/System/Protocols/midi/Device", 
                    inputs, 
                    outputs
                );
            }
        });
        
        let midi_agent = std::sync::Arc::new(openair_midi::MidiAgent::new(None)); 
        let (midi_tx, mut midi_rx) = tokio::sync::mpsc::channel(100);
        
        let mut mqttoptions = rumqttc::MqttOptions::new("open-air-midi-listener", "127.0.0.1", 1883);
        mqttoptions.set_keep_alive(std::time::Duration::from_secs(30));
        let (mqtt_client, mut mqtt_connection) = rumqttc::Client::new(mqttoptions, 10);
        
        let _ = mqtt_client.subscribe("OpenAir/System/Protocols/midi/Device/Output/#", rumqttc::QoS::AtLeastOnce);
        
        let midi_agent_clone = midi_agent.clone();
        std::thread::spawn(move || {
            for notification in mqtt_connection.iter() {
                if let Ok(rumqttc::Event::Incoming(rumqttc::Packet::Publish(publish))) = notification {
                    let topic = publish.topic.clone();
                    if topic.contains("/Output/Dev") {
                        let parts: Vec<&str> = topic.split('/').collect();
                        if let Some(dev_idx) = parts.iter().position(|&p| p.starts_with("Dev")) {
                            if let Ok(port_idx) = parts[dev_idx].trim_start_matches("Dev").parse::<usize>() {
                                let payload = String::from_utf8_lossy(&publish.payload).trim().to_string();
                                
                                // Topic format: .../Output/Dev1/Channel0/Note/60
                                if dev_idx + 2 < parts.len() && parts[dev_idx + 1].starts_with("Channel") {
                                    if let Ok(channel_display) = parts[dev_idx + 1].trim_start_matches("Channel").parse::<u8>() {
                                        let channel = if channel_display > 0 { channel_display - 1 } else { 0 };
                                        let msg_type = parts[dev_idx + 2];
                                        let data1 = if dev_idx + 3 < parts.len() {
                                            parts[dev_idx + 3].parse::<u8>().unwrap_or(0)
                                        } else { 0 };
                                        
                                        let val = payload.parse::<u8>().unwrap_or(0);
                                        
                                        let mut raw_data = Vec::new();
                                        if msg_type == "Note" {
                                            if val > 0 {
                                                raw_data = vec![144 | channel, data1, val];
                                            } else {
                                                raw_data = vec![128 | channel, data1, 0];
                                            }
                                        } else if msg_type == "ControlChange" {
                                            raw_data = vec![176 | channel, data1, val];
                                        } else if msg_type == "ProgramChange" {
                                            raw_data = vec![192 | channel, val, 0];
                                        } else if msg_type == "PitchBend" {
                                            let pval = payload.parse::<u16>().unwrap_or(0);
                                            raw_data = vec![224 | channel, (pval & 0x7F) as u8, ((pval >> 7) & 0x7F) as u8];
                                        }
                                        
                                        if !raw_data.is_empty() {
                                            println!("   📡 [MIDI MQTT] ⮞ Output on Dev{} -> {} = {}", port_idx, topic, val);
                                            let _ = midi_agent_clone.send(port_idx, &raw_data);
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        });

        tokio::spawn(async move {
            let _ = devices_task.await;
            if let Err(e) = midi_agent.start(midi_tx).await {
                eprintln!("🎹❌ [MIDI AGENT] Failed to start: {:?}", e);
            }
        });
        
        while let Some(midi_event) = midi_rx.recv().await {
            let system_event = SystemState {
                topic: format!("OpenAir/Protocol/MidiIn/{}", midi_event.address),
                value: midi_event.value.clone(),
            };
            let _ = tx_clone_midi.send(system_event);
            
            if let Some(port_idx) = midi_event.value.get("port_index").and_then(|v| v.as_u64()) {
                let channel = midi_event.value.get("channel").and_then(|v| v.as_u64()).unwrap_or(0) + 1;
                let command = midi_event.value.get("command").and_then(|v| v.as_u64()).unwrap_or(0);
                let data1 = midi_event.value.get("data1").and_then(|v| v.as_u64()).unwrap_or(0);
                let data2 = midi_event.value.get("data2").and_then(|v| v.as_u64()).unwrap_or(0);

                let (subtopic, payload_val) = match command {
                    128 => (format!("Channel{}/Note/{}", channel, data1), 0),
                    144 => (format!("Channel{}/Note/{}", channel, data1), data2),
                    176 => (format!("Channel{}/ControlChange/{}", channel, data1), data2),
                    192 => (format!("Channel{}/ProgramChange", channel), data1),
                    224 => (format!("Channel{}/PitchBend", channel), (data2 << 7) | data1),
                    _ => (format!("Channel{}/Raw/{}", channel, command), data1),
                };

                println!("   📡 [MIDI MQTT] ⮜ Input on Dev{} -> {} = {}", port_idx, subtopic, payload_val);
                let topic = format!("OpenAir/System/Protocols/midi/Device/Input/Dev{}/{}", port_idx, subtopic);
                let payload = payload_val.to_string();
                let _ = mqtt_client.publish(topic, rumqttc::QoS::AtLeastOnce, false, payload.as_bytes());
            }
        }
    });

    let tx_clone_aes70 = tx.clone();
    tokio::spawn(async move {
        println!("🚀 [AGENT] Launching Native AES70 Agent (OCP.1 TCP)...");
        let aes70_agent = openair_aes70::Aes70Agent::new("127.0.0.1".to_string(), 50014); 
        let (aes70_tx, mut aes70_rx) = tokio::sync::mpsc::channel(100);
        tokio::spawn(async move {
            if let Err(e) = aes70_agent.start(aes70_tx).await {
                if e.kind() != std::io::ErrorKind::ConnectionRefused {
                    eprintln!("🔊❌ [AES70 AGENT] Failed to start: {:?}", e);
                }
            }
        });
        while let Some(aes70_event) = aes70_rx.recv().await {
            let system_event = SystemState {
                topic: format!("OpenAir/Protocol/AES70/{}", aes70_event.address),
                value: aes70_event.value,
            };
            let _ = tx_clone_aes70.send(system_event);
        }
    });

    // DNS-SD / mDNS discovery agent — continuous browse on its own thread
    // (mdns-sd is sync); retained topics land in the Discovered tab via the
    // same builder sweep as VISA/MIDI. No longer a stub.
    std::thread::spawn(|| {
        println!("🚀 [AGENT] Launching Native DNS-SD Agent (continuous browse)...");
        openair_dnssd::run_browse_agent("127.0.0.1", 1883);
    });

    let tx_clone_visa = tx.clone();
    tokio::spawn(async move {
        println!("🚀 [AGENT] Launching Native VISA Agent (Background Scan)...");

        let mut mqttoptions = rumqttc::MqttOptions::new("open-air-visa-scanner", "127.0.0.1", 1883);
        mqttoptions.set_keep_alive(std::time::Duration::from_secs(30));
        let (mqtt_client, mut mqtt_connection) = rumqttc::Client::new(mqttoptions, 10);

        std::thread::spawn(move || {
            for _ in mqtt_connection.iter() {}
        });

        // The Write daemon and the scan loop share the topic→resource map:
        // every rescan swaps in a fresh mapping.
        let topic_to_resource: std::sync::Arc<std::sync::Mutex<std::collections::HashMap<String, String>>> =
            Default::default();
        // Rescan trigger: the Discovered tab's Scan panel publishes value=1
        // (non-retained) to .../visa/Device/Rescan; the daemon thread signals
        // this loop. Capacity 1: triggers during a running scan coalesce.
        let (rescan_tx, mut rescan_rx) = tokio::sync::mpsc::channel::<()>(1);

        spawn_visa_write_daemon(topic_to_resource.clone(), rescan_tx);

        loop {

        // Clear the previous scan's retained topics first, so devices that
        // moved category (e.g. after a knowledge-base fix) or disappeared
        // don't linger as ghosts in the Discovered tab.
        {
            let old_prefixes: Vec<String> =
                topic_to_resource.lock().unwrap().keys().cloned().collect();
            if !old_prefixes.is_empty() {
                const DEVICE_KEYS: [&str; 13] = [
                    "manufacturer", "model", "serial", "firmware", "raw_idn", "resource",
                    "status", "device_type", "notes", "last_online", "connected", "Write", "Read",
                ];
                for prefix in &old_prefixes {
                    for key in DEVICE_KEYS {
                        let _ = mqtt_client.publish(
                            format!("{}/{}", prefix, key),
                            rumqttc::QoS::AtLeastOnce,
                            true,
                            Vec::<u8>::new(), // empty retained payload = delete
                        );
                    }
                }
                println!("   🧹 [VISA AGENT] cleared retained topics for {} previous device(s)", old_prefixes.len());
            }
        }

        let devices = tokio::task::spawn_blocking(|| {
            openair_visa::oa_visa_scan_for_devices::list_resources()
        }).await.unwrap_or_default();

        let mut counts: std::collections::HashMap<(String, String), usize> = std::collections::HashMap::new();

        // Fresh map per scan; swapped into the shared handle after the loop.
        let mut scan_topic_to_resource = std::collections::HashMap::new();

        for dev in devices {
            println!("   📡 [VISA AGENT] Probing resource: {}", dev);
            
            let mut info = serde_json::json!({ "resource": dev, "status": "found" });
            if let Ok(output) = tokio::process::Command::new("python3")
                .arg("-c")
                .arg(VISA_PROBE_SCRIPT)
                .arg(&dev)
                .output()
                .await
            {
                let out_str = String::from_utf8_lossy(&output.stdout);
                if let Ok(parsed) = serde_json::from_str::<serde_json::Value>(&out_str) {
                    if parsed.get("error").is_none() {
                        let mut merged = parsed.as_object().unwrap().clone();
                        merged.insert("resource".to_string(), serde_json::Value::String(dev.clone()));
                        merged.insert("status".to_string(), serde_json::Value::String("identified".to_string()));
                        
                        let model_str = merged.get("model").and_then(|m| m.as_str()).unwrap_or("Unknown").to_string();
                        let (device_type, notes) = openair_visa::oa_visa_known_devices::get_device_info(&model_str);
                        merged.insert("device_type".to_string(), serde_json::Value::String(device_type.clone()));
                        merged.insert("notes".to_string(), serde_json::Value::String(notes));
                        
                        let key = (device_type.clone(), model_str.clone());
                        let count = counts.entry(key).or_insert(0);
                        
                        let topic_prefix = format!("OpenAir/System/Protocols/visa/Device/{}/{}/Dev{}", device_type.replace(" ", "_"), model_str.replace(" ", "_"), count);
                        scan_topic_to_resource.insert(topic_prefix.clone(), dev.clone());
                        
                        let mut is_online = false;
                        if let Some(raw_idn) = merged.get("raw_idn").and_then(|r| r.as_str()) {
                            if !raw_idn.trim().is_empty() { is_online = true; }
                        }
                        
                        if let Ok(duration) = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH) {
                            merged.insert("last_online".to_string(), serde_json::Value::Number(duration.as_secs().into()));
                        }
                        merged.insert("connected".to_string(), serde_json::Value::Number((if is_online { 1 } else { 0 }).into()));
                        
                        for (k, v) in &merged {
                            let val_str = match v {
                                serde_json::Value::String(s) => s.clone(),
                                serde_json::Value::Number(n) => n.to_string(),
                                _ => v.to_string(),
                            };
                            let _ = mqtt_client.publish(format!("{}/{}", topic_prefix, k), rumqttc::QoS::AtLeastOnce, true, val_str.into_bytes());
                        }
                        
                        let _ = mqtt_client.publish(format!("{}/Write", topic_prefix), rumqttc::QoS::AtLeastOnce, true, "");
                        let _ = mqtt_client.publish(format!("{}/Read", topic_prefix), rumqttc::QoS::AtLeastOnce, true, "");
                        
                        *count += 1;
                        
                        info = serde_json::Value::Object(merged);
                        println!("     ✅ Identified & Published to MQTT: {}", model_str);
                    } else {
                        println!("     ⚠️  Identify failed: {:?}", parsed.get("error"));
                    }
                }
            }

            let system_event = SystemState {
                topic: format!("OpenAir/System/Protocols/visa/Device/Found"),
                value: info,
            };
            let _ = tx_clone_visa.send(system_event);
        }
        println!("✅ [VISA AGENT] Scan & MQTT Publish complete.");

        // Publish the fresh topic→resource mapping for the Write daemon.
        *topic_to_resource.lock().unwrap() = scan_topic_to_resource;

        // Phase 0 item 3: regenerate the Discovered tab panels from the
        // retained discovery topics just published. Transitional — Phase 4
        // replaces this whole pipeline with the Device Registry + a live
        // Discovered widget, and deletes the builder.
        {
            let builder = std::env::current_dir()
                .unwrap_or_else(|_| std::path::PathBuf::from("."))
                .join("Deployment/build_discovered_gui.py");
            if builder.is_file() {
                match tokio::process::Command::new("python3").arg(&builder).spawn() {
                    Ok(_) => println!("🧩 [DISCOVERED-GUI] builder spawned: {}", builder.display()),
                    Err(e) => println!("⚠️  [DISCOVERED-GUI] failed to spawn builder: {e}"),
                }
            } else {
                println!("⚠️  [DISCOVERED-GUI] builder not found at {}", builder.display());
            }
        }

        // Triggers that arrived DURING the scan are stale — the scan they
        // asked for just ran. This also absorbs the browser's 400 ms
        // settle-retained republish of the same press (forwarded live by
        // the broker), which would otherwise queue a second scan.
        while rescan_rx.try_recv().is_ok() {}

        // Wait for the Discovered tab's rescan trigger, then go again.
        println!("⏸️  [VISA AGENT] Scan idle — publish 1 (non-retained) to OpenAir/System/Protocols/visa/Device/Rescan to rescan.");
        if rescan_rx.recv().await.is_none() {
            break;
        }
        println!("🔁 [VISA AGENT] Rescan triggered from the bus.");

        } // end scan loop
    });

    // Sub-router for API endpoints
    let api_state = api::ApiState { root_dir: root.clone() };
    let api_router = api::router(api_state);

    let cors = CorsLayer::new()
        .allow_methods([Method::GET, Method::POST])
        .allow_origin(tower_http::cors::Any);

    let ws_router = Router::new()
        .route("/ws", get(ws_handler))
        .with_state(app_state);

use axum::response::Redirect;

    let app = Router::new()
        .route("/", get(|| async { Redirect::temporary("/index.html") }))
        .nest("/api", api_router)
        .route("/api/health", get(|| async { "Rust Core is Healthy" }))
        .merge(ws_router)
        .fallback_service(ServeDir::new(root.join("FrontEnd")).append_index_html_on_directories(true))
        .layer(cors);

    // Run on the frontend port, since orchestrator replaces the python server.
    let addr = SocketAddr::from(([0, 0, 0, 0], args.port));
    
    let listener = match tokio::net::TcpListener::bind(addr).await {
        Ok(l) => l,
        Err(e) => {
            eprintln!("❌ [API] Could not bind {addr}: {e}");
            eprintln!("        Another instance might be running. Stop it or change port.");
            return;
        }
    };
    
    let local_ip = match std::net::UdpSocket::bind("0.0.0.0:0") {
        Ok(socket) => {
            if socket.connect("8.8.8.8:80").is_ok() {
                socket.local_addr().map(|addr| addr.ip().to_string()).unwrap_or_else(|_| "localhost".to_string())
            } else {
                "localhost".to_string()
            }
        },
        Err(_) => "localhost".to_string(),
    };
    let url = format!("http://{}:{}", local_ip, args.port);
    println!("🌐 [API] Frontend API Server listening on {}", url);
    if !args.no_browser {
        println!("🌐 [WEB] Opening {} in the browser…", url);
        let _ = open::that(url);
    }
    
    if let Err(e) = axum::serve(listener, app).await {
        eprintln!("❌ [API] server error: {e}");
    }
}

// Inline comment: Logic for ws_handler
async fn ws_handler(
    ws: WebSocketUpgrade,
    State(state): State<Arc<AppState>>,
) -> impl IntoResponse {
    println!("🔌 [WEBSOCKET] Client requested connection...");
    ws.on_upgrade(|socket| handle_socket(socket, state))
}

// Inline comment: Logic for handle_socket
async fn handle_socket(mut socket: WebSocket, state: Arc<AppState>) {
    println!("🟢 [WEBSOCKET] Client connected!");
    let mut rx = state.tx.subscribe();
    loop {
        tokio::select! {
            Ok(msg) = rx.recv() => {
                if let Ok(json_str) = serde_json::to_string(&msg) {
                    if socket.send(Message::Text(json_str)).await.is_err() {
                        println!("🔴 [WEBSOCKET] Client disconnected.");
                        break;
                    }
                }
            }
            Some(result) = socket.recv() => {
                match result {
                    Ok(Message::Text(text)) => {
                        println!("📥 [WEBSOCKET] Received from UI: {}", text);
                    }
                    Ok(Message::Close(_)) => {
                        println!("🔴 [WEBSOCKET] Client closed connection.");
                        break;
                    }
                    Err(_) => {
                        println!("⚠️ [WEBSOCKET] Error receiving from client.");
                        break;
                    }
                    _ => {}
                }
            }
        }
    }
}


/// Executes one SCPI write or query against one instrument.
///
/// Takes `sys.argv[1]` = VISA resource, `sys.argv[2]` = SCPI command. Nothing is
/// interpolated into this source — it is a constant, so no caller-supplied value
/// can alter the program. Invoked as `python3 -c SCRIPT <resource> <command>`,
/// which yields `sys.argv == ['-c', resource, command]`.
///
/// Phase 4 replaces this with native Rust VXI-11; until then argv is what keeps
/// the subshell safe.
const VISA_WRITE_SCRIPT: &str = r#"
import pyvisa
import sys

resource = sys.argv[1]
command = sys.argv[2]

try:
    rm = pyvisa.ResourceManager('@py')
except Exception:
    rm = pyvisa.ResourceManager()
try:
    inst = rm.open_resource(resource, open_timeout=2000)
    inst.timeout = 2000
    inst.read_termination = '\n'
    inst.write_termination = '\n'
    if '?' in command:
        print(inst.query(command).strip())
    else:
        inst.write(command)
    inst.close()
except Exception as e:
    print("ERROR:", str(e))
"#;

/// Probes one VISA resource for its `*IDN?` identity and prints a JSON record.
///
/// Takes `sys.argv[1]` = VISA resource. Same argv discipline as
/// [`VISA_WRITE_SCRIPT`]: the resource string comes from the local enumerator
/// rather than the network, but it is passed as data regardless — a resource
/// name is not a place to rely on the trustworthiness of its source.
const VISA_PROBE_SCRIPT: &str = r#"
import pyvisa
import json
import sys

resource = sys.argv[1]

try:
    rm = pyvisa.ResourceManager('@py')
except:
    try:
        rm = pyvisa.ResourceManager()
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

try:
    inst = rm.open_resource(resource, open_timeout=1500)
    inst.timeout = 1500
    inst.read_termination = '\n'
    inst.write_termination = '\n'
    idn = inst.query('*IDN?')
    inst.close()

    parts = [p.strip() for p in idn.split(',')]
    print(json.dumps({
        "manufacturer": parts[0] if len(parts) > 0 else 'Unknown',
        "model": parts[1] if len(parts) > 1 else 'Unknown',
        "serial": parts[2] if len(parts) > 2 else '',
        "firmware": parts[3] if len(parts) > 3 else '',
        "raw_idn": idn.strip()
    }))
except Exception as e:
    print(json.dumps({"error": str(e)}))
"#;

/// VISA Write daemon + rescan listener. Owns its own MQTT connection on a
/// dedicated OS thread (rumqttc sync iter blocks). `topic_to_resource` is
/// shared with the scan loop, which swaps in a fresh mapping per scan;
/// a non-retained truthy publish on .../Device/Rescan signals that loop.
fn spawn_visa_write_daemon(
    topic_to_resource: std::sync::Arc<std::sync::Mutex<std::collections::HashMap<String, String>>>,
    rescan_tx: tokio::sync::mpsc::Sender<()>,
) {
    const RESCAN_TOPIC: &str = "OpenAir/System/Protocols/visa/Device/Rescan";
    println!("🚀 [VISA AGENT] Starting MQTT Daemon for live SCPI commands + rescan trigger...");
    let mut mqttoptions_sub = rumqttc::MqttOptions::new("open-air-visa-daemon", "127.0.0.1", 1883);
    mqttoptions_sub.set_keep_alive(std::time::Duration::from_secs(30));
    let (mut mqtt_client_sub, mut mqtt_connection_sub) = rumqttc::Client::new(mqttoptions_sub, 10);

    let _ = mqtt_client_sub.subscribe("OpenAir/System/Protocols/visa/Device/+/+/+/Write", rumqttc::QoS::AtLeastOnce);
    let _ = mqtt_client_sub.subscribe(RESCAN_TOPIC, rumqttc::QoS::AtLeastOnce);

    std::thread::spawn(move || {
        for notification in mqtt_connection_sub.iter() {
            if let Ok(rumqttc::Event::Incoming(rumqttc::Packet::Publish(publish))) = notification {
                let topic = publish.topic.clone();
                let payload = String::from_utf8_lossy(&publish.payload).trim().to_string();

                if topic == RESCAN_TOPIC {
                    // Retained messages are state, not commands: only a live
                    // press triggers (the browser's settle-retained publish
                    // and boot-time retained replay must not start scans).
                    if !publish.retain && is_truthy_trigger(&payload) {
                        println!("   🔁 [VISA MQTT] Rescan requested via {}", topic);
                        let _ = rescan_tx.try_send(()); // full channel = scan already pending
                    }
                    continue;
                }

                if payload.is_empty() { continue; }

                if let Some(topic_prefix) = topic.strip_suffix("/Write") {
                    let resource = topic_to_resource.lock().unwrap().get(topic_prefix).cloned();
                    if let Some(resource_name) = resource {
                        println!("   📡 [VISA MQTT] Executing on {} -> {}", resource_name, payload);

                        // SECURITY: the resource and the SCPI command are passed as
                        // argv, never interpolated into the script body. The previous
                        // version built the source with `payload.replace("'", "\\'")`,
                        // which is not an escape — it writes a backslash into Python
                        // source, so a payload ending in a backslash consumed the
                        // closing quote and broke out into executable code. The
                        // payload arrives raw off MQTT, so that was remote code
                        // execution. As argv, a payload containing quotes,
                        // backslashes, or newlines is inert data to the interpreter.
                        if let Ok(output) = std::process::Command::new("python3")
                            .arg("-c")
                            .arg(VISA_WRITE_SCRIPT)
                            .arg(&resource_name)
                            .arg(&payload)
                            .output()
                        {
                            let out_str = String::from_utf8_lossy(&output.stdout).trim().to_string();
                            if payload.contains('?') {
                                println!("      ⮜ [VISA MQTT] {} response -> {}", resource_name, out_str);
                                let read_topic = format!("{}/Read", topic_prefix);
                                let _ = mqtt_client_sub.publish(read_topic, rumqttc::QoS::AtLeastOnce, true, out_str.as_bytes());
                                let write_topic = format!("{}/Write", topic_prefix);
                                let _ = mqtt_client_sub.publish(write_topic, rumqttc::QoS::AtLeastOnce, true, "");
                            } else if !out_str.is_empty() {
                                println!("      ⚠️ [VISA MQTT] {} warning/error -> {}", resource_name, out_str);
                            }
                        }
                    }
                }
            }
        }
    });
}

/// Truthy scan trigger: the GUI envelope `{"value":1,...}`, or a bare
/// `1`/`true`/`scan`. `0`, `false`, and empty payloads never trigger.
fn is_truthy_trigger(payload: &str) -> bool {
    if let Ok(v) = serde_json::from_str::<serde_json::Value>(payload) {
        return match v.get("value").unwrap_or(&v) {
            serde_json::Value::Number(n) => n.as_f64().unwrap_or(0.0) != 0.0,
            serde_json::Value::Bool(b) => *b,
            serde_json::Value::String(s) => s == "1" || s.eq_ignore_ascii_case("true") || s.eq_ignore_ascii_case("scan"),
            _ => false,
        };
    }
    payload == "1" || payload.eq_ignore_ascii_case("true") || payload.eq_ignore_ascii_case("scan")
}
