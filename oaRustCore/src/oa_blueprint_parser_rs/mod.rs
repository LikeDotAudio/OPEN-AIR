use pyo3::prelude::*;

#[pyclass(name = "BlueprintParser")]
struct BlueprintParser;

#[pymethods]
impl BlueprintParser {
    #[new]
    fn new() -> Self {
        BlueprintParser
    }
}

#[pymodule]
pub fn oablueprintparser_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<BlueprintParser>()?;
    m.add("__all__", vec!["BlueprintParser"])?;
    Ok(())
}
