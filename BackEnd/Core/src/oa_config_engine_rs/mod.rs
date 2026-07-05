/**
 * Header: mod.rs
 * Purpose: mod.rs implementation.
 * Description: Logic and implementation for mod.rs implementation.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// oaConfigurationManager/Methods/oaConfigEngine_rs/mod.rs
// Author: Gemini Iron Oxide Architect
// Version: 20260413.0010.1
//
// Description: Native configuration validation engine. Uses Rust's strict 
// typing and the `validator` crate to enforce schema compliance for 
// the global `config.ini` parameters. This prevents invalid network 
// ports or partition IDs from entering the system during bootstrap.

use pyo3::prelude::*;
use pyo3::types::PyDict;
use serde::{Deserialize, Serialize};
use validator::Validate;

const MQTT_DEFAULT_PORT: u16 = 1883;

// AppConfig defines the strict structural and numerical bounds for 
// the core system parameters. 
#[derive(Debug, Serialize, Deserialize, Validate)]
struct AppConfig {
    #[validate(length(min = 1))]
    partition_id: String,
    // Port range validation ensures the application doesn't attempt 
    // to bind to reserved or invalid TCP/UDP ranges.
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

    // validate_config performs a two-stage check:
    // 1. Extraction: Pulls raw Python types and converts them to native Rust types.
    // 2. Bound Checking: Executes macro-based validation (e.g., range and length).
    fn validate_config(&self, config_dict: &Bound<'_, PyDict>) -> PyResult<bool> {
        let mqtt_port: u16 = config_dict.get_item("mqtt_port")?.and_then(|v| v.extract().ok()).unwrap_or(MQTT_DEFAULT_PORT);
        let mqtt_broker: String = config_dict.get_item("mqtt_broker")?.and_then(|v| v.extract().ok()).unwrap_or_default();
        let partition_id: String = config_dict.get_item("partition_id")?.and_then(|v| v.extract().ok()).unwrap_or_default();

        let configuration = AppConfig {
            partition_id,
            mqtt_port,
            mqtt_broker,
        };

        // Failure results in a PyValueError, preventing the system from 
        // proceeding with dangerous or illogical settings.
        match configuration.validate() {
            Ok(_) => Ok(true),
            Err(e) => Err(pyo3::exceptions::PyValueError::new_err(format!("Config validation failed: {}", e))),
        }
    }
}

#[pymodule]
// Inline comment: Logic for oaconfigengine_rs
pub fn oaconfigengine_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<ConfigValidator>()?;
    Ok(())
}
