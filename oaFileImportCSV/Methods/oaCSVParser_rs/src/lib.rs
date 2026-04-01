// oaFileImportCSV/Methods/oaCSVParser-rs/src/lib.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260331.2150.2

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use std::collections::HashMap;
use csv::ReaderBuilder;
use regex::Regex;
use polars::prelude::*;

#[pyfunction]
fn load_large_csv(py: Python<'_>, file_path: String) -> PyResult<PyObject> {
    let df = CsvReadOptions::default()
        .with_has_header(true)
        .try_into_reader_with_file_path(Some(file_path.into()))
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?
        .finish()
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

    let height = df.height();
    let columns = df.get_column_names();
    let list = PyList::empty_bound(py);
    
    for i in 0..height {
        let dict = PyDict::new_bound(py);
        for col_name in &columns {
            let series = df.column(col_name).unwrap();
            let val = series.get(i).unwrap();
            match val {
                AnyValue::String(s) => { let _ = dict.set_item(col_name.to_string(), s); },
                AnyValue::Int64(v) => { let _ = dict.set_item(col_name.to_string(), v); },
                AnyValue::Float64(v) => { let _ = dict.set_item(col_name.to_string(), v); },
                AnyValue::Boolean(v) => { let _ = dict.set_item(col_name.to_string(), v); },
                _ => { let _ = dict.set_item(col_name.to_string(), val.to_string()); },
            }
        }
        let _ = list.append(dict);
    }
    
    Ok(list.into())
}

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
    let processed_data = PyList::empty_bound(py);

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
                            let val: f64 = caps["val"].parse().unwrap_or(0.0);
                            let unit = caps.name("unit").map(|m| m.as_str().to_lowercase());
                            let mut mhz_val = val;
                            if let Some(u) = unit {
                                if u == "k" { mhz_val /= 1000.0; }
                                else if u == "g" { mhz_val *= 1000.0; }
                            }
                            value_obj = mhz_val.into_py(py);
                        } else {
                            if let Ok(val) = trimmed.parse::<f64>() {
                                value_obj = val.into_py(py);
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
        let _ = processed_data.append(row_dict);
    }

    let std_headers_vec: Vec<String> = standard_headers.iter().map(|s| s.to_string()).collect();
    Ok((std_headers_vec, processed_data.unbind()))
}

#[pymodule]
fn oacsvparser_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(convert_csv_unknown, m)?)?;
    m.add_function(wrap_pyfunction!(load_large_csv, m)?)?;
    Ok(())
}
