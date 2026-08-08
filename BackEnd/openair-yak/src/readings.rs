//! Turning one instrument reply into individually addressable readings.
//!
//! THE TALKER / LISTENER SPLIT
//!
//! A control says what it is — `center` — and that one name serves both
//! directions. It TALKS by sending its command, and it LISTENS to the reading of
//! the same name. The two stay decoupled: whoever publishes a reading has no
//! idea who consumes it, so a graph, a status bar or a second panel can listen
//! later without the writer changing at all.
//!
//! WHY NOT INDEX INTO `/Read`
//!
//! A device has exactly one `/Read` topic and its payload is a bare string, so
//! every query on that device overwrites the last — the VISA heartbeat's `*IDN?`
//! lands on top of a frequency reply. Reading a value out of it meant counting
//! separators, and a positional index silently points at the wrong quantity the
//! day a `returns` block gains a field. A named reading cannot drift that way.
//!
//! VERIFICATION FALLS OUT
//!
//! Because a reading carries the unit the instrument reported in, a listener can
//! compare what came back against what its talker asked for. That is the check
//! that would have caught a 0.3 MHz button setting an instrument to 0.3 Hz.

use crate::repository::YakRepository;

/// `OpenAir/System/Protocols/visa/Device/<family>/<model>/<dev>` from any topic
/// under it, plus the model segment.
pub fn device_base_and_model(topic: &str) -> Option<(String, String)> {
    let base = topic.rsplit_once('/').map(|(b, _)| b)?;
    let mut parts = base.rsplit('/');
    let _dev = parts.next()?;
    let model = parts.next()?.to_string();
    Some((base.to_string(), model))
}

/// One value ready to publish, already named and carrying its unit.
#[derive(Debug, PartialEq)]
pub struct Reading {
    pub name: String,
    pub value: String,
    pub unit: Option<String>,
}

/// The value, without the quotes SCPI wraps a string reply in.
///
/// `FUNCtion?` answers `"VOLT:DC"` — the quotes are the transport saying "this
/// is a string", not part of what the instrument measures with. Published
/// verbatim they reach a control as a six-character value that matches none of
/// its five positions, so the function selector sits on DC while the meter is
/// reading ohms: the same silent disagreement the enumerated readings were
/// named to end. Only a matched pair is removed, and only from the outside.
fn unquote(v: &str) -> &str {
    let bytes = v.as_bytes();
    if bytes.len() >= 2 {
        let (first, last) = (bytes[0], bytes[bytes.len() - 1]);
        if (first == b'"' && last == b'"') || (first == b'\'' && last == b'\'') {
            return &v[1..v.len() - 1];
        }
    }
    v
}

/// Split a reply into named readings using the command's declared `returns`.
///
/// Returns an empty vec when the command is unknown or declares no reply shape —
/// publishing an unlabelled fragment would be worse than publishing nothing,
/// because a listener cannot tell a misattributed value from a correct one.
pub fn decompose(repo: &YakRepository, model: &str, command_name: &str, raw: &str) -> Vec<Reading> {
    let Some(cmd) = repo.get(model, command_name) else { return Vec::new() };
    let Some(returns) = cmd.returns.as_ref() else { return Vec::new() };

    if returns.fields.is_empty() {
        // A single-value query answers under its own command name.
        let v = unquote(raw.trim());
        if v.is_empty() {
            return Vec::new();
        }
        return vec![Reading {
            name: command_name.to_string(),
            value: v.to_string(),
            unit: returns.unit.clone().filter(|u| !u.is_empty()),
        }];
    }

    let sep = returns.separator.clone().unwrap_or_else(|| ";".to_string());
    let parts: Vec<&str> = raw.split(sep.as_str()).collect();

    // A short reply is not a reason to guess. Publishing the fields that DID
    // arrive is right; inventing the rest, or shifting them left to fill the
    // gap, would put a value under someone else's name.
    returns
        .fields
        .iter()
        .zip(parts.iter())
        .filter_map(|(field, part)| {
            let v = unquote(part.trim());
            if v.is_empty() {
                return None;
            }
            Some(Reading {
                name: field.name.clone(),
                value: v.to_string(),
                unit: field.unit.clone().filter(|u| !u.is_empty()),
            })
        })
        .collect()
}

/// `<device base>/Reading/<command>/<field>` — namespaced by the query that
/// produced it, so `bandwidth_settings/time` and a sweep command's `time` are
/// different topics rather than a silent collision.
pub fn reading_topic(device_base: &str, command_name: &str, reading: &str) -> String {
    if reading == command_name {
        format!("{device_base}/Reading/{command_name}")
    } else {
        format!("{device_base}/Reading/{command_name}/{reading}")
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn a_device_base_and_model_come_off_the_reply_topic() {
        let t = "OpenAir/System/Protocols/visa/Device/Spectrum/N9340B/Dev0/Reply";
        let (base, model) = device_base_and_model(t).expect("parses");
        assert_eq!(model, "N9340B");
        assert_eq!(base, "OpenAir/System/Protocols/visa/Device/Spectrum/N9340B/Dev0");
    }

    #[test]
    fn a_compound_reading_is_namespaced_by_its_query() {
        let base = "OpenAir/System/Protocols/visa/Device/Spectrum/N9340B/Dev0";
        assert_eq!(
            reading_topic(base, "bandwidth_settings", "time"),
            format!("{base}/Reading/bandwidth_settings/time")
        );
        // A single-value query does not repeat its own name.
        assert_eq!(
            reading_topic(base, "Reference_Level", "Reference_Level"),
            format!("{base}/Reading/Reference_Level")
        );
    }

    #[test]
    fn a_quoted_string_reply_publishes_without_its_quotes() {
        // FUNCtion? answers "VOLT:DC"; the value is VOLT:DC.
        assert_eq!(unquote("\"VOLT:DC\""), "VOLT:DC");
        assert_eq!(unquote("'VOLT:DC'"), "VOLT:DC");
        // A lone or interior quote is part of the value, not a wrapper.
        assert_eq!(unquote("\"VOLT:DC"), "\"VOLT:DC");
        assert_eq!(unquote("6.5\" rack"), "6.5\" rack");
        assert_eq!(unquote("+1.0E+00"), "+1.0E+00");
    }
}
