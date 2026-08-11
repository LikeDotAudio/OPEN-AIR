//! Standalone IAS Importer & Test Runner written in Rust.
//! Parses IAS HTML reports (e.g., report.html), serializes to structured data,
//! and publishes the parsed channel matrix to the MQTT bus.

use scraper::{Html, Selector};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IasChannel {
    pub zone: String,
    pub group: String,
    pub device: String,
    pub name: String,
    pub freq_mhz: f64,
    pub band_info: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct IasParseResult {
    pub status: String,
    pub source_format: String,
    pub file_path: String,
    pub mqtt_topic: String,
    pub total_channels: usize,
    pub channels: Vec<IasChannel>,
}

pub const IAS_MQTT_TOPIC: &str = "OpenAir/System/DataMigration/IAS/ImportedData";

/// Standalone parser for IAS HTML Reports.
/// Extract zones, headers, device names, channel titles, and frequencies.
pub fn parse_ias_report(file_path: impl AsRef<Path>) -> Result<IasParseResult, String> {
    let path = file_path.as_ref();
    let content = fs::read_to_string(path)
        .map_err(|e| format!("Failed to read file {:?}: {}", path, e))?;
    parse_ias_report_str(&content, &path.to_string_lossy())
}

/// Standalone parser for raw IAS HTML Report content strings.
pub fn parse_ias_report_str(content: &str, source_name: &str) -> Result<IasParseResult, String> {
    let mut channels = Vec::new();
    let document = Html::parse_document(content);

    let tr_selector = Selector::parse("tr").map_err(|e| format!("Selector error: {:?}", e))?;
    let td_selector = Selector::parse("td").map_err(|e| format!("Selector error: {:?}", e))?;
    let th_selector = Selector::parse("th").map_err(|e| format!("Selector error: {:?}", e))?;
    let b_selector = Selector::parse("b").map_err(|e| format!("Selector error: {:?}", e))?;
    let p_selector = Selector::parse("p").map_err(|e| format!("Selector error: {:?}", e))?;

    let mut current_zone = "Default Zone".to_string();
    let mut current_group = "General".to_string();

    // Parse Zones from <p style="... font-size: large ...">Zone: ...</p>
    for p_elem in document.select(&p_selector) {
        let p_text = p_elem.text().collect::<Vec<_>>().join("");
        if p_text.contains("Zone:") {
            if let Some(zone_str) = p_text.split("Zone:").nth(1) {
                current_zone = zone_str.trim().to_string();
            }
        }
    }

    // Parse Table Assignments
    let assignment_selector = Selector::parse("table.Assignment").map_err(|e| format!("Selector error: {:?}", e))?;
    for table in document.select(&assignment_selector) {
        // Extract Group/Header from <th>
        if let Some(th) = table.select(&th_selector).next() {
            current_group = th.text().collect::<Vec<_>>().join("").trim().to_string();
        }

        for row in table.select(&tr_selector) {
            let cells: Vec<_> = row.select(&td_selector).collect();
            if cells.len() >= 4 {
                // Read chunks of 4 td cells (IAS formats up to 2 channel blocks per row)
                for chunk in cells.chunks(4) {
                    if chunk.len() == 4 {
                        let device = chunk[0].text().collect::<Vec<_>>().join("").trim().to_string();
                        let name = chunk[1].text().collect::<Vec<_>>().join("").trim().to_string();
                        
                        // Frequency is wrapped inside <b>
                        let freq_text = if let Some(b_elem) = chunk[3].select(&b_selector).next() {
                            b_elem.text().collect::<Vec<_>>().join("").trim().to_string()
                        } else {
                            chunk[3].text().collect::<Vec<_>>().join("").trim().to_string()
                        };

                        if let Ok(freq_mhz) = freq_text.parse::<f64>() {
                            if freq_mhz > 100.0 && freq_mhz < 3000.0 {
                                channels.push(IasChannel {
                                    zone: current_zone.clone(),
                                    group: current_group.clone(),
                                    device: if device.is_empty() { "Generic RF".into() } else { device },
                                    name: if name.is_empty() { format!("CH_{}", channels.len() + 1) } else { name },
                                    freq_mhz,
                                    band_info: "UHF".to_string(),
                                });
                            }
                        }
                    }
                }
            }
        }
    }

    let result = IasParseResult {
        status: "success".to_string(),
        source_format: "IAS_HTML_Report".to_string(),
        file_path: source_name.to_string(),
        mqtt_topic: IAS_MQTT_TOPIC.to_string(),
        total_channels: channels.len(),
        channels,
    };

    // Publish parsed result to MQTT
    if let Ok(json_payload) = serde_json::to_string_pretty(&result) {
        publish_to_mqtt(IAS_MQTT_TOPIC, &json_payload);
    }

    Ok(result)
}

pub fn publish_to_mqtt(topic: &str, payload: &str) {
    use rumqttc::{Client, MqttOptions, Event, Packet, QoS};
    use std::time::Duration;

    let mut mqttoptions = MqttOptions::new("openair-ias-importer", "127.0.0.1", 1883);
    mqttoptions.set_keep_alive(Duration::from_secs(10));
    // Max payload is ~35KB, set max_packet_size to 5MB
    mqttoptions.set_max_packet_size(5_000_000, 5_000_000);

    let (client, mut connection) = Client::new(mqttoptions, 10);
    let deadline = std::time::Instant::now() + Duration::from_secs(5);
    let mut connected = false;
    let mut acked = false;

    for notification in connection.iter() {
        if let Ok(event) = notification {
            match event {
                Event::Incoming(Packet::ConnAck(_)) => {
                    connected = true;
                    let _ = client.publish(topic, QoS::AtLeastOnce, true, payload.as_bytes());
                    println!("[IAS MQTT PUBLISHER] Connected & Published payload to '{}'", topic);
                }
                Event::Incoming(Packet::PubAck(_)) => {
                    println!("[IAS MQTT PUBLISHER] Broker Acked payload on '{}'", topic);
                    acked = true;
                    break;
                }
                _ => {}
            }
        }
        if std::time::Instant::now() > deadline {
            break;
        }
    }
    if acked || connected {
        std::thread::sleep(Duration::from_millis(300));
    }
}
