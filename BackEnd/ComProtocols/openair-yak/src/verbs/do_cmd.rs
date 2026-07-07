use rumqttc::AsyncClient;
use crate::config::Config;
use crate::models::IncomingMessage;
use crate::repository::YakRepository;

/// Handles the DO (Execution) construct
pub async fn handle(client: &AsyncClient, config: &Config, msg: &IncomingMessage, repo: &YakRepository) {
    let yak = msg.yak_handler.as_ref().unwrap();
    let _raw_val = msg.extra.get("value").or_else(|| msg.extra.get(&yak.input_name));
    eprintln!("   ⚙️ [YAK DO] Handling DO command: {}", yak.command);
    
    let target_model = msg.model.as_deref().or(msg.device.as_deref()).unwrap_or("");
    let template = match repo.get_scpi(target_model, &yak.command) {
        Some(t) => t,
        None => {
            eprintln!("   ❌ [YAK DO] Command '{}' not found in YAK repository for model '{}'!", yak.command, target_model);
            return;
        }
    };
    
    let scpi_string = template.clone();
    eprintln!("   📡 [YAK MQTT] ⮞ TX SCPI (Model: {}): {}", target_model, scpi_string);
    
    let payload = if let Some(cid) = msg.extra.get("full_id").and_then(|v| v.as_str()) {
        serde_json::json!({
            "correlation_id": cid,
            "command": scpi_string
        }).to_string()
    } else {
        scpi_string.clone()
    };

    if let Err(e) = client.publish(&config.topic_publish, rumqttc::QoS::AtMostOnce, false, payload).await {
        eprintln!("   ❌ [YAK MQTT] Failed to relay DO command: {}", e);
    }
    let monitor_out = format!("{}/monitor/out", config.topic);
    let _ = client.publish(monitor_out, rumqttc::QoS::AtMostOnce, false, scpi_string).await;
}
