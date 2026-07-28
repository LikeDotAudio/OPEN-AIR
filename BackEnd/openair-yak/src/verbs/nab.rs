use rumqttc::AsyncClient;
use crate::config::Config;
use crate::models::IncomingMessage;
use crate::repository::YakRepository;

/// Handles the NAB (Status/Observation) construct
pub async fn handle(client: &AsyncClient, config: &Config, msg: &IncomingMessage, repo: &YakRepository) {
    let yak = msg.yak_handler.as_ref().unwrap();
    let raw_val = msg.extra.get("value").or_else(|| msg.extra.get(&yak.input_name));
    eprintln!("   📡 [YAK NAB] Handling command: {}", yak.command);
    
    // The instance's own model wins — see verbs::target_model.
    let target_model = super::target_model(msg, yak);
    let target_model = target_model.as_str();
    let template = match repo.get_scpi_form(target_model, &yak.command, config.prefer_short_scpi) {
        Some(t) => t,
        None => {
            eprintln!("   ❌ [YAK NAB] Command '{}' not found in YAK repository for model '{}'!", yak.command, target_model);
            return;
        }
    };
    
    // NAB is usually a query, like `FREQ:SPAN?`, so it takes no widget value —
    // but it still needs its instance constants, or `INST:NSEL <chan>;MEAS:VOLT?`
    // reaches the instrument with the placeholder still in it.
    let scpi_string = super::apply_params(&template, yak);
    eprintln!("   📡 [YAK MQTT] ⮞ TX SCPI (Model: {}): {}", target_model, scpi_string);
    
    let payload = if let Some(cid) = msg.extra.get("full_id").and_then(|v| v.as_str()) {
        serde_json::json!({
            "correlation_id": cid,
            "command": scpi_string
        }).to_string()
    } else {
        scpi_string.clone()
    };
    
    super::dispatch(client, config, yak, &scpi_string, &payload, "NAB").await;
}
