/**
 * Header: mod.rs
 * Purpose: mod.rs implementation.
 * Description: Logic and implementation for mod.rs implementation.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// oaFileImportCSV/Methods/oaCSVParser_rs/mod.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260413.1400.1
//
// Description: High-performance CSV parsing engine. Utilizes 
// Rust's type safety to validate and ingest large datasets 
// without Python-side overhead.

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use std::collections::HashMap;
use csv::ReaderBuilder;
use regex::Regex;

#[pyfunction]
// Inline comment: Logic for convert_csv_unknown
fn convert_csv_unknown(py: Python<'_>, file_path: String) -> PyResult<(Vec<String>, Py<PyList>)> {
    let standard_headers = vec!["ZONE", "GROUP", "DEVICE", "NAME", "FREQ_MHZ", "PEAK"];
    let mut header_aliases = HashMap::new();
    header_aliases.insert("zone", vec!["zone", "area", "location"]);
    header_aliases.insert("group", vec!["group", "channel_group"]);
    header_aliases.insert("device", vec!["device", "dev_type", "model"]);
    header_aliases.insert("name", vec!["name", "alias", "description"]);
    header_aliases.insert("freq_mhz", vec!["freq", "frequency", "frequency_mhz", "freq_mhz"]);
    header_aliases.insert("peak", vec!["peak", "peak_level", "max_level", "dbm"]);

    let mut reader = ReaderBuilder::new()
        .has_headers(true)
        .from_path(file_path)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;

    let headers: Vec<String> = reader.headers()
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?
        .iter()
        .map(|h| h.trim().to_lowercase())
        .collect();

    let mut header_map = HashMap::new();
    for std_header in &standard_headers {
        let std_key = std_header.to_lowercase();
        if let Some(aliases) = header_aliases.get(std_key.as_str()) {
            for alias in aliases {
                if let Some(position) = headers.iter().position(|h| h == alias) {
                    header_map.insert(*std_header, position);
                    break;
                }
            }
        }
    }

    let freq_regex = Regex::new(r"(?i)(?P<value>\d+(?:\.\d+)?)\s*(?:(?P<unit>k|m|g)?hz)?").unwrap();
    let parsed_records = PyList::empty_bound(py);

    for result in reader.records() {
        let record = result.map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
        let row_dict = PyDict::new_bound(py);

        for std_header in &standard_headers {
            let mut value_obj = py.None();
            if let Some(&index) = header_map.get(std_header) {
                if let Some(raw_value) = record.get(index) {
                    let trimmed = raw_value.trim();
                    if *std_header == "FREQ_MHZ" && !trimmed.is_empty() {
                        if let Some(caps) = freq_regex.captures(trimmed) {
                            let value: f64 = caps["value"].parse().unwrap_or(0.0);
                            let unit = caps.name("unit").map(|m| m.as_str().to_lowercase());
                            let mut mhz_val = value;
                            if let Some(u) = unit {
                                if u == "k" { mhz_val /= 1000.0; }
                                else if u == "g" { mhz_val *= 1000.0; }
                            }
                            value_obj = mhz_val.into_py(py);
                        } else {
                            if let Ok(value) = trimmed.parse::<f64>() {
                                value_obj = value.into_py(py);
                            } else {
                                value_obj = trimmed.into_py(py);
                            }
                        }
                    } else {
                        value_obj = trimmed.into_py(py);
                    }
                }
            }
            let _ = row_dict.set_item(std_header, value_obj);
        }
        let _ = parsed_records.append(row_dict);
    }

    let std_headers_vec: Vec<String> = standard_headers.iter().map(|s| s.to_string()).collect();
    Ok((std_headers_vec, parsed_records.unbind()))
}

#[pymodule]
// Inline comment: Logic for oacsvparser_rs
pub fn oacsvparser_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(convert_csv_unknown, m)?)?;
    Ok(())
}
