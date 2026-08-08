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
        // A boolean SET may name a command that exists only as an _ON/_OFF pair.
        //
        // Not every instrument spells a toggle as one parameterised command. The
        // N9340B's preamp is `:POWer:GAIN ON` and `:POWer:GAIN OFF` — two
        // zero-arg DO entries, no `<value>` anywhere — while the panel publishes
        // the single command `Set_Power_Gain` carrying value ON. Direct lookup
        // misses, and before this the toggle just logged "not found" on every
        // press: the button moved, the preamp never did.
        //
        // Strictly a fallback: it runs only after the exact name misses, so no
        // command that resolves today can be re-routed by it, and it only fires
        // when the payload is genuinely boolean. Anything else still errors.
        None => {
            let resolved = converters::as_bool(&converted_val)
                .or_else(|| raw_val.and_then(converters::as_bool))
                .and_then(|on| {
                    let paired = format!("{}_{}", yak.command, if on { "ON" } else { "OFF" });
                    repo.get_scpi_form(target_model, &paired, config.prefer_short_scpi)
                        .map(|t| (paired, t))
                });
            match resolved {
                Some((paired, t)) => {
                    eprintln!("   🔀 [YAK SET] '{}' is an ON/OFF pair on {} — resolved to '{}'",
                              yak.command, target_model, paired);
                    t
                }
                None => {
                    eprintln!("   ❌ [YAK SET] Command '{}' not found in YAK repository for model '{}'!", yak.command, target_model);
                    return;
                }
            }
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

    // Close the loop: ask what actually stuck (see YakHandler::readback).
    super::dispatch_readback(client, config, yak, repo, target_model).await;
}
