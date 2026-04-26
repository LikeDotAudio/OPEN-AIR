// oaStand_Alone_Utilities/Methods/oaLogAligner_rs/main.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260413.0010.1
//
// Description: High-performance log realignment utility. Ingests fragmented 
// log files from multiple subsystems, extracts UTP timestamps via regex, 
// and performs a stable sort to reconstruct a chronologically accurate 
// system-wide forensic trace.

use clap::Parser;
use regex::Regex;
use std::fs::File;
use std::io::{self, BufRead, BufReader, BufWriter, Write};
use std::path::PathBuf;
use walkdir::WalkDir;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Directory containing .log files
    #[arg(short, long)]
    dir: PathBuf,

    /// Output file name
    #[arg(short, long, default_value = "realigned_logs.log")]
    output: PathBuf,
}

struct LogLine {
    timestamp: f64,
    content: String,
}

fn main() -> io::Result<()> {
    let args = Args::parse();
    
    // The standardized OPEN-AIR log pattern uses a leading float timestamp (UTP).
    // We only capture the timestamp here as it is the primary sort key.
    let log_pattern = Regex::new(r"^(?P<timestamp>\d+\.\d+)\s+\|\s+").unwrap();

    let mut all_log_lines: Vec<LogLine> = Vec::new();

    println!("📡📥📥 [INBOUND] Scanning directory: {:?}", args.dir);

    for entry in WalkDir::new(&args.dir).max_depth(1) {
        let entry = entry?;
        // Only process .log files to avoid ingesting binary artifacts or reports.
        if entry.path().extension().and_then(|s| s.to_str()) == Some("log") {
            let file = File::open(entry.path())?;
            let reader = BufReader::new(file);

            for line in reader.lines() {
                let line = line?;
                if line.is_empty() {
                    continue;
                }

                if let Some(caps) = log_pattern.captures(&line) {
                    if let Ok(timestamp) = caps["timestamp"].parse::<f64>() {
                        all_log_lines.push(LogLine {
                            timestamp: timestamp,
                            content: line,
                        });
                    }
                }
            }
        }
    }

    println!("📡 [PROCESS] Sorting {} log lines...", all_log_lines.len());
    // Stable sort by timestamp reconstructs the system-wide event timeline.
    all_log_lines.sort_by(|a, b| a.timestamp.partial_cmp(&b.timestamp).unwrap_or(std::cmp::Ordering::Equal));

    println!("📡📤📤 [OUTBOUND] Writing to: {:?}", args.output);
    let out_file = File::create(&args.output)?;
    let mut writer = BufWriter::new(out_file);

    for log_line in all_log_lines {
        writer.write_all(log_line.content.as_bytes())?;
        writer.write_all(b"\n")?;
    }
    
    writer.flush()?;
    println!("📡 Successfully realigned logs.");

    Ok(())
}
