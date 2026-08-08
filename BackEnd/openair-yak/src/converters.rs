use serde_json::{Value, Number};
use log::warn;

/// The one truth table for "is this payload on or off".
///
/// Shared with the SET verb, which needs the same answer to resolve a toggle
/// onto an `_ON`/`_OFF` command pair. Two copies of this would drift, and the
/// drift would be silent: a panel whose converter says ON while the command
/// resolver says OFF sends a command that contradicts the button.
pub fn as_bool(val: &Value) -> Option<bool> {
    match val {
        Value::Bool(b) => Some(*b),
        Value::Number(n) => n.as_f64().map(|f| f != 0.0),
        Value::String(s) => match s.trim().to_ascii_lowercase().as_str() {
            "1" | "true" | "on" | "yes" => Some(true),
            "0" | "false" | "off" | "no" => Some(false),
            _ => None,
        },
        _ => None,
    }
}

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
    let truthy = as_bool(val);
    match (converter.to_lowercase().as_str(), truthy) {
        // `bool_to_int` is a misnomer carried by 11 rows of
        // Instruments/Instrument functions.csv, and until now it matched
        // no arm here at all: it fell through to the numeric branch, where
        // "ON".as_f64() is None, and the value was passed through with a
        // warning. That was survivable only by accident — the GUI publishes the
        // string "ON"/"OFF", which is already valid SCPI. It mapped to nothing
        // the moment a toggle published `true` or `1`. Deliberately ON/OFF and
        // not 1/0 despite the name: ON/OFF is what those eleven controls have
        // been sending all along, so this fixes the missing conversion without
        // silently changing the bytes eleven working panels put on the wire.
        ("bool_on_off" | "bool_to_int", Some(b)) => return Value::String(if b { "ON" } else { "OFF" }.to_string()),
        ("bool_off_on", Some(b)) => return Value::String(if b { "OFF" } else { "ON" }.to_string()),
        ("bool_1_0", Some(b)) => return Value::String(if b { "1" } else { "0" }.to_string()),
        _ => {}
    }

    // A NUMBER-SHAPED STRING IS A NUMBER.
    //
    // `as_f64()` answers None for Value::String, so every converter silently did
    // nothing whenever the payload arrived quoted — and a toggler's options are
    // quoted by nature (`"value": "0.3"`), because JSON object values in a panel
    // are authored as text. The slider next to it published a bare 0.3 and
    // converted fine, so the same command with the same `mhz_to_hz` behaved
    // differently depending on which widget you touched: the fader sent
    // `:SENSe:BANDwidth:RESolution 300000` and the button sent `0.3` — the same
    // request off by a factor of a million, reaching real hardware as 0.3 Hz.
    //
    // Parsing here rather than at the call sites keeps one definition of "is
    // this numeric" for every converter and every widget type.
    let numeric = val.as_f64().or_else(|| match val {
        Value::String(s) => s.trim().parse::<f64>().ok(),
        _ => None,
    });

    match numeric {
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

#[cfg(test)]
mod bool_tests {
    use super::{apply_converter, as_bool};
    use serde_json::{json, Value};

    #[test]
    fn bool_to_int_converts_instead_of_falling_through() {
        // The spelling used by 11 rows of Instrument functions.csv. It matched no
        // arm at all until now: "ON" is not numeric, so it left through the
        // not-a-number branch unchanged and only looked correct because the GUI
        // already publishes SCPI-shaped strings.
        assert_eq!(apply_converter("bool_to_int", Some(&json!("ON"))), json!("ON"));
        assert_eq!(apply_converter("bool_to_int", Some(&json!("OFF"))), json!("OFF"));
        // The cases that used to escape as a bare `true` / `1`.
        assert_eq!(apply_converter("bool_to_int", Some(&json!(true))), json!("ON"));
        assert_eq!(apply_converter("bool_to_int", Some(&json!(1))), json!("ON"));
        assert_eq!(apply_converter("bool_to_int", Some(&json!(0))), json!("OFF"));
    }

    #[test]
    fn a_quoted_number_converts_like_a_bare_one() {
        // The N9340B bandwidth buttons: options are authored as JSON strings, so
        // the payload is "0.3" where the slider beside them sends 0.3. Before
        // this they diverged by a factor of a million on the wire.
        assert_eq!(apply_converter("mhz_to_hz", Some(&json!("0.3"))), json!(300000.0));
        assert_eq!(apply_converter("mhz_to_hz", Some(&json!(0.3))), json!(300000.0));
        assert_eq!(apply_converter("khz_to_hz", Some(&json!("300"))), json!(300000.0));
        assert_eq!(apply_converter("mhz_to_hz", Some(&json!(" 0.0003 "))), json!(300.0));
    }

    #[test]
    fn a_non_numeric_string_still_passes_through_untouched() {
        // Enum arguments and identity strings must not be mangled by a numeric
        // converter that was declared on the widget by mistake.
        assert_eq!(apply_converter("mhz_to_hz", Some(&json!("MAXimum"))), json!("MAXimum"));
    }

    #[test]
    fn every_shape_a_toggle_can_publish_reads_as_on_or_off() {
        // SET resolves an _ON/_OFF command pair from this, so a shape that reads
        // as None here is a button press that sends nothing.
        for on in [json!(true), json!(1), json!("1"), json!("on"), json!("ON"), json!(" yes ")] {
            assert_eq!(as_bool(&on), Some(true), "{on:?} should read as ON");
        }
        for off in [json!(false), json!(0), json!("0"), json!("off"), json!("OFF"), json!("no")] {
            assert_eq!(as_bool(&off), Some(false), "{off:?} should read as OFF");
        }
        // Not boolean-shaped: SET must fall through to its "not found" error
        // rather than guess a direction for a value it cannot read.
        assert_eq!(as_bool(&json!("10")), None);
        assert_eq!(as_bool(&Value::Null), None);
    }
}
