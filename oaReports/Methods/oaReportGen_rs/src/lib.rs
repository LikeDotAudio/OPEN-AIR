// oaReports/Methods/oaReportGen-rs/src/lib.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260331.2350.1

use pyo3::prelude::*;
use printpdf::*;
use std::fs::File;
use std::io::BufWriter;

#[pyfunction]
fn build_pdf(json_schema: String, output_path: String) -> PyResult<()> {
    let schema: serde_json::Value = serde_json::from_str(&json_schema).map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
    
    let title = schema["title"].as_str().unwrap_or("OPEN-AIR Report");
    
    let (doc, page1, layer1) = PdfDocument::new(title, Mm(210.0), Mm(297.0), "Layer 1");
    let current_layer = doc.get_page(page1).get_layer(layer1);

    // Load a font (using a system font would be better, but for POC we'll use a built-in if available or just basic shapes)
    // printpdf doesn't have built-in fonts, we need to load one or use basic shapes.
    // For Phase 2 verification, we'll just draw a rectangle and some text placeholder logic.
    
    current_layer.set_fill_color(Color::Rgb(Rgb::new(0.0, 0.0, 0.0, None)));
    // current_layer.use_text(...) requires a font. 
    
    let mut file = BufWriter::new(File::create(output_path).map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?);
    doc.save(&mut file).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

    Ok(())
}

#[pymodule]
fn oareportgen_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(build_pdf, m)?)?;
    Ok(())
}
