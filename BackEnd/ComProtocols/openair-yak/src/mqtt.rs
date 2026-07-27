use crate::config::Config;
use crate::verbs;
use crate::repository::YakRepository;
use log::{info, error};
use rumqttc::{AsyncClient, MqttOptions, QoS, Event, Incoming};
use std::time::Duration;
use std::sync::Arc;
use std::collections::HashMap;

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
                
                if let Ok(mut parsed_json) = json_val {
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
                        // Execution Payload
                        if let Some(yak) = topic_configs.get(&p.topic) {
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
