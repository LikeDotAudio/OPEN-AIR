//! `openair-chromecast` — Google Cast device **discovery**.
//!
//! Browses `_googlecast._tcp` and publishes one retained topic tree per device,
//! with the mDNS TXT record decoded into named properties rather than left as an
//! opaque `k=v | k=v` blob.
//!
//! # Scope: discovery only, deliberately
//!
//! No control is implemented. Sending commands (volume, launch app, media
//! transport) means speaking **Cast V2**: a TLS socket to port 8009, a constant
//! heartbeat, and protobuf messages multiplexed over virtual channels
//! (`urn:x-cast:com.google.cast.{tp.heartbeat,tp.connection,receiver,media}`).
//! That is a substantial protocol implementation — the `rust-cast` crate exists
//! for it — and it is not needed to answer the question this agent answers:
//! *what Cast hardware is on this network, and what can it do?*
//!
//! Discovery is also the cheap half: it is passive, needs no pairing, and cannot
//! disturb a device someone is listening to.
//!
//! # Why not just read the DNS-SD agent's output?
//!
//! `openair-dnssd` already sees these devices — it browses every service type —
//! but it publishes the TXT record verbatim, because it cannot know what any
//! given service's keys mean. Cast TXT keys are well defined, so this agent
//! turns them into columns you can sort a table by: friendly name, model,
//! capabilities, status. That is the difference between "42 services found" and
//! "a Nest Mini in the garage that is audio-out only and currently idle".

use mdns_sd::{ServiceDaemon, ServiceEvent};

/// The one service type Cast hardware advertises.
const CAST_SERVICE: &str = "_googlecast._tcp.local.";

/// Retained attribute keys published per device. The Discovered-tab builder
/// renders these as columns, so order here is the natural column order.
const DEVICE_KEYS: [&str; 12] = [
    "friendly_name",
    "model",
    "device_type",
    "capabilities",
    "addresses",
    "port",
    "hostname",
    "cast_id",
    "protocol_version",
    "status_text",
    "status",
    "last_online",
];

/// Sanitise a string for use as one MQTT topic segment.
///
/// `/` would fork the topic tree and `+`/`#` are wildcards; Cast friendly names
/// are user-set ("Garage speaker", "Living Room TV") so they contain spaces and
/// occasionally worse.
fn seg(raw: &str) -> String {
    raw.trim()
        .trim_end_matches('.')
        .replace(['/', '+', '#'], "_")
        .replace(' ', "_")
}

/// Decode the Cast `ca` capability bitmask into human-readable flags.
///
/// Only the low bits are publicly documented and stable; higher bits vary by
/// firmware and are not guessed at here. The raw value is always published
/// alongside so nothing is lost to this interpretation — a wrong guess dressed
/// as a fact would be worse than an undecoded number.
fn decode_capabilities(ca: u64) -> String {
    const FLAGS: [(u64, &str); 6] = [
        (1 << 0, "video_out"),
        (1 << 1, "video_in"),
        (1 << 2, "audio_out"),
        (1 << 3, "audio_in"),
        (1 << 4, "dev_mode"),
        (1 << 5, "multizone_group"),
    ];
    let mut out: Vec<&str> = FLAGS
        .iter()
        .filter(|(bit, _)| ca & bit != 0)
        .map(|(_, name)| *name)
        .collect();
    if out.is_empty() {
        return format!("raw:{ca}");
    }
    // Keep the raw value visible: the decoded flags are a subset of the truth.
    out.push("…");
    format!("{} (raw:{})", out.join(", "), ca)
}

/// Classify a device from its model string, for grouping in the UI.
///
/// Model (`md`) is a free-text marketing name, so this is a best-effort bucket,
/// not an identity. Anything unrecognised lands in "Cast Device" rather than
/// being forced into a category it may not belong to.
fn categorise(model: &str, capabilities: u64) -> &'static str {
    let m = model.to_ascii_lowercase();
    if m.contains("group") {
        return "Speaker Group";
    }
    if m.contains("nest hub") || m.contains("home hub") {
        return "Smart Display";
    }
    if m.contains("chromecast") || m.contains("android tv") || m.contains("google tv") {
        return "Video Cast";
    }
    if m.contains("nest mini") || m.contains("home mini") || m.contains("nest audio") || m.contains("google home") {
        return "Speaker";
    }
    // Fall back to the capability bits: audio-out without video-out is a speaker.
    let video_out = capabilities & 1 != 0;
    let audio_out = capabilities & 4 != 0;
    match (video_out, audio_out) {
        (true, _) => "Video Cast",
        (false, true) => "Speaker",
        _ => "Cast Device",
    }
}

/// Blocking browse loop — run this on a dedicated thread.
///
/// Publishes retained device topics as devices resolve, and clears them (empty
/// retained payload) when a device leaves, so the Discovered tab reflects what
/// is actually present rather than everything ever seen.
pub fn run_browse_agent(mqtt_host: &str, mqtt_port: u16) {
    let mut opts = rumqttc::MqttOptions::new("open-air-chromecast", mqtt_host, mqtt_port);
    opts.set_keep_alive(std::time::Duration::from_secs(30));
    let (mqtt_client, mut connection) = rumqttc::Client::new(opts, 32);
    std::thread::spawn(move || {
        for _ in connection.iter() {}
    });

    let mdns = match ServiceDaemon::new() {
        Ok(d) => d,
        Err(e) => {
            eprintln!("❌ [CAST] could not start mDNS daemon: {e}");
            return;
        }
    };

    let receiver = match mdns.browse(CAST_SERVICE) {
        Ok(r) => r,
        Err(e) => {
            eprintln!("❌ [CAST] could not browse {CAST_SERVICE}: {e}");
            return;
        }
    };

    println!("🚀 [CAST] browsing {CAST_SERVICE} (discovery only — no control)");

    while let Ok(event) = receiver.recv() {
        match event {
            ServiceEvent::ServiceResolved(info) => {
                // TXT keys are Cast-defined:
                //   fn = friendly name   md = model         id = device id
                //   ve = protocol ver    ca = capabilities  rs = status text
                let mut txt: std::collections::HashMap<String, String> =
                    std::collections::HashMap::new();
                for prop in info.get_properties().iter() {
                    txt.insert(prop.key().to_ascii_lowercase(), prop.val_str().to_string());
                }
                let get = |k: &str| txt.get(k).cloned().unwrap_or_default();

                let friendly = {
                    let f = get("fn");
                    if f.is_empty() { seg(&info.get_fullname().to_string()) } else { f }
                };
                let model = get("md");
                let ca: u64 = get("ca").parse().unwrap_or(0);
                let category = categorise(&model, ca);

                let mut addresses: Vec<String> =
                    info.get_addresses().iter().map(|a| a.to_string()).collect();
                addresses.sort();

                let now_secs = std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .map(|d| d.as_secs())
                    .unwrap_or(0);

                let prefix = format!(
                    "OpenAir/System/Protocols/chromecast/Device/{}/{}",
                    seg(category),
                    seg(&friendly)
                );

                let values = [
                    friendly.clone(),
                    if model.is_empty() { "Unknown".into() } else { model.clone() },
                    category.to_string(),
                    decode_capabilities(ca),
                    addresses.join(", "),
                    info.get_port().to_string(),
                    info.get_hostname().trim_end_matches('.').to_string(),
                    get("id"),
                    get("ve"),
                    { let rs = get("rs"); if rs.is_empty() { "idle".into() } else { rs } },
                    "identified".to_string(),
                    now_secs.to_string(),
                ];

                println!(
                    "   ✅ [CAST] {} — {} ({}) @ {}:{}",
                    friendly,
                    if model.is_empty() { "unknown model" } else { &model },
                    category,
                    addresses.first().map(String::as_str).unwrap_or("?"),
                    info.get_port()
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
            ServiceEvent::ServiceRemoved(_stype, fullname) => {
                // A removal event does not carry the TXT record, so the category
                // it was filed under is unknown here. Clear the name under every
                // category rather than leave a ghost in whichever one it used.
                let instance = seg(fullname.trim_end_matches(CAST_SERVICE));
                println!("   👋 [CAST] removed {fullname}");
                for category in ["Speaker", "Video_Cast", "Smart_Display", "Speaker_Group", "Cast_Device"] {
                    let prefix = format!(
                        "OpenAir/System/Protocols/chromecast/Device/{category}/{instance}"
                    );
                    for key in DEVICE_KEYS {
                        let _ = mqtt_client.publish(
                            format!("{prefix}/{key}"),
                            rumqttc::QoS::AtLeastOnce,
                            true,
                            Vec::new(),
                        );
                    }
                }
            }
            _ => {}
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn capabilities_decode_known_bits() {
        assert!(decode_capabilities(4).starts_with("audio_out"));
        assert!(decode_capabilities(5).contains("video_out"));
        assert!(decode_capabilities(5).contains("audio_out"));
    }

    /// The raw value must survive decoding — the flag list is a subset of the
    /// truth, and a real device on this bench reports ca=198660.
    #[test]
    fn capabilities_always_keep_the_raw_value() {
        assert!(decode_capabilities(198660).contains("raw:198660"));
        assert!(decode_capabilities(0).contains("raw:0"));
    }

    #[test]
    fn categorise_prefers_model_then_falls_back_to_capabilities() {
        assert_eq!(categorise("Google Nest Mini", 4), "Speaker");
        assert_eq!(categorise("Chromecast Ultra", 5), "Video Cast");
        assert_eq!(categorise("Nest Hub Max", 5), "Smart Display");
        assert_eq!(categorise("Google Cast Group", 4), "Speaker Group");
        // Unknown model, audio-only bits -> Speaker via capabilities.
        assert_eq!(categorise("", 4), "Speaker");
        // Unknown model, no useful bits -> not forced into a category.
        assert_eq!(categorise("", 0), "Cast Device");
    }

    #[test]
    fn seg_neutralises_topic_metacharacters() {
        assert_eq!(seg("Garage speaker"), "Garage_speaker");
        assert_eq!(seg("a/b+c#d"), "a_b_c_d");
    }
}
