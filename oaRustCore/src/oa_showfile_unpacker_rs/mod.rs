// oaFileImportShow/Methods/oaShowfileUnpacker-rs/src/lib.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260331.2320.1

use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::fs::File;
use std::io::Read;
use zip::ZipArchive;

#[pyfunction]
fn unpack_showfile(py: Python<'_>, file_path: String) -> PyResult<Py<PyAny>> {
    let file = File::open(&file_path).map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
    let mut archive = ZipArchive::new(file).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

    let dict = PyDict::new(py);

    for i in 0..archive.len() {
        let mut file = archive.by_index(i).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        let name = file.name().to_string();
        
        if name.ends_with(".json") {
            let mut contents = String::new();
            file.read_to_string(&mut contents).map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
            
            if let Ok(json_val) = serde_json::from_str::<serde_json::Value>(&contents) {
                // Convert serde_json to python dict would be complex here, 
                // for now let's just put the string or use a helper.
                let _ = dict.set_item(name, contents);
            }
        }
    }

    Ok(dict.into())
}

#[pymodule]
pub fn oashowfileunpacker_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(unpack_showfile, m)?)?;
    Ok(())
}
