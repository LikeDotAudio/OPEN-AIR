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
    let template = match repo.get_scpi_form(target_model, &yak.command, config.prefer_short_scpi) {
        Some(t) => t,
        None => {
            eprintln!("   ❌ [YAK SET] Command '{}' not found in YAK repository for model '{}'!", yak.command, target_model);
            return;
        }
    };

    // Per-instance constants first (see verbs::apply_params), then the value.
    let mut scpi_command = super::apply_params(&template, yak);
    // Every placeholder, not just one — see verbs::fill_placeholders.
    scpi_command = match super::fill_placeholders(&scpi_command, msg, yak, &converted_val) {
        Ok(filled) => filled,
        Err(missing) => {
            eprintln!("   ❌ [YAK SET] '{}' needs {:?}, and the payload plus sibling Input widgets \
                       supplied none of it — not sending a half-built command",
                      yak.command, missing);
            return;
        }
    };
    
    eprintln!("   📡 [YAK MQTT] ⮞ TX SCPI (Model: {}): {}", target_model, scpi_command);

    // SET has no correlation envelope of its own, so both destinations carry
    // the same raw command.
    super::dispatch(client, config, yak, &scpi_command, &scpi_command, "SET").await;
}
