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
    let val_str = match converted_val {
        serde_json::Value::Null => "".to_string(),
        serde_json::Value::String(ref s) => s.clone(),
        _ => converted_val.to_string(),
    };
    
    let target_model = msg.model.as_deref().or(msg.device.as_deref()).unwrap_or("");
    let template = match repo.get_scpi(target_model, &yak.command) {
        Some(t) => t,
        None => {
            eprintln!("   ❌ [YAK RIG] Command '{}' not found in YAK repository for model '{}'!", yak.command, target_model);
            return;
        }
    };

    let mut scpi_command = template.clone();
    let exact_placeholder = format!("<{}>", yak.input_name);

    if scpi_command.contains(&exact_placeholder) {
        scpi_command = scpi_command.replace(&exact_placeholder, &val_str);
    } else if let Some(start) = scpi_command.find('<') {
        if let Some(end) = scpi_command[start..].find('>') {
            let to_replace = &scpi_command[start..start + end + 1];
            scpi_command = scpi_command.replace(to_replace, &val_str);
        }
    }

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

    if let Err(e) = client.publish(&config.topic_publish, rumqttc::QoS::AtMostOnce, false, payload).await {
        eprintln!("   ❌ [YAK MQTT] Failed to relay RIG command: {}", e);
    }
    let monitor_out = format!("{}/monitor/out", config.topic);
    let _ = client.publish(&monitor_out, rumqttc::QoS::AtMostOnce, false, scpi_string).await;
}
