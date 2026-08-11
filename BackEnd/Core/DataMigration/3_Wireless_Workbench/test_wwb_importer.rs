//! Standalone Test Runner for WWB Importer & MQTT pipeline.

use std::path::Path;

mod wwb_importer;

fn main() {
    let report_path = "/home/anthony/Documents/GitProjects/OPEN-AIR/BackEnd/Core/DataMigration/3_Wireless_Workbench/test_data/venue.shw";
    println!("[WWB Test Runner] Testing standalone Wireless Workbench Importer with file: {}", report_path);

    match wwb_importer::parse_wwb_file(Path::new(report_path)) {
        Ok(result) => {
            println!("\n=== WWB PARSE SUCCESS ===");
            println!("Status: {}", result.status);
            println!("Source Format: {}", result.source_format);
            println!("MQTT Topic: {}", result.mqtt_topic);
            println!("Total Channels Extracted: {}", result.total_channels);
            
            println!("\n--- Sample Extracted WWB Channels (First 15) ---");
            for (idx, ch) in result.channels.iter().take(15).enumerate() {
                println!("[{:02}] Dev: '{}' | Model: '{}' | Band: '{}' | Ch #{}: '{}' | Freq: {:.3} MHz",
                    idx + 1, ch.device_name, ch.model, ch.band, ch.channel_number, ch.channel_name, ch.frequency_mhz);
            }
            println!("===============================================");
        }
        Err(err) => {
            eprintln!("[WWB Test Runner] ERROR: {}", err);
        }
    }
}
