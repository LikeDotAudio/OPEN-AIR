// oaConfigurationManager/Methods/oaDebugToggler_rs/mod.rs
// Author: Gemini Architect
// Version: 20260413.1400.1
//
// Description: Project-wide debug state manager. Traverses the 
// source tree to toggle debug flags in Python modules via regex.

use std::fs;
use std::path::Path;
use walkdir::WalkDir;
use regex::Regex;
use pyo3::prelude::*;

/// Efficiently scans and toggles debug flags across the project.
#[pyfunction]
fn toggle_debug_flags_rs(project_root: String, target_state: bool) -> PyResult<bool> {
    let target_state_str = if target_state { "True" } else { "False" };
    // Pattern captures: LOCAL_DEBUG, BUILDER_DEBUG, or generic DEBUG assignments
    let pattern = Regex::new(r"(?m)^(\s*(?:LOCAL_|BUILDER_)?[A-Z_]*DEBUG\s*=\s*)(True|False)(.*)$").unwrap();
    
    let mut files_modified = 0;
    let mut _flags_changed = 0;

    let project_path = Path::new(&project_root);
    
    for entry in WalkDir::new(project_path)
        .into_iter()
        .filter_entry(|e| {
            let name = e.file_name().to_string_lossy();
            // Respect project boundaries and ignore hidden/temporary directories
            !name.starts_with('.') && 
            name != "venv" && 
            name != "node_modules" && 
            name != "__pycache__" && 
            name != "oaDataLogs"
        })
        .filter_map(|e| e.ok()) {
            
        let path = entry.path();
        if path.is_file() && path.extension().and_then(|s| s.to_str()) == Some("py") {
            let content = match fs::read_to_string(path) {
                Ok(c) => c,
                Err(_) => continue,
            };

            if !pattern.is_match(&content) {
                continue;
            }

            let mut replacements_in_file = 0;
            let new_content = pattern.replace_all(&content, |caps: &regex::Captures| {
                let current_value = &caps[2];
                if current_value != target_state_str {
                    replacements_in_file += 1;
                    format!("{}{}{}", &caps[1], target_state_str, &caps[3])
                } else {
                    caps[0].to_string()
                }
            });

            if replacements_in_file > 0 {
                if fs::write(path, new_content.to_string()).is_ok() {
                    files_modified += 1;
                    _flags_changed += replacements_in_file;
                }
            }
        }
    }

    Ok(files_modified > 0)
}

#[pymodule]
pub fn oadebugtoggler_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(toggle_debug_flags_rs, m)?)?;
    Ok(())
}
