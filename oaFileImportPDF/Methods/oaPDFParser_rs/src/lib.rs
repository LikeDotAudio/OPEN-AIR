// oaFileImportPDF/Methods/oaPDFParser_rs/src/lib.rs
// Author: Gemini Iron Oxide Architect
// Version: 20260402.0010.1
//
// Description: High-performance PDF text extraction engine for SoundBase reports.

use pyo3::prelude::*;
use pyo3::exceptions::PyRuntimeError;
use pdf_extract::*;
use std::path::Path;

#[pyclass]
struct PDFEngine;

#[pymethods]
impl PDFEngine {
    #[new]
    fn new() -> Self {
        PDFEngine
    }

    /// Extracts all text from a PDF file using high-speed native buffers.
    fn extract_text(&self, filepath: String) -> PyResult<String> {
        let path = Path::new(&filepath);
        if !path.exists() {
            return Err(PyRuntimeError::new_err(format!("File not found: {}", filepath)));
        }

        match extract_text(path) {
            Ok(text) => Ok(text),
            Err(e) => Err(PyRuntimeError::new_err(format!("PDF Extraction failed: {}", e))),
        }
    }
}

#[pymodule]
fn oapdfparser_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PDFEngine>()?;
    Ok(())
}
