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
    
    // Lookup SCPI template. The instance's own model wins — see verbs::target_model.
    let target_model = super::target_model(msg, yak);
    let target_model = target_model.as_str();
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

    // SET has no correlation envelope of its own, so both destinations carry
    // the same raw command.
    super::dispatch(client, config, yak, &scpi_command, &scpi_command, "SET").await;
}
