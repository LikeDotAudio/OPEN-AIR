// oaFileImportHTML/Methods/oaHTMLScraper-rs/src/lib.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260331.2250.1

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use scraper::{Html, Selector};

#[pyfunction]
fn scrape_tables(py: Python<'_>, html_content: String) -> PyResult<PyObject> {
    let document = Html::parse_document(&html_content);
    let table_selector = Selector::parse("table").unwrap();
    let row_selector = Selector::parse("tr").unwrap();
    let cell_selector = Selector::parse("th, td").unwrap();

    let all_tables = PyList::empty_bound(py);

    for table in document.select(&table_selector) {
        let mut headers = Vec::new();
        let rows_list = PyList::empty_bound(py);
        
        for (i, row) in table.select(&row_selector).enumerate() {
            let cells: Vec<_> = row.select(&cell_selector).collect();
            if cells.is_empty() { continue; }

            if i == 0 {
                // Assume first row is headers
                for cell in cells {
                    headers.push(cell.text().collect::<Vec<_>>().join(" ").trim().to_string());
                }
            } else {
                let row_dict = PyDict::new_bound(py);
                for (j, cell) in cells.iter().enumerate() {
                    let text = cell.text().collect::<Vec<_>>().join(" ").trim().to_string();
                    let header = headers.get(j).cloned().unwrap_or_else(|| format!("col_{}", j));
                    let _ = row_dict.set_item(header, text);
                }
                let _ = rows_list.append(row_dict);
            }
        }
        let _ = all_tables.append(rows_list);
    }

    Ok(all_tables.into())
}

#[pymodule]
fn oahtmlscraper_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(scrape_tables, m)?)?;
    Ok(())
}
