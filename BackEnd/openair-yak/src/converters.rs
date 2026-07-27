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
