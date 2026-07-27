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
