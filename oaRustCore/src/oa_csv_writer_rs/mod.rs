// oaFileExportCSV/Methods/oaCSVWriter-rs/src/lib.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260331.2220.2

use pyo3::prelude::*;
use pyo3::types::{PyList, PyDict};
use std::thread;

#[pyfunction]
fn dump_async(py: Python<'_>, data: Bound<'_, PyList>, filepath: String) -> PyResult<()> {
    // Extract data from Python list of dicts to Rust Vec of Vec of Strings
    let mut headers = Vec::new();
    let mut rows = Vec::new();
    
    for (i, item) in data.iter().enumerate() {
        if let Ok(dict) = item.downcast::<PyDict>() {
            if i == 0 {
                for key in dict.keys() {
                    headers.push(key.to_string());
                }
            }
            
            let mut row = Vec::new();
            for key in &headers {
                if let Ok(val) = dict.get_item(key) {
                    if let Some(v) = val {
                        row.push(v.to_string());
                    } else {
                        row.push("".to_string());
                    }
                } else {
                    row.push("".to_string());
                }
            }
            rows.push(row);
        }
    }

    // Spawn a thread to handle writing without the GIL
    thread::spawn(move || {
        if let Ok(mut writer) = csv::Writer::from_path(&filepath) {
            let _ = writer.write_record(&headers);
            for row in rows {
                let _ = writer.write_record(&row);
            }
            let _ = writer.flush();
        }
    });
    
    Ok(())
}

#[pymodule]
fn oacsvwriter_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(dump_async, m)?)?;
    Ok(())
}
