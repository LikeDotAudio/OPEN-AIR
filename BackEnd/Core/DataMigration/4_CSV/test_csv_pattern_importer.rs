//! Standalone Test Runner for CSV Pattern Recognition & MQTT pipeline.

use std::path::Path;

mod csv_importer;

fn main() {
    let test_files = vec![
        "/home/anthony/Documents/GitProjects/OPEN-AIR/BackEnd/Core/DataMigration/4_CSV/test_data/report_converted.csv",
        "/home/anthony/Documents/GitProjects/OPEN-AIR/BackEnd/Core/DataMigration/4_CSV/test_data/report.csv",
        "/home/anthony/Documents/GitProjects/OPEN-AIR/BackEnd/Core/DataMigration/4_CSV/test_data/SB PDF.csv",
        "/home/anthony/Documents/GitProjects/OPEN-AIR/BackEnd/Core/DataMigration/4_CSV/test_data/venue_converted.csv",
        "/home/anthony/Documents/GitProjects/OPEN-AIR/BackEnd/Core/DataMigration/4_CSV/test_data/venue_data.csv",
        "/home/anthony/Documents/GitProjects/OPEN-AIR/BackEnd/Core/DataMigration/4_CSV/test_data/venue.csv",
    ];

    println!("=== SMART CSV PATTERN RECOGNITION TEST RUNNER ===");

    for file_path in test_files {
        let path = Path::new(file_path);
        let filename = path.file_name().unwrap_or_default().to_string_lossy();
        println!("\nTesting File: '{}'", filename);

        match csv_importer::parse_and_classify_csv(path) {
            Ok(res) => {
                println!("  └─ Recognized Pattern: [{}]", res.pattern_name);
                println!("  └─ Total Records Extracted: {}", res.total_records);
                println!("  └─ MQTT Topic: {}", res.mqtt_topic);

                if let Some(sample) = res.records.first() {
                    println!("  └─ Sample Record: Zone='{}' | Group='{}' | Device='{}' | Freq={:.3} MHz",
                        sample.zone, sample.group, sample.device, sample.frequency_mhz);
                }
            }
            Err(e) => {
                eprintln!("  └─ ERROR: {}", e);
            }
        }
    }
    println!("\n=================================================");
}
