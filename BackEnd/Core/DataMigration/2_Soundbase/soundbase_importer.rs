//! Standalone Soundbase Importer module written in Rust.
//! Parses Soundbase PDF exports / CSV data (e.g., SB PDF.csv),
//! maps Group, Model, Band, Name, Preset, Spacing, Frequency fields,
//! and publishes the result to the MQTT bus.

use csv::ReaderBuilder;
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SoundbaseChannel {
    pub group: String,
    pub model: String,
    pub band: String,
    pub name: String,
    pub preset: String,
    pub spacing: String,
    pub frequency_mhz: f64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SoundbaseParseResult {
    pub status: String,
    pub source_format: String,
    pub file_path: String,
    pub mqtt_topic: String,
    pub total_channels: usize,
    pub channels: Vec<SoundbaseChannel>,
}

pub const SOUNDBASE_MQTT_TOPIC: &str = "OpenAir/System/DataMigration/Soundbase/ImportedData";

/// Parses a Soundbase report / PDF CSV export directly into structured data and publishes to MQTT.
pub fn parse_soundbase_report(file_path: impl AsRef<Path>) -> Result<SoundbaseParseResult, String> {
    let path = file_path.as_ref();
    let file_content = fs::read_to_string(path)
        .map_err(|e| format!("Failed to read file {:?}: {}", path, e))?;
    parse_soundbase_report_str(&file_content, &path.to_string_lossy())
}

/// Parses a raw Soundbase CSV content string directly into structured data and publishes to MQTT.
pub fn parse_soundbase_report_str(file_content: &str, source_name: &str) -> Result<SoundbaseParseResult, String> {
    let mut channels = Vec::new();
    let mut rdr = ReaderBuilder::new()
        .has_headers(true)
        .flexible(true)
        .from_reader(file_content.as_bytes());

    for record in rdr.records() {
        if let Ok(rec) = record {
            if rec.len() >= 7 {
                let group = rec[0].trim().to_string();
                let model = rec[1].trim().to_string();
                let band = rec[2].trim().to_string();
                let name = rec[3].trim().to_string();
                let preset = rec[4].trim().to_string();
                let spacing = rec[5].trim().to_string();
                
                if let Ok(freq) = rec[6].trim().parse::<f64>() {
                    channels.push(SoundbaseChannel {
                        group,
                        model,
                        band,
                        name,
                        preset,
                        spacing,
                        frequency_mhz: freq,
                    });
                }
            }
        }
    }

    let result = SoundbaseParseResult {
        status: "success".to_string(),
        source_format: "Soundbase_CSV_Report".to_string(),
        file_path: source_name.to_string(),
        mqtt_topic: SOUNDBASE_MQTT_TOPIC.to_string(),
        total_channels: channels.len(),
        channels,
    };

    if let Ok(json_payload) = serde_json::to_string_pretty(&result) {
        publish_to_mqtt(SOUNDBASE_MQTT_TOPIC, &json_payload);
    }

    Ok(result)
}

pub fn publish_to_mqtt(topic: &str, payload: &str) {
    use rumqttc::{Client, MqttOptions, Event, Packet, QoS};
    use std::time::Duration;

    let mut mqttoptions = MqttOptions::new("openair-soundbase-importer", "127.0.0.1", 1883);
    mqttoptions.set_keep_alive(Duration::from_secs(10));

    let (client, mut connection) = Client::new(mqttoptions, 10);
    let _ = client.publish(topic, QoS::AtLeastOnce, true, payload.as_bytes());

    let deadline = std::time::Instant::now() + Duration::from_secs(3);
    let mut acked = false;
    for notification in connection.iter() {
        if let Ok(Event::Incoming(Packet::PubAck(_))) = notification {
            println!("[SOUNDBASE MQTT PUBLISHER] Published & Acked by Broker (127.0.0.1:1883) Topic: '{}'", topic);
            acked = true;
            break;
        }
        if std::time::Instant::now() > deadline {
            break;
        }
    }
    if acked {
        std::thread::sleep(Duration::from_millis(200));
    }
}
