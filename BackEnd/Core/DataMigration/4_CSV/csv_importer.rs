//! Smart CSV Pattern Classifier & Importer written in Rust with MQTT Publishing.

use csv::ReaderBuilder;
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum RecognizedCsvPattern {
    SoundbaseReport,    // Headers: Group, Model, Band, Name, Preset, Spacing, Frequency
    StandardZoneGroup,  // Headers: ZONE, GROUP, DEVICE, NAME, FREQ
    UnknownCustom,      // Arbitrary / Custom CSV
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StandardRfRecord {
    pub zone: String,
    pub group: String,
    pub device: String,
    pub name: String,
    pub frequency_mhz: f64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct CsvRecognizedResult {
    pub status: String,
    pub source_file: String,
    pub pattern: RecognizedCsvPattern,
    pub pattern_name: String,
    pub mqtt_topic: String,
    pub total_records: usize,
    pub records: Vec<StandardRfRecord>,
}

pub const CSV_IMPORTER_MQTT_TOPIC: &str = "OpenAir/System/DataMigration/CSV/ImportedData";

/// Smartly classifies CSV patterns and extracts standard RF records.
pub fn parse_and_classify_csv(file_path: impl AsRef<Path>) -> Result<CsvRecognizedResult, String> {
    let path = file_path.as_ref();
    let content = fs::read_to_string(path)
        .map_err(|e| format!("Failed to read CSV file {:?}: {}", path, e))?;

    let mut rdr = ReaderBuilder::new()
        .has_headers(true)
        .flexible(true)
        .from_reader(content.as_bytes());

    let headers = rdr
        .headers()
        .map_err(|e| format!("Failed to parse headers: {}", e))?
        .clone();

    let header_vec: Vec<String> = headers.iter().map(|s| s.trim().to_uppercase()).collect();

    // Pattern Recognition Logic
    let (pattern, pattern_name) = if header_vec.contains(&"SPACING".into()) && header_vec.contains(&"FREQUENCY".into()) {
        (RecognizedCsvPattern::SoundbaseReport, "Soundbase CSV Export")
    } else if header_vec.contains(&"ZONE".into()) && header_vec.contains(&"FREQ".into()) {
        (RecognizedCsvPattern::StandardZoneGroup, "Standard Zone/Group CSV")
    } else {
        (RecognizedCsvPattern::UnknownCustom, "Arbitrary Custom CSV")
    };

    let mut records = Vec::new();

    match pattern {
        RecognizedCsvPattern::SoundbaseReport => {
            for rec in rdr.records().flatten() {
                if rec.len() >= 7 {
                    if let Ok(freq) = rec[6].trim().parse::<f64>() {
                        records.push(StandardRfRecord {
                            zone: rec[0].trim().to_string(),
                            group: rec[2].trim().to_string(),
                            device: rec[1].trim().to_string(),
                            name: rec[3].trim().to_string(),
                            frequency_mhz: freq,
                        });
                    }
                }
            }
        }
        RecognizedCsvPattern::StandardZoneGroup => {
            for rec in rdr.records().flatten() {
                if rec.len() >= 5 {
                    let zone = rec[0].trim().to_string();
                    let group = rec[1].trim().to_string();
                    let device = rec[2].trim().to_string();
                    let name = rec[3].trim().to_string();
                    let freq_str = rec[4].trim();

                    if let Ok(freq) = freq_str.parse::<f64>() {
                        if freq > 100.0 && freq < 3000.0 {
                            records.push(StandardRfRecord {
                                zone: if zone.is_empty() { "N/A".into() } else { zone },
                                group: if group.is_empty() { "General".into() } else { group },
                                device: if device.is_empty() { "Generic RF".into() } else { device },
                                name: if name.is_empty() { format!("CH_{}", records.len() + 1) } else { name },
                                frequency_mhz: freq,
                            });
                        }
                    }
                }
            }
        }
        RecognizedCsvPattern::UnknownCustom => {
            for rec in rdr.records().flatten() {
                // Heuristic scan for frequency floats in cells
                for cell in rec.iter() {
                    if let Ok(freq) = cell.trim().parse::<f64>() {
                        if freq > 100.0 && freq < 3000.0 {
                            records.push(StandardRfRecord {
                                zone: "Unknown Zone".into(),
                                group: "Custom CSV".into(),
                                device: "Generic".into(),
                                name: format!("CH_{}", records.len() + 1),
                                frequency_mhz: freq,
                            });
                            break;
                        }
                    }
                }
            }
        }
    }

    let result = CsvRecognizedResult {
        status: "success".to_string(),
        source_file: path.to_string_lossy().into_owned(),
        pattern,
        pattern_name: pattern_name.to_string(),
        mqtt_topic: CSV_IMPORTER_MQTT_TOPIC.to_string(),
        total_records: records.len(),
        records,
    };

    if let Ok(json_payload) = serde_json::to_string_pretty(&result) {
        publish_to_mqtt(CSV_IMPORTER_MQTT_TOPIC, &json_payload);
    }

    Ok(result)
}

pub fn publish_to_mqtt(topic: &str, payload: &str) {
    use rumqttc::{Client, MqttOptions, Event, Packet, QoS};
    use std::time::Duration;

    let mut mqttoptions = MqttOptions::new("openair-csv-importer", "127.0.0.1", 1883);
    mqttoptions.set_keep_alive(Duration::from_secs(10));

    let (client, mut connection) = Client::new(mqttoptions, 10);
    let _ = client.publish(topic, QoS::AtLeastOnce, true, payload.as_bytes());

    let deadline = std::time::Instant::now() + Duration::from_secs(3);
    let mut acked = false;
    for notification in connection.iter() {
        if let Ok(Event::Incoming(Packet::PubAck(_))) = notification {
            println!("[SMART CSV MQTT PUBLISHER] Published & Acked by Broker (127.0.0.1:1883) Topic: '{}'", topic);
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
