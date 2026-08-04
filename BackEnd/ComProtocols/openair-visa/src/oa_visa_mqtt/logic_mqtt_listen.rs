/**
 * Header: logic_mqtt_listen.rs
 * Purpose: logic_mqtt_listen.rs implementation.
 * Description: Logic and implementation for logic_mqtt_listen.rs implementation.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

use rumqttc::{Client, MqttOptions, QoS, Event, Packet};
use std::time::Duration;
use std::sync::Mutex;
use std::collections::HashMap;
use std::thread;
use pyo3::prelude::*;
use crate::oa_visa_pyvisa_wrapper::{execute_query, execute_write};

pub static DEVICE_MAP: Mutex<Option<HashMap<String, String>>> = Mutex::new(None);

// Inline comment: Logic for update_device_map
pub fn update_device_map(topic: String, resource: String) {
    let mut map_guard = DEVICE_MAP.lock().unwrap();
    if map_guard.is_none() {
        *map_guard = Some(HashMap::new());
    }
    if let Some(map) = map_guard.as_mut() {
        map.insert(topic, resource);
    }
}

#[pyfunction]
#[pyo3(signature = (broker_ip, port, base_topic))]
// Inline comment: Logic for start_mqtt_daemon
pub fn start_mqtt_daemon(broker_ip: String, port: u16, base_topic: String) -> PyResult<()> {
    let mut mqttoptions = MqttOptions::new(format!("openair-visa-daemon-{}", std::process::id()), &broker_ip, port);
    mqttoptions.set_keep_alive(Duration::from_secs(5));
    
    let (client, mut connection) = Client::new(mqttoptions, 10);
    
    let sub_topic = format!("{}/+/+/+/Write", base_topic.trim_end_matches('/'));
    let _ = client.subscribe(&sub_topic, QoS::AtLeastOnce);
    
    thread::spawn(move || {
        for notification in connection.iter() {
            if let Ok(Event::Incoming(Packet::Publish(publish))) = notification {
                let topic = publish.topic.clone();
                let payload = String::from_utf8_lossy(&publish.payload).trim().to_string();
                
                // Skip empty payloads (initial topic creation)
                if payload.is_empty() {
                    continue;
                }
                
                if let Some(topic_prefix) = topic.strip_suffix("/Write") {
                    let resource_opt = {
                        let map_guard = DEVICE_MAP.lock().unwrap();
                        if let Some(map) = map_guard.as_ref() {
                            map.get(topic_prefix).cloned()
                        } else {
                            None
                        }
                    };
                    
                    if let Some(resource_name) = resource_opt {
                        // Parse JSON if possible to extract correlation_id and command
                        let mut correlation_id = None;
                        let mut command_to_execute = payload.clone();
                        
                        if let Ok(json_val) = serde_json::from_str::<serde_json::Value>(&payload) {
                            if let Some(cmd) = json_val.get("command").and_then(|v| v.as_str()) {
                                command_to_execute = cmd.to_string();
                            }
                            if let Some(cid) = json_val.get("correlation_id").and_then(|v| v.as_str()) {
                                correlation_id = Some(cid.to_string());
                            }
                        }

                        if command_to_execute.contains('?') {
                            // Query: command contains a '?' so read response via PyVISA
                            let result_str = Python::with_gil(|py| {
                                execute_query(py, &resource_name, &command_to_execute)
                                    .unwrap_or_else(|e| format!("ERROR: {}", e))
                            });
                            
                            let read_topic = format!("{}/Read", topic_prefix);
                            let write_topic = format!("{}/Write", topic_prefix);
                            
                            // Wrap result in JSON if correlation ID exists
                            let final_result = if let Some(cid) = correlation_id {
                                serde_json::json!({
                                    "correlation_id": cid,
                                    "result": result_str
                                }).to_string()
                            } else {
                                result_str
                            };
                            
                            let _ = client.publish(read_topic, QoS::AtLeastOnce, true, final_result.as_bytes());
                            let _ = client.publish(write_topic, QoS::AtLeastOnce, true, "".as_bytes());
                        } else {
                            // Write-only: send command via PyVISA
                            Python::with_gil(|py| {
                                let _ = execute_write(py, &resource_name, &command_to_execute);
                            });
                        }
                    }
                }
            }
        }
    });

    // ---------------------------------------------------------
    // Background Keep-Alive / Heartbeat Runner
    // ---------------------------------------------------------
    let client_heartbeat = client.clone();
    thread::spawn(move || {
        loop {
            // Clone the map entries to avoid holding the lock during slow operations
            let devices: Vec<(String, String)> = {
                let map_guard = DEVICE_MAP.lock().unwrap();
                if let Some(map) = map_guard.as_ref() {
                    map.iter().map(|(k, v)| (k.clone(), v.clone())).collect()
                } else {
                    Vec::new()
                }
            };
            
            for (topic_prefix, resource_name) in devices {
                // Lightweight check: prove the command parser is responsive
                let is_alive = Python::with_gil(|py| {
                    execute_query(py, &resource_name, "*IDN?").is_ok()
                });
                
                if is_alive {
                    if let Ok(duration) = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH) {
                        let last_online = duration.as_secs().to_string();
                        let publish_topic = format!("{}/last_online", topic_prefix);
                        let _ = client_heartbeat.publish(publish_topic, QoS::AtLeastOnce, true, last_online.as_bytes());
                    }
                }
                
                // Sleep between devices to avoid network/GIL slamming
                thread::sleep(Duration::from_millis(500));
            }
            
            // Rest before next round-robin sweep (check every ~30 seconds)
            thread::sleep(Duration::from_secs(30));
        }
    });
    
    Ok(())
}
