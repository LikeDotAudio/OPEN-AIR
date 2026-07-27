use rumqttc::AsyncClient;
use crate::config::Config;
use crate::models::IncomingMessage;
use crate::repository::YakRepository;

/// Handles the DO (Execution) construct
pub async fn handle(client: &AsyncClient, config: &Config, msg: &IncomingMessage, repo: &YakRepository) {
    let yak = msg.yak_handler.as_ref().unwrap();
    let _raw_val = msg.extra.get("value").or_else(|| msg.extra.get(&yak.input_name));
    eprintln!("   ⚙️ [YAK DO] Handling DO command: {}", yak.command);
    
    // The instance's own model wins — see verbs::target_model.
    let target_model = super::target_model(msg, yak);
    let target_model = target_model.as_str();
    let template = match repo.get_scpi(target_model, &yak.command) {
        Some(t) => t,
        None => {
            eprintln!("   ❌ [YAK DO] Command '{}' not found in YAK repository for model '{}'!", yak.command, target_model);
            return;
        }
    };
    
    // No widget value on DO, but the instance constants still apply — an
    // `INST:NSEL <chan>;OUTP ON` must know which slot it is turning on.
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

    super::dispatch(client, config, yak, &scpi_string, &payload, "DO").await;
}
