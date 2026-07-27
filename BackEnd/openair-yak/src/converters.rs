use serde_json::{Value, Number};
use log::warn;

pub fn apply_converter(converter: &str, val: Option<&Value>) -> Value {
    let val = match val {
        Some(v) => v,
        None => return Value::Null,
    };

    if converter.is_empty() {
        return val.clone();
    }

    // Boolean-shaped converters run BEFORE the numeric branch: a GUI toggle
    // publishes 1/0 (or true/false), and SCPI wants a keyword. Without these a
    // toggle sends `:SENSe:VOLTage:DC:RANGe:AUTO 1`, which an HP 34401A rejects
    // as a syntax error — the panel looks wired and the instrument disagrees.
    let truthy = match val {
        Value::Bool(b) => Some(*b),
        Value::Number(n) => n.as_f64().map(|f| f != 0.0),
        Value::String(s) => match s.trim().to_ascii_lowercase().as_str() {
            "1" | "true" | "on" | "yes" => Some(true),
            "0" | "false" | "off" | "no" => Some(false),
            _ => None,
        },
        _ => None,
    };
    match (converter.to_lowercase().as_str(), truthy) {
        ("bool_on_off", Some(b)) => return Value::String(if b { "ON" } else { "OFF" }.to_string()),
        ("bool_off_on", Some(b)) => return Value::String(if b { "OFF" } else { "ON" }.to_string()),
        ("bool_1_0", Some(b)) => return Value::String(if b { "1" } else { "0" }.to_string()),
        _ => {}
    }

    match val.as_f64() {
        Some(num) => {
            let converted = match converter.to_lowercase().as_str() {
                "mhz_to_hz" => num * 1_000_000.0,
                "hz_to_mhz" => num / 1_000_000.0,
                "khz_to_hz" => num * 1_000.0,
                "hz_to_khz" => num / 1_000.0,
                "v_to_mv"   => num * 1_000.0,
                "mv_to_v"   => num / 1_000.0,
                _ => {
                    warn!("Unknown converter '{}'. Passing value through unchanged.", converter);
                    num
                }
            };
            
            // Convert back to serde_json::Value
            if let Some(n) = Number::from_f64(converted) {
                Value::Number(n)
            } else {
                Value::Null
            }
        },
        None => {
            // If the value is a string, bool, object, etc., and a converter was specified,
            // we can't do math on it. Just pass it through with a warning.
            warn!("Value is not numeric, cannot apply mathematical converter '{}'.", converter);
            val.clone()
        }
    }
}
