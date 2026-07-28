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
        serde_json::Value::String(s) => s.clone(),
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
