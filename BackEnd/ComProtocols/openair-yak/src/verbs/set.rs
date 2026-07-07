use rumqttc::AsyncClient;
use crate::config::Config;
use crate::models::IncomingMessage;
use crate::converters;
use crate::repository::YakRepository;

/// Handles the SET (Component Parameters) construct
/// Used for channel-specific settings like Vertical Scale or Offset.
pub async fn handle(client: &AsyncClient, config: &Config, msg: &IncomingMessage, repo: &YakRepository) {
    let yak = msg.yak_handler.as_ref().unwrap();
    eprintln!("   ⚙️ [YAK SET] Handling SET command: {}", yak.command);
    
    // Extract the raw value based on 'value' (standard UI payload) or input_name
    let raw_val = msg.extra.get("value").or_else(|| msg.extra.get(&yak.input_name));
    
    // Apply the converter (if any)
    let converted_val = converters::apply_converter(&yak.converter, raw_val);
    
    // Lookup SCPI template
    // We try to grab the model from the payload if provided, otherwise empty string for fallback
    let target_model = msg.model.as_deref().or(msg.device.as_deref()).unwrap_or("");
    let template = match repo.get_scpi(target_model, &yak.command) {
        Some(t) => t,
        None => {
            eprintln!("   ❌ [YAK SET] Command '{}' not found in YAK repository for model '{}'!", yak.command, target_model);
            return;
        }
    };

    // Inject value into SCPI template
    let mut scpi_command = template.clone();
    let exact_placeholder = format!("<{}>", yak.input_name);
    let val_str = match converted_val {
        serde_json::Value::Null => "".to_string(),
        serde_json::Value::String(ref s) => s.clone(),
        _ => converted_val.to_string(),
    };

    if scpi_command.contains(&exact_placeholder) {
        scpi_command = scpi_command.replace(&exact_placeholder, &val_str);
    } else if let Some(start) = scpi_command.find('<') {
        if let Some(end) = scpi_command[start..].find('>') {
            let to_replace = &scpi_command[start..start + end + 1];
            scpi_command = scpi_command.replace(to_replace, &val_str);
        }
    }
    
    eprintln!("   📡 [YAK MQTT] ⮞ TX SCPI (Model: {}): {}", target_model, scpi_command);
    
    // Publish out to VISA
    if let Err(e) = client.publish(&config.topic_publish, rumqttc::QoS::AtMostOnce, false, scpi_command.clone()).await {
        eprintln!("   ❌ [YAK MQTT] Failed to relay SET command: {}", e);
    }

    // Publish to monitor out
    let monitor_out = format!("{}/monitor/out", config.topic);
    let _ = client.publish(monitor_out, rumqttc::QoS::AtMostOnce, false, scpi_command).await;
}
