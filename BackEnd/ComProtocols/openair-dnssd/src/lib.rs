//! openair-dnssd — DNS-SD / mDNS (Bonjour, Zeroconf) discovery agent.
//!
//! Was a 25-line stub; now browses the network for real. Strategy: browse
//! the meta-service `_services._dns-sd._udp.local.` to enumerate every
//! advertised service TYPE, then browse each type and publish one retained
//! topic per attribute of every resolved instance:
//!
//!   OpenAir/System/Protocols/dnssd/Device/{service_type}/{instance}/{key}
//!
//! (the same v40 field-per-topic shape the Discovered-tab builder sweeps —
//! Phase 4's Device Registry replaces this with one DeviceRecord document,
//! see contracts D1). Browsing is continuous: services appearing later
//! refresh the retained tree, vanished services clear it; the Discovered
//! tab's RESCAN button re-runs the builder, which sweeps whatever is
//! retained at that moment.

use mdns_sd::{ServiceDaemon, ServiceEvent};
use std::collections::HashSet;
use std::time::Duration;

const META_QUERY: &str = "_services._dns-sd._udp.local.";

const DEVICE_KEYS: [&str; 8] =
    ["service_type", "instance", "hostname", "addresses", "port", "txt", "status", "last_online"];

/// MQTT topic segment: strip `.local.`, replace anything the topic grammar
/// rejects (spaces, `/ + #`, dots) with `_`.
fn seg(raw: &str) -> String {
    let trimmed = raw
        .trim_end_matches('.')
        .trim_end_matches("local")
        .trim_end_matches('.');
    let cleaned: String = trimmed
        .chars()
        .map(|c| if c.is_ascii_alphanumeric() || c == '-' || c == '_' { c } else { '_' })
        .collect();
    if cleaned.is_empty() { "_".to_string() } else { cleaned }
}

/// Blocking browse loop — run on a dedicated thread. Publishes retained
/// discovery topics to the local broker as services resolve or vanish.
pub fn run_browse_agent(mqtt_host: &str, mqtt_port: u16) {
    let mut mqttoptions = rumqttc::MqttOptions::new("open-air-dnssd", mqtt_host, mqtt_port);
    mqttoptions.set_keep_alive(Duration::from_secs(30));
    let (mqtt_client, mut connection) = rumqttc::Client::new(mqttoptions, 64);
    std::thread::spawn(move || {
        for _ in connection.iter() {} // drive the eventloop forever
    });

    let daemon = match ServiceDaemon::new() {
        Ok(d) => d,
        Err(e) => {
            eprintln!("🛑 [DNSSD] cannot start mDNS daemon: {e}");
            return;
        }
    };

    let meta = match daemon.browse(META_QUERY) {
        Ok(rx) => rx,
        Err(e) => {
            eprintln!("🛑 [DNSSD] meta-browse failed: {e}");
            return;
        }
    };

    println!("🔎 [DNSSD] Browsing {META_QUERY} for service types...");
    let (found_tx, found_rx) = std::sync::mpsc::channel::<ServiceEvent>();

    // Meta-query listener: every advertised service type spawns a per-type
    // browse whose events funnel into the single publisher channel below.
    {
        let daemon = daemon.clone();
        let found_tx = found_tx.clone();
        std::thread::spawn(move || {
            let mut browsing: HashSet<String> = HashSet::new();
            while let Ok(event) = meta.recv() {
                if let ServiceEvent::ServiceFound(_, fullname) = event {
                    if browsing.insert(fullname.clone()) {
                        println!("   🔎 [DNSSD] service type discovered: {fullname}");
                        if let Ok(rx) = daemon.browse(&fullname) {
                            let tx = found_tx.clone();
                            std::thread::spawn(move || {
                                while let Ok(ev) = rx.recv() {
                                    let _ = tx.send(ev);
                                }
                            });
                        }
                    }
                }
            }
        });
    }

    // Publisher: resolved instances become retained attribute topics.
    while let Ok(event) = found_rx.recv() {
        match event {
            ServiceEvent::ServiceResolved(info) => {
                let stype = seg(&info.ty_domain);
                let instance = seg(info.fullname.trim_end_matches(&info.ty_domain));
                let prefix =
                    format!("OpenAir/System/Protocols/dnssd/Device/{stype}/{instance}");

                let mut addresses: Vec<String> =
                    info.addresses.iter().map(|a| a.to_string()).collect();
                addresses.sort();
                let txt: Vec<String> = info
                    .txt_properties
                    .iter()
                    .map(|p| format!("{}={}", p.key(), p.val_str()))
                    .collect();
                let now_secs = std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .map(|d| d.as_secs())
                    .unwrap_or(0);

                let values = [
                    info.ty_domain.trim_end_matches('.').to_string(),
                    info.fullname.clone(),
                    info.host.trim_end_matches('.').to_string(),
                    addresses.join(", "),
                    info.port.to_string(),
                    if txt.is_empty() { "-".to_string() } else { txt.join(" | ") },
                    "identified".to_string(),
                    now_secs.to_string(),
                ];
                println!(
                    "   ✅ [DNSSD] resolved {} @ {}:{}",
                    info.fullname, info.host, info.port
                );
                for (key, value) in DEVICE_KEYS.iter().zip(values) {
                    let _ = mqtt_client.publish(
                        format!("{prefix}/{key}"),
                        rumqttc::QoS::AtLeastOnce,
                        true,
                        value.into_bytes(),
                    );
                }
            }
            ServiceEvent::ServiceRemoved(stype, fullname) => {
                // Empty retained payload = delete: vanished services leave
                // no ghosts in the Discovered tab.
                let s = seg(&stype);
                let instance = seg(fullname.trim_end_matches(&stype));
                let prefix = format!("OpenAir/System/Protocols/dnssd/Device/{s}/{instance}");
                println!("   👋 [DNSSD] removed {fullname}");
                for key in DEVICE_KEYS {
                    let _ = mqtt_client.publish(
                        format!("{prefix}/{key}"),
                        rumqttc::QoS::AtLeastOnce,
                        true,
                        Vec::new(),
                    );
                }
            }
            _ => {}
        }
    }
}
