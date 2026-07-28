use rumqttc::AsyncClient;
use crate::config::Config;
use crate::models::IncomingMessage;
use crate::converters;
use crate::repository::YakRepository;

/// Handles the RIG (System Configuration) construct
pub async fn handle(client: &AsyncClient, config: &Config, msg: &IncomingMessage, repo: &YakRepository) {
    let yak = msg.yak_handler.as_ref().unwrap();
    eprintln!("   ⚙️ [YAK RIG] Handling RIG command: {}", yak.command);
    
    let raw_val = msg.extra.get("value").or_else(|| msg.extra.get(&yak.input_name));
    let converted_val = converters::apply_converter(&yak.converter, raw_val);
    
    // The instance's own model wins — see verbs::target_model.
    let target_model = super::target_model(msg, yak);
    let target_model = target_model.as_str();
    let template = match repo.get_scpi_form(target_model, &yak.command, config.prefer_short_scpi) {
        Some(t) => t,
        None => {
            eprintln!("   ❌ [YAK RIG] Command '{}' not found in YAK repository for model '{}'!", yak.command, target_model);
            return;
        }
    };

    // Per-instance constants first (see verbs::apply_params), then the value.
    let mut scpi_command = super::apply_params(&template, yak);
    // Every placeholder, not just one — see verbs::fill_placeholders. RIG
    // commands are the multi-argument ones by nature (APPLy:SINusoid takes
    // frequency, amplitude and offset together), so this verb is the one that
    // could never work before.
    scpi_command = match super::fill_placeholders(&scpi_command, msg, yak, &converted_val) {
        Ok(filled) => filled,
        Err(missing) => {
            eprintln!("   ❌ [YAK RIG] '{}' needs {:?}, and the payload plus sibling Input widgets \
                       supplied none of it — not sending a half-built command",
                      yak.command, missing);
            return;
        }
    };

    let scpi_string = scpi_command;
    eprintln!("   📡 [YAK MQTT] ⮞ TX SCPI (Model: {}): {}", target_model, scpi_string);

    let payload = if let Some(cid) = msg.extra.get("full_id").and_then(|v| v.as_str()) {
        serde_json::json!({
            "correlation_id": cid,
            "command": scpi_string
        }).to_string()
    } else {
        scpi_string.clone()
    };

    super::dispatch(client, config, yak, &scpi_string, &payload, "RIG").await;
}
