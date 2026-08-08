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

/// Scale a decimal number by a power of ten by MOVING THE POINT, never by
/// multiplying an f64.
///
/// `2057.515` MHz reached the N9340B as `:FREQuency:CENTer 2057514999.9999998`.
/// Nothing was wrong with the number: 2057.515 has no exact binary
/// representation, 1e6 does, and their product in f64 is that. Rounding the
/// result would only hide it — 15 significant figures of nonsense would become
/// 15 significant figures of luck, and the next value with a different fraction
/// would produce a different artefact.
///
/// Shifting the decimal point in the digit STRING is exact for every input,
/// because a power of ten is what a decimal point means. `2057.515` shifted six
/// places is `2057515000`, with no arithmetic performed at all.
///
/// Returns None for anything that is not a plain decimal — exponent forms,
/// `MAXimum`, units — leaving those to the caller.
pub fn shift_decimal(text: &str, power: i32) -> Option<String> {
    let s = text.trim();
    let (sign, body) = match s.strip_prefix('-') {
        Some(rest) => ("-", rest),
        None => ("", s.strip_prefix('+').unwrap_or(s)),
    };
    let (int, frac) = match body.split_once('.') {
        Some((i, f)) => (i, f),
        None => (body, ""),
    };
    if int.is_empty() && frac.is_empty() {
        return None;
    }
    if !int.bytes().all(|b| b.is_ascii_digit()) || !frac.bytes().all(|b| b.is_ascii_digit()) {
        return None;
    }

    // digits + where the point sits inside them
    let digits: String = format!("{int}{frac}");
    let point = int.len() as i32 + power;

    let (mut whole, mut fraction) = if point <= 0 {
        ("0".to_string(), format!("{}{}", "0".repeat((-point) as usize), digits))
    } else if point as usize >= digits.len() {
        (format!("{}{}", digits, "0".repeat(point as usize - digits.len())), String::new())
    } else {
        (digits[..point as usize].to_string(), digits[point as usize..].to_string())
    };

    let trimmed = whole.trim_start_matches('0');
    whole = if trimmed.is_empty() { "0".to_string() } else { trimmed.to_string() };
    fraction = fraction.trim_end_matches('0').to_string();

    let out = if fraction.is_empty() {
        format!("{sign}{whole}")
    } else {
        format!("{sign}{whole}.{fraction}")
    };
    // "-0" is not a number anybody means to send.
    Some(if out == "-0" { "0".to_string() } else { out })
}

/// How many places each scaling converter moves the point.
fn converter_power(converter: &str) -> Option<i32> {
    match converter {
        "mhz_to_hz" => Some(6),
        "hz_to_mhz" => Some(-6),
        "khz_to_hz" => Some(3),
        "hz_to_khz" => Some(-3),
        "v_to_mv" => Some(3),
        "mv_to_v" => Some(-3),
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
    // The payload's own text, NOT an f64 read of it. `Value::Number` already
    // holds the shortest decimal that round-trips, so its string form is the
    // number the panel actually sent — and it is that string, never a float,
    // that gets scaled and written to the instrument.
    let text: Option<String> = match val {
        Value::Number(n) => Some(n.to_string()),
        Value::String(s) => {
            let t = s.trim();
            if t.parse::<f64>().is_ok() { Some(t.to_string()) } else { None }
        }
        _ => None,
    };

    match text {
        Some(t) => {
            let lower = converter.to_lowercase();
            let Some(power) = converter_power(&lower) else {
                warn!("Unknown converter '{}'. Passing value through unchanged.", converter);
                return val.clone();
            };
            // Exponent forms ("1e-07", a DS1104Z channel calibration) have no
            // decimal point to move. They are rare, already unambiguous to the
            // instrument, and worth keeping on the float path rather than
            // growing a parser for them.
            match shift_decimal(&t, power) {
                Some(scaled) => Value::String(scaled),
                None => match t.parse::<f64>() {
                    Ok(num) => {
                        let f = num * 10f64.powi(power);
                        Number::from_f64(f).map(Value::Number).unwrap_or(Value::Null)
                    }
                    Err(_) => val.clone(),
                },
            }
        }
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
        assert_eq!(apply_converter("mhz_to_hz", Some(&json!("0.3"))), json!("300000"));
        assert_eq!(apply_converter("mhz_to_hz", Some(&json!(0.3))), json!("300000"));
        assert_eq!(apply_converter("khz_to_hz", Some(&json!("300"))), json!("300000"));
        assert_eq!(apply_converter("mhz_to_hz", Some(&json!(" 0.0003 "))), json!("300"));
    }

    #[test]
    fn scaling_into_hz_never_produces_a_decimal_point() {
        // The one that reached the bench: 2057.515 MHz went out as
        // ':FREQuency:CENTer 2057514999.9999998'. 2057.515 has no exact binary
        // form and 1e6 does, so their f64 product IS that number — the fix is to
        // never perform the multiplication.
        assert_eq!(apply_converter("mhz_to_hz", Some(&json!(2057.515))), json!("2057515000"));
        assert_eq!(apply_converter("mhz_to_hz", Some(&json!("2057.515"))), json!("2057515000"));
        // Every fraction that bit us on this bench, in both directions.
        for (mhz, hz) in [
            ("1.1", "1100000"), ("665.551", "665551000"), ("0.0000001", "0.1"),
            ("107.5", "107500000"), ("3000", "3000000000"), ("-1.5", "-1500000"),
        ] {
            assert_eq!(apply_converter("mhz_to_hz", Some(&json!(mhz))), json!(hz), "{mhz} MHz");
        }
        for (hz, mhz) in [("665551000", "665.551"), ("300000", "0.3"), ("1", "0.000001")] {
            assert_eq!(apply_converter("hz_to_mhz", Some(&json!(hz))), json!(mhz), "{hz} Hz");
        }
    }

    #[test]
    fn a_non_numeric_string_still_passes_through_untouched() {
        // Enum arguments and identity strings must not be mangled by a numeric
        // converter that was declared on the widget by mistake.
        assert_eq!(apply_converter("mhz_to_hz", Some(&json!("MAXimum"))), json!("MAXimum"));
    }

    #[test]
    fn an_exponent_form_keeps_its_meaning() {
        // A DS1104Z channel calibration is authored as -1e-07. There is no point
        // to move, so it stays on the float path rather than being dropped.
        let out = apply_converter("v_to_mv", Some(&json!("-1e-07")));
        let f = out.as_f64().expect("still a number");
        assert!((f - -1e-4).abs() < 1e-15, "-1e-07 V is -1e-4 mV, got {f}");
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
