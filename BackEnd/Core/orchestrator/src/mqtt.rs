/**
 * Header: mqtt.rs
 * Purpose: mqtt.rs implementation.
 * Description: Logic and implementation for mqtt.rs implementation.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

use std::fs;
use std::path::Path;
use std::time::Duration;
use ini::Ini;
use rumqttc::{Client, MqttOptions, QoS};
use serde_json::json;

// Inline comment: Logic for publish_protocol_configs
pub fn publish_protocol_configs(root: &Path, no_mqtt: bool) {
    if no_mqtt {
        println!("⏭️  [MQTT] --no-mqtt set; skipping protocol config publish.");
        return;
    }
    
    let com_protocols = root.join("BackEnd").join("ComProtocols");
    if !com_protocols.is_dir() {
        return;
    }
    
    // Attempt to connect to broker using mqtt config.ini if available
    let mut host = "127.0.0.1".to_string();
    let mut port = 1883;
    
    let mqtt_ini = com_protocols.join("openair-mqtt").join("config.ini");
    if let Ok(conf) = Ini::load_from_file(&mqtt_ini) {
        if let Some(section) = conf.section(Some("mqtt")) {
            if let Some(h) = section.get("host") { host = h.to_string(); }
            if let Some(p) = section.get("tcp_port").and_then(|p| p.parse::<u16>().ok()) { port = p; }
        }
    }
    
    let mut mqttoptions = MqttOptions::new("open-air-orchestrator", &host, port);
    mqttoptions.set_keep_alive(Duration::from_secs(30));
    
    let (client, mut connection) = Client::new(mqttoptions, 10);

    std::thread::spawn(move || {
        for _ in 0..10 {
            if connection.iter().next().is_none() {
                break;
            }
        }
    });

    // v41 AgentHeartbeat (contracts H1): the orchestrator's retained beat,
    // typed by openair-contracts. This client is ephemeral, so no LWT here —
    // the persistent supervisor client (Phase 4) owns liveness; until then
    // staleness is readable from lastBeat. Published first so it flushes
    // within the drained connection events.
    let connected_at = openair_contracts::time::from_unix_seconds(
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs_f64())
            .unwrap_or(0.0),
    );
    if let Ok((hb_topic, mut beat)) =
        openair_contracts::heartbeat::heartbeat_lwt("orchestrator", &connected_at, None)
    {
        beat.status = openair_contracts::heartbeat::AgentHeartbeatStatus::Online;
        beat.version = Some(env!("CARGO_PKG_VERSION").to_string());
        beat.pid = Some(std::process::id() as i64);
        if let Ok(bytes) = serde_json::to_vec(&beat) {
            let _ = client.publish(&hb_topic, QoS::AtLeastOnce, true, bytes);
            println!("💓 [MQTT] AgentHeartbeat online (retained) at {}", hb_topic);
        }
    }

    let mut published = Vec::new();
    
    if let Ok(entries) = fs::read_dir(&com_protocols) {
        let mut entries: Vec<_> = entries.flatten().collect();
        entries.sort_by_key(|e| e.file_name());
        for entry in entries {
            let path = entry.path();
            if path.is_dir() {
                if let Some(name) = path.file_name().and_then(|n| n.to_str()) {
                    if name.starts_with("openair-") {
                        let proto = &name["openair-".len()..];
                        let ini_path = path.join("config.ini");
                        if ini_path.is_file() {
                            if let Ok(conf) = Ini::load_from_file(&ini_path) {
                                let mut config_map = serde_json::Map::new();
                                for (sec, prop) in conf.iter() {
                                    let sec_name = sec.as_deref().unwrap_or("").to_string();
                                    let mut prop_map = serde_json::Map::new();
                                    for (k, v) in prop.iter() {
                                        prop_map.insert(k.to_string(), json!(v));
                                    }
                                    config_map.insert(sec_name, json!(prop_map));
                                }
                                
                                let sect = conf.section(Some(proto));
                                let topic = sect.and_then(|s| s.get("topic")).unwrap_or(&format!("OpenAir/System/Protocols/{}", proto)).to_string();
                                
                                let rel_path = ini_path.strip_prefix(root).unwrap_or(&ini_path).to_string_lossy();
                                
                                let payload = json!({
                                    "value": config_map,
                                    "path": rel_path,
                                    "source": "backend"
                                });
                                
                                let _ = client.publish(format!("{}/config", topic), QoS::AtLeastOnce, true, payload.to_string());
                                let _ = client.publish(format!("{}/status", topic), QoS::AtLeastOnce, true, "online");
                                
                                published.push(topic);
                            }
                        }
                    }
                }
            }
        }
    }
    
    if !published.is_empty() {
        println!("📡 [MQTT] Published {} protocol configs (retained) to {}:{}:", published.len(), host, port);
        for t in published {
            println!("   • {}/config  (+ /status=online)", t);
        }
    }
}
