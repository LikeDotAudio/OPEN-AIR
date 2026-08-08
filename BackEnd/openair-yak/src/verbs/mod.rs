pub mod nab;
pub mod rig;
pub mod set;
pub mod do_cmd;

use rumqttc::AsyncClient;
use crate::config::Config;
use crate::models::YakHandler;

/// Send one translated SCPI command on its way, and mirror it to the monitor.
///
/// Two destinations, and the difference matters:
///
/// * `yak_handler.target` — a per-device VISA Write topic, stamped onto
///   generated instrument panels. The VISA daemon executes whatever payload
///   lands there verbatim, so this path publishes the RAW SCPI string. Wrapping
///   it in the correlation-id envelope would send `{"correlation_id":…}` to the
///   instrument as a command.
/// * `config.topic_publish` — the legacy global topic, used by hand-authored
///   panels that name no device. The envelope is preserved there because that
///   is the shape anything listening on it was written against.
/// Say what YAK just did, on a topic the browser subscribes to.
///
/// `eprintln!` reaches the agent's own stdout and nothing else, which is
/// invisible to whoever is actually pressing the button — the same gap the VISA
/// scan log was opened to close. Every verb narrates here so a press produces
/// visible dialog in the browser console: the command, the model, the SCPI that
/// went out, and the instrument it went to.
///
/// Non-retained, QoS 0: this is an event stream. A page opened an hour from now
/// must not be shown a `*RST` as though it were happening right then.
pub async fn narrate(client: &AsyncClient, config: &Config, level: &str, message: String) {
    let line = serde_json::json!({
        "level": level,          // "info" | "ok" | "warn" | "error"
        "message": message,
        "source": "yak",
        "ts": std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs_f64())
            .unwrap_or(0.0),
    });
    let topic = format!("{}/Activity", config.topic);
    let _ = client
        .publish(topic, rumqttc::QoS::AtMostOnce, false, line.to_string().into_bytes())
        .await;
}

/// Fire a control's declared readback query, if it declared one.
///
/// Runs after the write has been dispatched, so the instrument answers with the
/// value that actually took effect rather than the one it was mid-way through
/// applying. Silent when no readback is named — the overwhelmingly common case.
pub async fn dispatch_readback(
    client: &AsyncClient,
    config: &Config,
    yak: &YakHandler,
    repo: &crate::repository::YakRepository,
    target_model: &str,
) {
    if yak.readback.is_empty() {
        return;
    }
    // A comma-separated LIST, because one write can change more than one kind of
    // thing. All Markers ON/OFF alters both which markers are enabled and what
    // they read, and those live in two different queries — asking only one back
    // leaves half the panel showing what it believed before the press.
    //
    // Sent as separate queries rather than one longer chain on purpose: a single
    // unanswerable statement kills an entire chained reply, so combining them
    // would let one bad node take the other's values down with it.
    for name in yak.readback.split(',').map(str::trim).filter(|n| !n.is_empty()) {
        let Some(template) = repo.get_scpi_form(target_model, name, config.prefer_short_scpi) else {
            eprintln!("   ❌ [YAK READBACK] '{}' not found in YAK repository for model '{}'!",
                      name, target_model);
            continue;
        };
        // Instance constants only: a query takes no widget value.
        let scpi = apply_params(&template, yak);
        eprintln!("   🔄 [YAK READBACK] {} -> {}", name, scpi);
        dispatch(client, config, yak, &scpi, &scpi, "NAB").await;
    }
}

pub async fn dispatch(
    client: &AsyncClient,
    config: &Config,
    yak: &YakHandler,
    scpi: &str,
    enveloped: &str,
    verb: &str,
) {
    let target = yak.target.as_deref().filter(|t| !t.is_empty());
    let (topic, payload) = match target {
        Some(t) => (t, scpi),
        None => (config.topic_publish.as_str(), enveloped),
    };

    if target.is_some() {
        eprintln!("   🎯 [YAK MQTT] ⮞ {} -> {}", verb, topic);
    }

    // The instrument this actually reaches, as the operator would name it: the
    // device segment of the Write topic, not the whole path.
    let instrument = target
        .and_then(|t| t.strip_suffix("/Write"))
        .and_then(|t| t.rsplit("/Device/").next())
        .unwrap_or("the global publish topic");
    narrate(
        client,
        config,
        "ok",
        format!("{verb} {} -> {scpi}  →  {instrument}", yak.command),
    )
    .await;
    if let Err(e) = client
        .publish(topic, rumqttc::QoS::AtMostOnce, false, payload.as_bytes())
        .await
    {
        eprintln!("   ❌ [YAK MQTT] Failed to relay {} command: {}", verb, e);
    }

    let monitor_out = format!("{}/monitor/out", config.topic);
    let _ = client
        .publish(monitor_out, rumqttc::QoS::AtMostOnce, false, scpi.as_bytes())
        .await;
}

/// Drop a decimal point that carries no information.
///
/// `1.0` is not how a number is written to an instrument — the widget said
/// "one", the table declares NPLC as `kind: integer`, and the meter should be
/// sent `1`. A GUI knob emits whatever its `value_default` string says and
/// JSON renders a whole f64 as `1.0`, so both routes produce a decimal point
/// nobody asked for.
///
/// Deliberately conservative: only trailing zeros after a decimal point are
/// removed, and only when what remains is still the same number. Genuine
/// fractions are left exactly as written, because plenty of this bench's
/// commands need them — a DS1104Z takes 0.001 V/div and a channel calibration
/// of -1e-07, and "no decimal points" applied literally would send those as 0.
/// Exponent forms are never touched.
fn scpi_number(text: &str) -> String {
    let s = text.trim();
    // Only plain decimal numbers; anything with an exponent, unit or keyword is
    // somebody else's business.
    let body = s.strip_prefix('-').unwrap_or(s);
    let mut parts = body.split('.');
    let (Some(int), Some(frac), None) = (parts.next(), parts.next(), parts.next()) else {
        return s.to_string();
    };
    if int.is_empty()
        || !int.bytes().all(|b| b.is_ascii_digit())
        || !frac.bytes().all(|b| b.is_ascii_digit())
    {
        return s.to_string();
    }
    let trimmed = frac.trim_end_matches('0');
    let sign = if s.starts_with('-') { "-" } else { "" };
    if trimmed.is_empty() {
        format!("{sign}{int}")
    } else {
        format!("{sign}{int}.{trimmed}")
    }
}

/// Fill in the per-instance constants a panel was stamped with (`<chan>`, …).
///
/// Must run BEFORE the widget's value is injected. Value injection falls back
/// to "replace the first `<…>` in the template" whenever the template has no
/// `<input_name>` placeholder, so on `INST:NSEL <chan>;VOLT <volt>` it would
/// otherwise write the voltage into the slot selector — quietly commanding the
/// wrong module rather than failing.
pub fn apply_params(template: &str, yak: &YakHandler) -> String {
    let mut out = template.to_string();
    for (name, value) in &yak.params {
        out = out.replace(&format!("<{}>", name), value);
    }
    out
}

/// Fill every `<placeholder>` in a SCPI template, or say which ones are missing.
///
/// A command like `APPLy:SINusoid <freq>, <amp>, <offset>` has three arguments
/// living in three sibling widgets. The old substitution filled exactly one —
/// `<input_name>`, else the first `<…>` — and sent the rest to the instrument
/// verbatim, so a three-argument command arrived as
/// `APPLy:SINusoid 1000, <amp>, <offset>`. That is a syntax error the panel has
/// no way to show you, which is why templates carrying multi-argument commands
/// were never bound to anything.
///
/// Resolution order per placeholder:
///   1. a same-named key in the payload — sibling `Input/*` widgets are folded
///      in by mqtt.rs before dispatch, and a named argument always beats the
///      actuator's own press value
///   2. the primary value (converted) when the name matches `input_name`
///   3. the primary value when it is the ONLY placeholder, preserving the old
///      "first `<…>` wins" behaviour for handlers that name no input
///
/// Returns Err with the unresolved names rather than sending a half-built
/// command: refusing is recoverable, a malformed write to an instrument is not.
pub fn fill_placeholders(
    template: &str,
    msg: &crate::models::IncomingMessage,
    yak: &YakHandler,
    primary: &serde_json::Value,
) -> Result<String, Vec<String>> {
    let as_text = |v: &serde_json::Value| match v {
        serde_json::Value::Null => String::new(),
        serde_json::Value::String(s) => scpi_number(s),
        serde_json::Value::Number(n) => scpi_number(&n.to_string()),
        other => other.to_string(),
    };

    let names: Vec<String> = template
        .match_indices('<')
        .filter_map(|(start, _)| {
            template[start..].find('>').map(|end| template[start + 1..start + end].to_string())
        })
        .collect();

    let single = names.len() == 1;
    let mut out = template.to_string();
    let mut missing = Vec::new();

    for name in &names {
        // A NAMED value wins over the primary, and that order matters: the
        // handler sits on the actuator, so its own payload is the button press
        // (`value: 1`), never the argument. `<freq>` must come from the sibling
        // `Input/freq` widget even though the handler declares freq as its
        // input_name — otherwise every command reads "1".
        let resolved = if let Some(v) = msg.extra.get(name) {
            Some(as_text(v))
        } else if !yak.input_name.is_empty() && *name == yak.input_name {
            Some(as_text(primary))
        } else if single {
            Some(as_text(primary))
        } else {
            None
        };
        match resolved {
            Some(text) if !text.is_empty() => {
                out = out.replace(&format!("<{name}>"), &text);
            }
            _ => missing.push(name.clone()),
        }
    }

    if missing.is_empty() { Ok(out) } else { Err(missing) }
}

/// Which model's command table to look SCPI up in.
///
/// Instance binding first (the panel knows what it was stamped for), then
/// whatever the payload claimed, then "" — which sends `get_scpi` into its
/// search-every-model fallback.
pub fn target_model(msg: &crate::models::IncomingMessage, yak: &YakHandler) -> String {
    yak.model
        .as_deref()
        .filter(|m| !m.is_empty())
        .or(msg.model.as_deref())
        .or(msg.device.as_deref())
        .unwrap_or("")
        .to_string()
}

#[cfg(test)]
mod number_tests {
    use super::scpi_number;

    #[test]
    fn a_whole_number_is_written_without_a_decimal_point() {
        // What the log showed going to a 34401A whose table declares NPLC as an
        // integer: `:SENSe:VOLTage:DC:NPLC 1.0`.
        assert_eq!(scpi_number("1.0"), "1");
        assert_eq!(scpi_number("10.000"), "10");
        assert_eq!(scpi_number("-5.00"), "-5");
        assert_eq!(scpi_number("1"), "1");
    }

    #[test]
    fn a_real_fraction_survives_intact() {
        // This bench needs these: 1 mV/div on a DS1104Z, 0.02 NPLC on a meter.
        assert_eq!(scpi_number("0.001"), "0.001");
        assert_eq!(scpi_number("0.02"), "0.02");
        assert_eq!(scpi_number("1.50"), "1.5");
        assert_eq!(scpi_number("-0.10"), "-0.1");
    }

    #[test]
    fn anything_that_is_not_a_plain_decimal_is_left_alone() {
        // Exponents, keywords and units are not ours to rewrite.
        assert_eq!(scpi_number("1e-07"), "1e-07");
        assert_eq!(scpi_number("MAX"), "MAX");
        assert_eq!(scpi_number("ON"), "ON");
        assert_eq!(scpi_number("1.2.3"), "1.2.3");
        assert_eq!(scpi_number("10 V"), "10 V");
    }
}
