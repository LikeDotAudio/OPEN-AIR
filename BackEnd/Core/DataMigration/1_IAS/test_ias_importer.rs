//! Standalone Test Runner for IAS Importer & MQTT pipeline.

use std::path::Path;

mod ias_importer;

fn main() {
    let report_path = "/home/anthony/Documents/GitProjects/OPEN-AIR/BackEnd/Core/DataMigration/1_IAS/test_data/report.html";
    println!("[IAS Test Runner] Testing standalone IAS Importer with file: {}", report_path);

    match ias_importer::parse_ias_report(Path::new(report_path)) {
        Ok(result) => {
            println!("\n=== IAS PARSE SUCCESS ===");
            println!("Status: {}", result.status);
            println!("Source Format: {}", result.source_format);
            println!("MQTT Topic: {}", result.mqtt_topic);
            println!("Total Channels Extracted: {}", result.total_channels);
            
            println!("\n--- Sample Extracted Channels (First 10) ---");
            for (idx, ch) in result.channels.iter().take(10).enumerate() {
                println!("[{:02}] Zone: '{}' | Group: '{}' | Device: '{}' | Name: '{}' | Freq: {:.3} MHz",
                    idx + 1, ch.zone, ch.group, ch.device, ch.name, ch.freq_mhz);
            }
            println!("==========================");
        }
        Err(err) => {
            eprintln!("[IAS Test Runner] ERROR: {}", err);
        }
    }
}
