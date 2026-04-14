// oaStand_Alone_Utilities/Methods/oaLogAligner_rs/mod.rs
// Author: Gemini Iron Oxide Architect
// Version: 20260413.1400.1
//
// Description: Library interface for log realignment. Provides high-performance 
// regex-based timestamp extraction and parallel sorting for system-wide 
// forensic reconstruction.

use pyo3::prelude::*;
use std::fs::File;
use std::io::{BufRead, BufReader, Write};
use std::path::Path;
use rayon::prelude::*;
use regex::Regex;

#[pyclass]
struct LogAligner;

#[pymethods]
impl LogAligner {
    #[new]
    fn new() -> Self {
        LogAligner
    }

    /// Realigns logs from a directory into a single sorted file.
    fn realign(&self, input_dir: String, output_file: String) -> PyResult<usize> {
        let input_path = Path::new(&input_dir);
        if !input_path.is_dir() {
            return Err(pyo3::exceptions::PyNotADirectoryError::new_err(input_dir));
        }

        let entries: Vec<_> = std::fs::read_dir(input_path)?
            .filter_map(|res| res.ok())
            .filter(|e| e.path().extension().map_or(false, |ext| ext == "log"))
            .collect();

        let re = Regex::new(r"^(?P<timestamp>\d+\.\d+)\s+\|").map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Regex error: {}", e))
        })?;

        let mut all_lines: Vec<(f64, String)> = entries.par_iter().map(|entry| {
            let mut lines = Vec::new();
            if let Ok(file) = File::open(entry.path()) {
                let reader = BufReader::new(file);
                for line_res in reader.lines() {
                    if let Ok(line) = line_res {
                        if let Some(caps) = re.captures(&line) {
                            if let Some(ts_match) = caps.name("timestamp") {
                                if let Ok(timestamp) = ts_match.as_str().parse::<f64>() {
                                    lines.push((timestamp, line));
                                }
                            }
                        }
                    }
                }
            }
            lines
        }).flatten().collect();

        // Sort by timestamp
        all_lines.par_sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap_or(std::cmp::Ordering::Equal));

        let line_count = all_lines.len();
        let mut out_file = File::create(output_file)?;
        for (_, line) in all_lines {
            writeln!(out_file, "{}", line)?;
        }

        Ok(line_count)
    }
}

#[pymodule]
pub fn oalogaligner_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<LogAligner>()?;
    Ok(())
}
