use pyo3::prelude::*;
use regex::Regex;
use once_cell::sync::Lazy;

static RE_SANITIZE: Lazy<Regex> = Lazy::new(|| Regex::new(r"[^a-zA-Z0-9]").unwrap());
static RE_UNDERSCORES: Lazy<Regex> = Lazy::new(|| Regex::new(r"_{2,}").unwrap());
static RE_DIGITS: Lazy<Regex> = Lazy::new(|| Regex::new(r"\d+").unwrap());

#[pyfunction]
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
fn midi_to_topic(dev_id: String, msg_type: String, channel: u8, note_or_cc: u8, value: u8) -> PyResult<(String, u8)> {
    let base = format!("OPEN-AIR/MIDI/{}/ch{}", dev_id, channel);
    
    match msg_type.as_str() {
        "control_change" => Ok((format!("{}/cc{}", base, note_or_cc), value)),
        "note_on" => Ok((format!("{}/note{}", base, note_or_cc), value)),
        "note_off" => Ok((format!("{}/note{}", base, note_or_cc), 0)),
        _ => Ok((format!("{}/{}", base, msg_type), 0)),
    }
}

#[pyfunction]
fn parse_channel_and_val(topic_part: String) -> PyResult<u8> {
    if let Some(caps) = RE_DIGITS.find(&topic_part) {
        if let Ok(val) = caps.as_str().parse::<u8>() {
            return Ok(val);
        }
    }
    Ok(0)
}

#[pymodule]
fn oamidimapper_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(sanitize_id, m)?)?;
    m.add_function(wrap_pyfunction!(midi_to_topic, m)?)?;
    m.add_function(wrap_pyfunction!(parse_channel_and_val, m)?)?;
    Ok(())
}
