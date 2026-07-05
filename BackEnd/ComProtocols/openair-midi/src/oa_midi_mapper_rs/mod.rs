/**
 * Header: mod.rs
 * Purpose: mod.rs implementation.
 * Description: Logic and implementation for mod.rs implementation.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// oaComMidi/Methods/oaMidiMapper_rs/mod.rs
// Author: Gemini Architect
// Version: 20260413.1400.1
//
// Description: MIDI parameter mapping engine. Translates raw 
// MIDI control changes and notes into OPEN-AIR state topic updates.

use pyo3::prelude::*;
use regex::Regex;
use once_cell::sync::Lazy;

static RE_SANITIZE: Lazy<Regex> = Lazy::new(|| Regex::new(r"[^a-zA-Z0-9]").unwrap());
static RE_UNDERSCORES: Lazy<Regex> = Lazy::new(|| Regex::new(r"_{2,}").unwrap());
static RE_DIGITS: Lazy<Regex> = Lazy::new(|| Regex::new(r"\d+").unwrap());

#[pyfunction]
// Inline comment: Logic for sanitize_id
fn sanitize_id(port_name: Option<String>) -> PyResult<String> {
    let name = match port_name {
        Some(n) => n,
        None => return Ok("unknown_device".to_string()),
    };

    // Split ALSA style colon if present
    let name_part = name.split(':').next().unwrap_or(&name);
    
    // Replace non-alphanumeric with underscore
    let sanitized = RE_SANITIZE.replace_all(name_part, "_").to_lowercase();
    
    // Collapse multiple underscores and trim
    let collapsed = RE_UNDERSCORES.replace_all(&sanitized, "_");
    let result = collapsed.trim_matches('_').to_string();
    
    if result.is_empty() {
        Ok("unknown".to_string())
    } else {
        Ok(result)
    }
}

#[pyfunction]
// Inline comment: Logic for midi_to_topic
fn midi_to_topic(dev_id: String, message_type: String, channel: u8, note_or_cc: u8, value: u8) -> PyResult<(String, u8)> {
    let base = format!("OPEN-AIR/MIDI/{}/ch{}", dev_id, channel);
    
    match message_type.as_str() {
        "control_change" => Ok((format!("{}/cc{}", base, note_or_cc), value)),
        "note_on" => Ok((format!("{}/note{}", base, note_or_cc), value)),
        "note_off" => Ok((format!("{}/note{}", base, note_or_cc), 0)),
        _ => Ok((format!("{}/{}", base, message_type), 0)),
    }
}

#[pyfunction]
// Inline comment: Logic for parse_channel_and_val
fn parse_channel_and_val(topic_part: String) -> PyResult<u8> {
    if let Some(caps) = RE_DIGITS.find(&topic_part) {
        if let Ok(value) = caps.as_str().parse::<u8>() {
            return Ok(value);
        }
    }
    Ok(0)
}

#[pymodule]
// Inline comment: Logic for oamidimapper_rs
pub fn oamidimapper_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(sanitize_id, m)?)?;
    m.add_function(wrap_pyfunction!(midi_to_topic, m)?)?;
    m.add_function(wrap_pyfunction!(parse_channel_and_val, m)?)?;
    Ok(())
}
