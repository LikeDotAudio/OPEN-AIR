// oaConfigurationManager/Methods/oaConfigEngine_rs/src/lib.rs
// Author: Gemini Iron Oxide Architect
// Version: 20260402.0010.1

use pyo3::prelude::*;
use pyo3::types::PyDict;
use serde::{Deserialize, Serialize};
use validator::Validate;

#[derive(Debug, Serialize, Deserialize, Validate)]
struct AppConfig {
    #[validate(length(min = 1))]
    partition_id: String,
    #[validate(range(min = 1024, max = 65535))]
    mqtt_port: u16,
    #[validate(length(min = 1))]
    mqtt_broker: String,
}

#[pyclass]
struct ConfigValidator;

#[pymethods]
impl ConfigValidator {
    #[new]
    fn new() -> Self {
        ConfigValidator
    }

    /// Validates a configuration dictionary against the strict schema.
    fn validate_config(&self, config_dict: &Bound<'_, PyDict>) -> PyResult<bool> {
        let mqtt_port: u16 = config_dict.get_item("mqtt_port")?.and_then(|v| v.extract().ok()).unwrap_or(1883);
        let mqtt_broker: String = config_dict.get_item("mqtt_broker")?.and_then(|v| v.extract().ok()).unwrap_or_default();
        let partition_id: String = config_dict.get_item("partition_id")?.and_then(|v| v.extract().ok()).unwrap_or_default();

        let cfg = AppConfig {
            partition_id,
            mqtt_port,
            mqtt_broker,
        };

        match cfg.validate() {
            Ok(_) => Ok(true),
            Err(e) => Err(pyo3::exceptions::PyValueError::new_err(format!("Config validation failed: {}", e))),
        }
    }
}

#[pymodule]
pub fn oaconfigengine_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<ConfigValidator>()?;
    Ok(())
}
