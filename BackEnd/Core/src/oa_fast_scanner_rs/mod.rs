/**
 * Header: mod.rs
 * Purpose: mod.rs implementation.
 * Description: Logic and implementation for mod.rs implementation.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// oaGuiManager/Core/oaFastScanner_rs/mod.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260413.1400.1
//
// Description: Native GUI resource scanner. Locates and indexes 
// icons, fonts, and stylesheets to accelerate application startup.

use pyo3::prelude::*;
use walkdir::WalkDir;
use std::path::Path;

#[pyclass]
struct FastScanner;

#[pymethods]
impl FastScanner {
    #[new]
    fn new() -> Self {
        FastScanner
    }

    /// Scans a directory recursively for files matching a suffix.
    fn scan_directory(&self, root_path: String, suffix: String) -> Vec<String> {
        let mut results = Vec::new();
        for entry in WalkDir::new(root_path).into_iter().filter_map(|e| e.ok()) {
            if entry.file_type().is_file() {
                let path = entry.path();
                if let Some(s) = path.to_str() {
                    if s.ends_with(&suffix) {
                        results.push(s.to_string());
                    }
                }
            }
        }
        results
    }
}

#[pymodule]
// Inline comment: Logic for oafastscanner_rs
pub fn oafastscanner_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<FastScanner>()?;
    Ok(())
}
