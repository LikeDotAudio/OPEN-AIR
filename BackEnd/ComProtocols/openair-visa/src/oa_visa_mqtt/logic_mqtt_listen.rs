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
pub static DEVICE_LAST_ACTIVITY: Mutex<Option<HashMap<String, u64>>> = Mutex::new(None);
pub static DEVICE_FAILURES: Mutex<Option<HashMap<String, u8>>> = Mutex::new(None);

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

pub fn record_activity(topic_prefix: &str) {
    if let Ok(duration) = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH) {
        let now = duration.as_secs();
        if let Ok(mut activity) = DEVICE_LAST_ACTIVITY.lock() {
            if activity.is_none() { *activity = Some(HashMap::new()); }
            activity.as_mut().unwrap().insert(topic_prefix.to_string(), now);
        }
        if let Ok(mut failures) = DEVICE_FAILURES.lock() {
            if failures.is_none() { *failures = Some(HashMap::new()); }
            failures.as_mut().unwrap().insert(topic_prefix.to_string(), 0);
        }
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
    
    let client_heartbeat = client.clone();
    
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
                            let query_res = Python::with_gil(|py| {
                                execute_query(py, &resource_name, &command_to_execute)
                            });
                            
                            let result_str = match query_res {
                                Ok(res) => {
                                    record_activity(topic_prefix);
                                    res
                                },
                                Err(e) => format!("ERROR: {}", e),
                            };
                            
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
                            let write_res = Python::with_gil(|py| {
                                execute_write(py, &resource_name, &command_to_execute)
                            });
                            if write_res.is_ok() {
                                record_activity(topic_prefix);
                            }
                        }
                    }
                }
            }
        }
    });

    // ---------------------------------------------------------
    // Background Keep-Alive / Heartbeat Runner
    // ---------------------------------------------------------
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
            
            let now = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_secs();
            
            for (topic_prefix, resource_name) in devices {
                let last_active = {
                    let guard = DEVICE_LAST_ACTIVITY.lock().unwrap();
                    guard.as_ref().and_then(|m| m.get(&topic_prefix).copied()).unwrap_or(0)
                };
                
                let mut check_failed = false;
                
                // If it hasn't been active in the last 30 seconds, we probe it
                if now - last_active > 30 {
                    let is_alive = Python::with_gil(|py| {
                        execute_query(py, &resource_name, "*IDN?").is_ok()
                    });
                    
                    if is_alive {
                        record_activity(&topic_prefix);
                        let publish_topic = format!("{}/last_online", topic_prefix);
                        let _ = client_heartbeat.publish(publish_topic, QoS::AtLeastOnce, true, now.to_string().as_bytes());
                        let reachable_topic = format!("{}/reachable", topic_prefix);
                        let _ = client_heartbeat.publish(reachable_topic, QoS::AtLeastOnce, true, "1".as_bytes());
                    } else {
                        check_failed = true;
                    }
                } else {
                    // It was active recently! Keep it green in the UI.
                    let publish_topic = format!("{}/last_online", topic_prefix);
                    let _ = client_heartbeat.publish(publish_topic, QoS::AtLeastOnce, true, now.to_string().as_bytes());
                    let reachable_topic = format!("{}/reachable", topic_prefix);
                    let _ = client_heartbeat.publish(reachable_topic, QoS::AtLeastOnce, true, "1".as_bytes());
                }
                
                if check_failed {
                    // First check failed, wait and try again immediately
                    thread::sleep(Duration::from_millis(1500));
                    let is_alive_retry = Python::with_gil(|py| {
                        execute_query(py, &resource_name, "*IDN?").is_ok()
                    });
                    
                    if is_alive_retry {
                        record_activity(&topic_prefix);
                        let publish_topic = format!("{}/last_online", topic_prefix);
                        let _ = client_heartbeat.publish(publish_topic, QoS::AtLeastOnce, true, now.to_string().as_bytes());
                        let reachable_topic = format!("{}/reachable", topic_prefix);
                        let _ = client_heartbeat.publish(reachable_topic, QoS::AtLeastOnce, true, "1".as_bytes());
                    } else {
                        // Second check failed! Mark unreachable.
                        {
                            let mut guard = DEVICE_FAILURES.lock().unwrap();
                            if guard.is_none() { *guard = Some(HashMap::new()); }
                            let map = guard.as_mut().unwrap();
                            map.insert(topic_prefix.clone(), 2);
                        }
                        let reachable_topic = format!("{}/reachable", topic_prefix);
                        let _ = client_heartbeat.publish(reachable_topic, QoS::AtLeastOnce, true, "0".as_bytes());
                    }
                }
                
                // Sleep between devices to avoid network/GIL slamming
                thread::sleep(Duration::from_millis(500));
            }
            
            // Rest before next round-robin sweep
            thread::sleep(Duration::from_secs(30));
        }
    });
    
    Ok(())
}
