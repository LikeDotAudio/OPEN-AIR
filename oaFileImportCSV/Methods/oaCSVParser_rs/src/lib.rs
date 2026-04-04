// oaFileImportCSV/Methods/oaCSVParser_rs/src/lib.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260402.0010.1

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use pyo3::IntoPyAnyExt;
use std::collections::HashMap;
use csv::ReaderBuilder;
use regex::Regex;

#[pyfunction]
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
                if let Some(pos) = headers.iter().position(|h| h == alias) {
                    header_map.insert(*std_header, pos);
                    break;
                }
            }
        }
    }

    let freq_regex = Regex::new(r"(?i)(?P<val>\d+(?:\.\d+)?)\s*(?:(?P<unit>k|m|g)?hz)?").unwrap();
    let processed_data = PyList::empty(py);

    for result in reader.records() {
        let record = result.map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
        let row_dict = PyDict::new(py);

        for std_header in &standard_headers {
            let mut value_obj = py.None();
            if let Some(&index) = header_map.get(std_header) {
                if let Some(raw_value) = record.get(index) {
                    let trimmed = raw_value.trim();
                    if *std_header == "FREQ_MHZ" && !trimmed.is_empty() {
                        if let Some(caps) = freq_regex.captures(trimmed) {
                            let val: f64 = caps["val"].parse().unwrap_or(0.0);
                            let unit = caps.name("unit").map(|m| m.as_str().to_lowercase());
                            let mut mhz_val = val;
                            if let Some(u) = unit {
                                if u == "k" { mhz_val /= 1000.0; }
                                else if u == "g" { mhz_val *= 1000.0; }
                            }
                            value_obj = mhz_val.into_py_any(py)?;
                        } else {
                            if let Ok(val) = trimmed.parse::<f64>() {
                                value_obj = val.into_py_any(py)?;
                            } else {
                                value_obj = trimmed.into_py_any(py)?;
                            }
                        }
                    } else {
                        value_obj = trimmed.into_py_any(py)?;
                    }
                }
            }
            let _ = row_dict.set_item(std_header, value_obj);
        }
        let _ = processed_data.append(row_dict);
    }

    let std_headers_vec: Vec<String> = standard_headers.iter().map(|s| s.to_string()).collect();
    Ok((std_headers_vec, processed_data.unbind()))
}

#[pyfunction]
fn sum_as_string(a: usize, b: usize) -> PyResult<String> {
    Ok((a + b).to_string())
}

#[pymodule]
fn oacsvparser_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(convert_csv_unknown, m)?)?;
    m.add_function(wrap_pyfunction!(sum_as_string, m)?)?;
    Ok(())
}
