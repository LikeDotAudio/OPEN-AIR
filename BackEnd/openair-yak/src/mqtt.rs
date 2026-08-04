use crate::config::Config;
use crate::verbs;
use crate::repository::YakRepository;
use log::error;
use rumqttc::{AsyncClient, MqttOptions, QoS, Event, Incoming};
use std::time::Duration;
use std::sync::Arc;
use std::collections::HashMap;

/// Is this GUI value a press, rather than the release that follows it?
///
/// Mirrors the orchestrator's rule for its own Rescan/Clear triggers, so the
/// whole system agrees on what counts as "the button was pressed".
fn is_truthy_trigger(v: &serde_json::Value) -> bool {
    match v {
        serde_json::Value::Bool(b) => *b,
        serde_json::Value::Number(n) => n.as_f64().unwrap_or(0.0) != 0.0,
        serde_json::Value::String(s) => {
            s == "1" || s.eq_ignore_ascii_case("true") || s.eq_ignore_ascii_case("on")
        }
        _ => false,
    }
}

pub async fn start_mqtt_client(config: Config, repo: Arc<YakRepository>) -> Result<(), Box<dyn std::error::Error>> {
    let client_id = format!("openair-yak-agent-{}", std::process::id());
    let mut mqttoptions = MqttOptions::new(client_id, "localhost", 1883);
    mqttoptions.set_keep_alive(Duration::from_secs(5));
    // Increase max packet size to 256MB to handle massive OPEN-AIR GUI retained JSON payloads
    mqttoptions.set_max_packet_size(256 * 1024 * 1024, 256 * 1024 * 1024);

    // v41 AgentHeartbeat (contracts H1/H2): retained beat + Last Will at
    // OpenAir/System/Agents/yak, typed by openair-contracts — a broker kill
    // of this agent flips the retained status to "offline" automatically.
    let connected_at = openair_contracts::time::from_unix_seconds(
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs_f64())
            .unwrap_or(0.0),
    );
    let (hb_topic, lwt_payload) =
        openair_contracts::heartbeat::heartbeat_lwt("yak", &connected_at, None)?;
    mqttoptions.set_last_will(rumqttc::LastWill::new(
        &hb_topic,
        serde_json::to_vec(&lwt_payload)?,
        QoS::AtLeastOnce,
        true,
    ));

    let (client, mut eventloop) = AsyncClient::new(mqttoptions, 1024);

    let mut online_beat = lwt_payload.clone();
    online_beat.status = openair_contracts::heartbeat::AgentHeartbeatStatus::Online;
    online_beat.version = Some(env!("CARGO_PKG_VERSION").to_string());
    online_beat.pid = Some(std::process::id() as i64);
    client
        .publish(&hb_topic, QoS::AtLeastOnce, true, serde_json::to_vec(&online_beat)?)
        .await?;
    eprintln!("   💓 [YAK AGENT] AgentHeartbeat online (retained) at {} — LWT registered", hb_topic);

    let listen_topic = "OpenAir/Gui/#";
    eprintln!("   📡 [YAK AGENT] Subscribing to listen topic: {}", listen_topic);
    client.subscribe(listen_topic, QoS::AtMostOnce).await?;

    let mut topic_configs: HashMap<String, crate::models::YakHandler> = HashMap::new();

    // Last value seen on every GUI topic.
    //
    // An authored command block is an actuator plus its arguments as SIBLING
    // widgets — `.../Apply_Sine/Execute Command` next to `.../Apply_Sine/Input/freq`,
    // `/amp`, `/offset`. Each publishes to its own topic, so the press that fires
    // the command carries only its own `1`; the three numbers the SCPI needs are
    // elsewhere on the bus. Caching them is what lets `APPLy:SINusoid <freq>, <amp>,
    // <offset>` be filled from a single button press, which is how the templates
    // were authored to work and why they have never worked.
    //
    // Cheap: this agent already subscribes to OpenAir/Gui/# for the configs.
    let mut topic_values: HashMap<String, serde_json::Value> = HashMap::new();

    loop {
        match eventloop.poll().await {
            Ok(Event::Incoming(Incoming::Publish(p))) => {
                if p.topic == config.topic_ignore {
                    continue;
                }

                let payload = String::from_utf8_lossy(&p.payload);
                let payload_str = payload.to_string();
                if payload_str.contains("yak_handler") {
                    eprintln!("   🐛 [YAK DEBUG] Raw payload with yak_handler on {}: {}", p.topic, payload_str);
                }

                // 1. Publish incoming command to monitor
                let monitor_in = format!("{}/monitor/in", config.topic);
                let client_clone = client.clone();
                let payload_clone = payload.to_string();
                tokio::spawn(async move {
                    let _ = client_clone.publish(&monitor_in, QoS::AtMostOnce, false, payload_clone.as_bytes()).await;
                });

                // 2. Deserialize payload
                let json_val: Result<serde_json::Value, _> = serde_json::from_str(&payload);
                
                if let Ok(parsed_json) = json_val {
                    // Protocol Translation Logic
                    if p.topic.ends_with("/config") {
                        if let Some(yak_val) = parsed_json.get("yak_handler") {
                            match serde_json::from_value::<crate::models::YakHandler>(yak_val.clone()) {
                                Ok(yak) => {
                                    let base_topic = p.topic.trim_end_matches("/config").to_string();
                                    eprintln!("   📡 [YAK MQTT] ⮜ RX CONFIG: {}", p.topic);
                                    eprintln!("   💾 [YAK TRANSLATOR] Cached yak_handler for topic: {}", base_topic);
                                    topic_configs.insert(base_topic, yak);
                                }
                                Err(e) => {
                                    eprintln!("   ❌ [YAK TRANSLATOR] Failed to parse yak_handler on {}: {}", p.topic, e);
                                }
                            }
                        }
                    } else {
                        // Remember every GUI value, command-bound or not — an argument
                        // widget carries no yak_handler of its own, so this is the only
                        // place its value is ever seen. Unwrapped: the GUI envelope is
                        // {value: X, full_id: …}, and a placeholder wants X.
                        {
                            let stored = parsed_json.get("value").cloned()
                                .unwrap_or_else(|| parsed_json.clone());
                            topic_values.insert(p.topic.to_string(), stored);
                        }

                        // Execution Payload
                        if let Some(yak) = topic_configs.get(&p.topic) {
                            // A RETAINED value is state, not a command.
                            //
                            // The GUI publishes control values retained by
                            // default, so every one of them is replayed to this
                            // agent on connect. Acting on that replay means a
                            // reconnect re-fires whatever each panel was last
                            // set to — including, now that instruments have a
                            // Setup page, a `*RST` at every discovered
                            // instrument simply because YAK restarted. The
                            // orchestrator applies the same rule to its Rescan
                            // and Clear triggers, and for the same reason.
                            if p.retain {
                                eprintln!("   ⏭️  [YAK] retained replay on {} — state, not a command; not firing '{}'",
                                          p.topic, yak.command);
                                continue;
                            }
                            // A momentary control reports BOTH edges: true on
                            // press, false on release. That is what a button
                            // physically does, and the GUI is right to say so —
                            // but a DO or a NAB carries no widget value, so both
                            // edges look identical here and the command would run
                            // twice per press, once on the way down and once on
                            // the way up.
                            //
                            // Only the truthy edge is a trigger. SET and RIG are
                            // untouched: there the value IS the payload, and
                            // `false` is a legitimate thing to send.
                            let verb = yak.yak_type.to_lowercase();
                            if matches!(verb.as_str(), "do" | "nab") {
                                if let Some(v) = parsed_json.get("value") {
                                    if !is_truthy_trigger(v) {
                                        continue;
                                    }
                                }
                            }
                            eprintln!("   📡 [YAK MQTT] ⮜ RX EXECUTE: {} -> {}", p.topic, payload);
                            
                            if !yak.enable {
                                eprintln!("   ⚠️ [YAK] yak_handler is disabled for command '{}'. Skipping.", yak.command);
                                continue;
                            }

                            // The model is no longer guessed from the topic path: generated
                            // instrument panels carry it in the yak_handler itself, stamped
                            // from the device that was actually discovered. Hand-authored
                            // panels still carry none, and verbs fall back to get_scpi()'s
                            // search-all-models behaviour as before.
                            let model_str: Option<String> = yak.model.clone();

                            // Fold the sibling `Input/*` widgets into the payload, so a
                            // verb sees {value: 1, freq: 1000, amp: 2, offset: 0} and can
                            // fill every placeholder. Existing keys win: a widget that
                            // published a compound value of its own is more specific than
                            // its neighbours.
                            let mut parsed_json = parsed_json;
                            if let Some(base) = p.topic.rsplit_once('/').map(|(b, _)| b) {
                                let prefix = format!("{base}/Input/");
                                let siblings: Vec<(String, serde_json::Value)> = topic_values
                                    .iter()
                                    .filter(|(t, _)| t.starts_with(&prefix))
                                    .filter_map(|(t, v)| {
                                        t.strip_prefix(&prefix)
                                            .filter(|leaf| !leaf.contains('/'))
                                            .map(|leaf| (leaf.to_string(), v.clone()))
                                    })
                                    .collect();
                                if let Some(obj) = parsed_json.as_object_mut() {
                                    for (name, value) in siblings {
                                        obj.entry(name).or_insert(value);
                                    }
                                }
                            }

                            let msg = crate::models::IncomingMessage {
                                handler: String::new(),
                                yak_handler: Some(yak.clone()),
                                model: model_str.clone(),
                                device: model_str,
                                extra: parsed_json,
                            };

                            let yak_type = yak.yak_type.to_lowercase();
                            match yak_type.as_str() {
                                "set" => verbs::set::handle(&client, &config, &msg, &repo).await,
                                "rig" => verbs::rig::handle(&client, &config, &msg, &repo).await,
                                "nab" => verbs::nab::handle(&client, &config, &msg, &repo).await,
                                "do"  => verbs::do_cmd::handle(&client, &config, &msg, &repo).await,
                                other => eprintln!("   ⚠️ [YAK] Unknown yak_type: {}", other),
                            }
                        }
                    }
                }
            }

            Ok(Event::Incoming(Incoming::ConnAck(_))) => {
                eprintln!("   ✅ [YAK AGENT] Connected successfully to the MQTT broker.");
            }
            Ok(_) => {} // Ignore other MQTT events
            Err(e) => {
                error!("MQTT Connection error: {:?}", e);
                tokio::time::sleep(Duration::from_secs(1)).await;
            }
        }
    }
}
