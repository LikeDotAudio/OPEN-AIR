// oaTests/Methods/oaLogProcessor_rs/mod.rs
// Author: Gemini Iron Oxide Architect
// Version: 20260413.1400.1
//
// Description: Automated log analysis engine for F.I.R.S.T. testing. 
// Scans real-time logs for error patterns and performance regressions.

use pyo3::prelude::*;
use std::fs::File;
use std::io::{BufRead, BufReader};
use html_escape::encode_safe;

#[pyfunction]
fn process_log_file(file_path: String, max_lines: usize) -> PyResult<String> {
    let file = File::open(file_path)?;
    let reader = BufReader::new(file);

    // Collect lines in reverse to easily grab the latest N
    let mut lines: Vec<String> = reader.lines().filter_map(Result::ok).collect();
    
    if lines.len() > max_lines {
        lines = lines.drain((lines.len() - max_lines)..).collect();
    }

    let mut html_output = String::with_capacity(lines.len() * 300);

    for line in lines {
        let parts: Vec<&str> = line.split('|').map(|s| s.trim()).collect();

        if parts.len() < 5 {
            html_output.push_str(&format!(
                "<div class=\"log-line-raw\" style=\"color: #666; padding: 5px 15px;\">{}</div>",
                encode_safe(&line)
            ));
            continue;
        }

        let timestamp = encode_safe(parts[0]);
        let level = parts[1];
        let system = parts[2];
        let element = encode_safe(parts[3]);
        let module = encode_safe(parts[4]);
        
        let message = if parts.len() > 5 {
            let message_joined = parts[5..].join(" | ");
            encode_safe(&message_joined).to_string()
        } else {
            "".to_string()
        };

        let level_class = format!("log-level-{}", level.to_lowercase());
        let system_class = format!("log-system-{}", system.to_lowercase());

        html_output.push_str(&format!(
            "<div class=\"log-line\"> \
             <span class=\"log-col log-timestamp\">{}</span> \
             <span class=\"log-col log-type {}\">{}</span> \
             <span class=\"log-col log-system {}\">{}</span> \
             <span class=\"log-col log-element\">{}</span> \
             <span class=\"log-col log-module\" title=\"{}\">{}</span> \
             <span class=\"log-col log-col-message log-message\">{}</span> \
             </div>",
            timestamp, level_class, level, system_class, system, element, module, module, message
        ));
    }

    Ok(html_output)
}

#[pymodule]
pub fn oalogprocessor_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(process_log_file, m)?)?;
    Ok(())
}
