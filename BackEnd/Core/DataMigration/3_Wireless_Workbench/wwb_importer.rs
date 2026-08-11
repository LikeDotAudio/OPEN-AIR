//! Standalone Shure Wireless Workbench (.shw) Importer written in Rust with MQTT publishing.

use serde::{Deserialize, Serialize};
use std::fs::File;
use std::io::Read;
use std::path::Path;
use zip::ZipArchive;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WwbChannel {
    pub device_name: String,
    pub manufacturer: String,
    pub model: String,
    pub band: String,
    pub channel_number: u32,
    pub channel_name: String,
    pub frequency_mhz: f64,
    pub zone: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct WwbParseResult {
    pub status: String,
    pub source_format: String,
    pub file_path: String,
    pub mqtt_topic: String,
    pub total_channels: usize,
    pub channels: Vec<WwbChannel>,
}

pub const WWB_MQTT_TOPIC: &str = "OpenAir/System/DataMigration/WWB/ImportedData";

/// Parses Shure Wireless Workbench .shw XML or .zip/.shw archives
pub fn parse_wwb_file(file_path: impl AsRef<Path>) -> Result<WwbParseResult, String> {
    let path = file_path.as_ref();
    if let Ok(file) = File::open(path) {
        if let Ok(mut archive) = ZipArchive::new(file) {
            let mut channels = Vec::new();
            for i in 0..archive.len() {
                if let Ok(mut zip_file) = archive.by_index(i) {
                    let mut content = String::new();
                    if zip_file.read_to_string(&mut content).is_ok() {
                        parse_wwb_xml_content(&content, &mut channels);
                    }
                }
            }
            return build_wwb_result(channels, &path.to_string_lossy());
        } else if let Ok(content) = std::fs::read_to_string(path) {
            return parse_wwb_str(&content, &path.to_string_lossy());
        }
    }
    Err(format!("Failed to open WWB file {:?}", path))
}

pub fn parse_wwb_str(content: &str, source_name: &str) -> Result<WwbParseResult, String> {
    let mut channels = Vec::new();
    parse_wwb_xml_content(content, &mut channels);
    build_wwb_result(channels, source_name)
}

fn build_wwb_result(channels: Vec<WwbChannel>, source_name: &str) -> Result<WwbParseResult, String> {
    let result = WwbParseResult {
        status: "success".to_string(),
        source_format: "Shure_WWB_SHW".to_string(),
        file_path: source_name.to_string(),
        mqtt_topic: WWB_MQTT_TOPIC.to_string(),
        total_channels: channels.len(),
        channels,
    };

    if let Ok(json_payload) = serde_json::to_string_pretty(&result) {
        publish_to_mqtt(WWB_MQTT_TOPIC, &json_payload);
    }

    Ok(result)
}

fn parse_wwb_xml_content(content: &str, channels: &mut Vec<WwbChannel>) {
    let mut current_manufacturer = "Shure".to_string();
    let mut current_model = "Generic".to_string();
    let mut current_device_name = "".to_string();
    let mut current_band = "".to_string();
    let mut current_zone = "".to_string();

    let mut in_device = false;
    let mut in_channel = false;
    let mut channel_num = 1;
    let mut ch_name = "".to_string();
    let mut freq_khz: Option<f64> = None;

    for line in content.lines() {
        let trimmed = line.trim();
        if trimmed.starts_with("<device>") {
            in_device = true;
            current_manufacturer = "Shure".to_string();
            current_model = "Generic".to_string();
            current_device_name = "".to_string();
            current_band = "".to_string();
            current_zone = "".to_string();
        } else if trimmed.starts_with("</device>") {
            in_device = false;
        } else if trimmed.starts_with("<channel ") {
            in_channel = true;
            ch_name = "".to_string();
            freq_khz = None;
            if let Some(pos) = trimmed.find("number=\"") {
                let rest = &trimmed[pos + 8..];
                if let Some(end) = rest.find('"') {
                    channel_num = rest[..end].parse::<u32>().unwrap_or(1);
                }
            }
        } else if trimmed.starts_with("</channel>") {
            if in_channel {
                if let Some(f_khz) = freq_khz {
                    let freq_mhz = f_khz / 1000.0;
                    if freq_mhz > 100.0 && freq_mhz < 3000.0 {
                        channels.push(WwbChannel {
                            device_name: current_device_name.clone(),
                            manufacturer: current_manufacturer.clone(),
                            model: current_model.clone(),
                            band: current_band.clone(),
                            channel_number: channel_num,
                            channel_name: ch_name.clone(),
                            frequency_mhz: freq_mhz,
                            zone: current_zone.clone(),
                        });
                    }
                }
            }
            in_channel = false;
        }

        if in_device && !in_channel {
            if trimmed.starts_with("<manufacturer") {
                current_manufacturer = extract_xml_cdata(trimmed);
            } else if trimmed.starts_with("<model") {
                current_model = extract_xml_cdata(trimmed);
            } else if trimmed.starts_with("<device_name") {
                current_device_name = extract_xml_cdata(trimmed);
            } else if trimmed.starts_with("<band") {
                current_band = extract_xml_text(trimmed);
            } else if trimmed.starts_with("<zone") {
                current_zone = extract_xml_text(trimmed);
            }
        } else if in_channel {
            if trimmed.starts_with("<channel_name") {
                ch_name = extract_xml_cdata(trimmed);
            } else if trimmed.starts_with("<frequency") {
                let freq_str = extract_xml_text(trimmed);
                if let Ok(f) = freq_str.parse::<f64>() {
                    freq_khz = Some(f);
                }
            }
        }
    }
}

fn extract_xml_cdata(line: &str) -> String {
    if let Some(start) = line.find("<![CDATA[") {
        let rest = &line[start + 9..];
        if let Some(end) = rest.find("]]>") {
            return rest[..end].to_string();
        }
    }
    extract_xml_text(line)
}

fn extract_xml_text(line: &str) -> String {
    if let Some(start) = line.find('>') {
        let rest = &line[start + 1..];
        if let Some(end) = rest.find('<') {
            return rest[..end].to_string();
        }
    }
    "".to_string()
}

pub fn publish_to_mqtt(topic: &str, payload: &str) {
    use rumqttc::{Client, MqttOptions, Event, Packet, QoS};
    use std::time::Duration;

    let mut mqttoptions = MqttOptions::new("openair-wwb-importer", "127.0.0.1", 1883);
    mqttoptions.set_keep_alive(Duration::from_secs(10));
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
                    println!("[WWB MQTT PUBLISHER] Connected & Published payload to '{}'", topic);
                }
                Event::Incoming(Packet::PubAck(_)) => {
                    println!("[WWB MQTT PUBLISHER] Broker Acked payload on '{}'", topic);
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
