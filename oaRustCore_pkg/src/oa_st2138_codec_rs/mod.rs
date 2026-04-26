// oaComSMPTE2138/Methods/oaST2138Codec_rs/mod.rs
// Author: Anthony Peter Kuzub (via Gemini)
// Version: 20260413.1400.1
//
// Description: SMPTE ST 2138-1 Protocol Buffer codec. Provides 
// efficient serialization for constraint and device management 
// in NMOS environments.

use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict};
use prost::Message;
use std::collections::HashMap;

pub mod st2138 {
    include!(concat!(env!("OUT_DIR"), "/st2138.rs"));
}

#[pyclass]
struct St2138Codec;

#[pymethods]
impl St2138Codec {
    #[new]
    fn new() -> Self {
        St2138Codec
    }

    fn encode_parameter(&self, py: Python<'_>, name: String, _value_f32: f32) -> PyResult<Py<PyAny>> {
        let mut parameter = st2138::Param::default();
        let mut poly_text = st2138::PolyglotText::default();
        let mut display_strings = HashMap::new();
        display_strings.insert("en".to_string(), name);
        poly_text.display_strings = display_strings;
        parameter.name = Some(poly_text);
        parameter.r#type = st2138::ParamType::Float32 as i32;
        
        let mut buf = Vec::new();
        parameter.encode(&mut buf).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        
        Ok(PyBytes::new_bound(py, &buf).into())
    }

    fn decode_parameter<'py>(&self, py: Python<'py>, data: &[u8]) -> PyResult<Bound<'py, PyDict>> {
        let parameter = st2138::Param::decode(data).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        
        let dict = PyDict::new_bound(py);
        if let Some(name) = parameter.name {
            if let Some(en_text) = name.display_strings.get("en") {
                dict.set_item("name", en_text)?;
            } else {
                // Fallback to first available string if "en" is missing
                if let Some(first) = name.display_strings.values().next() {
                    dict.set_item("name", first)?;
                }
            }
        }
        dict.set_item("type", parameter.r#type)?;
        
        Ok(dict)
    }
}

#[pymodule]
pub fn oast2138codec_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<St2138Codec>()?;
    Ok(())
}
