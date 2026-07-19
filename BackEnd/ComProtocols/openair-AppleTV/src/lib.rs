//! `openair-appletv` — Apple TV / AirPlay receiver discovery.
//!
//! An Apple TV is chatty on mDNS, and each service answers a different question:
//!
//! | Service | Port | What it tells you |
//! |---|---|---|
//! | `_airplay._tcp` | 7000 | AirPlay video / screen mirroring receiver |
//! | `_raop._tcp` | 7000 | AirPlay **audio** (Remote Audio Output Protocol) — the richest TXT |
//! | `_homekit._tcp` | ephemeral | HomeKit accessory (paired) |
//! | `_hap._tcp` | ephemeral | HomeKit Accessory Protocol |
//! | `_companion-link._tcp` | ephemeral | Continuity / Handoff |
//! | `_mediaremotetv._tcp` | ephemeral | Media Remote (the Remote app) |
//! | `_touch-able._tcp` | ephemeral | legacy DACP remote |
//! | `_sleep-proxy._udp` | ephemeral | Bonjour Sleep Proxy — it answers for sleeping devices |
//!
//! As with printers, that is **one device with many roles**, so this agent emits
//! one row per device and turns the service list into a `roles` column.
//! Grouping is by **hostname**, which every service shares.
//!
//! # What the `_raop` TXT actually carries
//!
//! ```text
//! am=AppleTV5,3     model identifier  -> decoded to a marketing name
//! ov=26.5           OS version (tvOS)
//! vs=950.7.1        AirPlay source version
//! cn=0,1,2,3        audio codecs      -> PCM, ALAC, AAC, AAC-ELD
//! md=0,1,2          metadata support  -> text, artwork, progress
//! et=0,3,5          encryption types
//! ft=0x5A7FDFD5,…   feature bitmask
//! pk=…              public key (pairing identity)
//! ```
//!
//! Codec and metadata lists are decoded because they are short, stable and
//! documented. The feature bitmask is **not** decoded: its bits are only partly
//! public and vary by tvOS release, so it is published raw rather than guessed
//! at — the same rule applied to the Cast capability mask.
//!
//! # Scope
//!
//! Discovery only. No pairing, no playback, no remote control. AirPlay control
//! requires the pairing/encryption handshake advertised by `pk`/`et`, which is a
//! protocol implementation in its own right and is not needed to answer "what
//! Apple hardware is on this network, and what will it accept?"

use mdns_sd::{ServiceDaemon, ServiceEvent};
use std::collections::{BTreeSet, HashMap};
use std::time::Duration;

/// Services an Apple TV (or other AirPlay receiver) advertises, with the short
/// role label used in the `roles` column.
const APPLE_SERVICES: [(&str, &str); 8] = [
    ("_airplay._tcp.local.", "airplay"),
    ("_raop._tcp.local.", "airplay-audio"),
    ("_homekit._tcp.local.", "homekit"),
    ("_hap._tcp.local.", "homekit-hap"),
    ("_companion-link._tcp.local.", "continuity"),
    ("_mediaremotetv._tcp.local.", "media-remote"),
    ("_touch-able._tcp.local.", "remote-legacy"),
    ("_sleep-proxy._udp.local.", "sleep-proxy"),
];

const DEVICE_KEYS: [&str; 12] = [
    "device",
    "model",
    "model_id",
    "os_version",
    "airplay_version",
    "roles",
    "audio_codecs",
    "metadata",
    "features_raw",
    "addresses",
    "status",
    "last_online",
];

/// Apple model identifiers seen on AirPlay receivers.
///
/// Only identifiers that are unambiguous are mapped. Anything unknown returns
/// the raw identifier rather than a guess — `AppleTV14,1` meaning nothing to
/// this table is better than it meaning the wrong thing.
pub fn decode_model(am: &str) -> String {
    let name = match am.trim() {
        "AppleTV3,1" | "AppleTV3,2" => "Apple TV (3rd gen)",
        "AppleTV5,3" => "Apple TV HD (4th gen)",
        "AppleTV6,2" => "Apple TV 4K (1st gen)",
        "AppleTV11,1" => "Apple TV 4K (2nd gen)",
        "AppleTV14,1" => "Apple TV 4K (3rd gen)",
        "AudioAccessory1,1" | "AudioAccessory1,2" => "HomePod",
        "AudioAccessory5,1" => "HomePod mini",
        "AudioAccessory6,1" => "HomePod (2nd gen)",
        "" => return "Unknown".to_string(),
        other => return other.to_string(),
    };
    name.to_string()
}

/// Decode the `cn` audio-codec list.
///
/// Documented and stable: 0=PCM, 1=ALAC, 2=AAC, 3=AAC-ELD.
pub fn decode_codecs(cn: &str) -> String {
    let mut out: Vec<&str> = Vec::new();
    for token in cn.split(',') {
        let name = match token.trim() {
            "0" => "PCM",
            "1" => "ALAC",
            "2" => "AAC",
            "3" => "AAC-ELD",
            "" => continue,
            _ => continue, // unknown code: silently skip rather than invent
        };
        if !out.contains(&name) {
            out.push(name);
        }
    }
    if out.is_empty() { "-".to_string() } else { out.join(", ") }
}

/// Decode the `md` metadata-capability list: 0=text, 1=artwork, 2=progress.
pub fn decode_metadata(md: &str) -> String {
    let mut out: Vec<&str> = Vec::new();
    for token in md.split(',') {
        let name = match token.trim() {
            "0" => "text",
            "1" => "artwork",
            "2" => "progress",
            _ => continue,
        };
        if !out.contains(&name) {
            out.push(name);
        }
    }
    if out.is_empty() { "-".to_string() } else { out.join(", ") }
}

fn seg(raw: &str) -> String {
    raw.trim()
        .trim_end_matches('.')
        .replace(['/', '+', '#'], "_")
        .replace(' ', "_")
}

fn now_secs() -> u64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0)
}

#[derive(Default, Clone)]
struct Device {
    name: String,
    txt: HashMap<String, String>,
    roles: BTreeSet<String>,
    addresses: BTreeSet<String>,
}

/// Blocking browse loop — run on a dedicated thread.
pub fn run_browse_agent(mqtt_host: &str, mqtt_port: u16) {
    let mut opts = rumqttc::MqttOptions::new("open-air-appletv", mqtt_host, mqtt_port);
    opts.set_keep_alive(Duration::from_secs(30));
    let (mqtt_client, mut connection) = rumqttc::Client::new(opts, 32);
    std::thread::spawn(move || {
        for _ in connection.iter() {}
    });

    let mdns = match ServiceDaemon::new() {
        Ok(d) => d,
        Err(e) => {
            eprintln!("❌ [APPLETV] could not start mDNS daemon: {e}");
            return;
        }
    };

    let (tx, rx) = std::sync::mpsc::channel::<(String, ServiceEvent)>();
    for (stype, role) in APPLE_SERVICES {
        match mdns.browse(stype) {
            Ok(receiver) => {
                let tx = tx.clone();
                let role = role.to_string();
                std::thread::spawn(move || {
                    while let Ok(ev) = receiver.recv() {
                        if tx.send((role.clone(), ev)).is_err() {
                            break;
                        }
                    }
                });
            }
            Err(e) => eprintln!("   ⚠️  [APPLETV] cannot browse {stype}: {e}"),
        }
    }
    drop(tx);

    println!("🚀 [APPLETV] browsing AirPlay/HomeKit/Continuity (one row per device, not per role)");

    // Hostname is the join key: every service on one device shares it.
    let mut devices: HashMap<String, Device> = HashMap::new();

    while let Ok((role, event)) = rx.recv() {
        let ServiceEvent::ServiceResolved(info) = event else {
            continue;
        };
        let host = info.get_hostname().trim_end_matches('.').to_string();
        if host.is_empty() {
            continue;
        }

        let entry = devices.entry(host.clone()).or_default();
        entry.roles.insert(role.clone());
        for a in info.get_addresses() {
            let s = a.to_string();
            if s.contains('.') {
                entry.addresses.insert(s);
            }
        }
        // Merge TXT without clobbering: `_raop` carries the rich record, the
        // others are nearly empty. Last-write-wins would erase the good data.
        for prop in info.get_properties().iter() {
            let v = prop.val_str().to_string();
            if !v.is_empty() {
                entry.txt.entry(prop.key().to_ascii_lowercase()).or_insert(v);
            }
        }
        // Friendly name: `_raop` instances are `<mac>@<Name>`; everything else
        // uses the plain instance name.
        let fullname = info.get_fullname().to_string();
        let instance = fullname
            .split_once("._")
            .map(|(s, _)| s.to_string())
            .unwrap_or_default();
        let friendly = instance
            .split_once('@')
            .map(|(_, n)| n.to_string())
            .unwrap_or(instance);
        if !friendly.is_empty() && (entry.name.is_empty() || role == "airplay-audio") {
            entry.name = friendly;
        }

        let d = entry.clone();
        // Only publish once something has actually identified the device.
        // `_sleep-proxy` alone is a Bonjour feature, not an Apple TV — a router
        // can offer it, and claiming that as an Apple TV would be wrong.
        let identifying = d.roles.iter().any(|r| {
            matches!(r.as_str(), "airplay" | "airplay-audio" | "homekit" | "homekit-hap" | "media-remote")
        });
        if !identifying {
            continue;
        }

        let get = |k: &str| d.txt.get(k).cloned().unwrap_or_default();
        let model_id = get("am");
        let name = if d.name.is_empty() { host.clone() } else { d.name.clone() };

        let values = [
            name.clone(),
            decode_model(&model_id),
            if model_id.is_empty() { "-".into() } else { model_id.clone() },
            { let ov = get("ov"); if ov.is_empty() { "-".into() } else { ov } },
            { let vs = get("vs"); if vs.is_empty() { "-".into() } else { vs } },
            d.roles.iter().cloned().collect::<Vec<_>>().join(", "),
            decode_codecs(&get("cn")),
            decode_metadata(&get("md")),
            { let ft = get("ft"); if ft.is_empty() { "-".into() } else { ft } },
            d.addresses.iter().cloned().collect::<Vec<_>>().join(", "),
            "identified".to_string(),
            now_secs().to_string(),
        ];

        let prefix = format!("OpenAir/System/Protocols/appletv/Device/{}", seg(&name));
        println!(
            "   ✅ [APPLETV] {name} — {} ({}) roles: {}",
            decode_model(&model_id),
            if model_id.is_empty() { "?" } else { &model_id },
            d.roles.iter().cloned().collect::<Vec<_>>().join("/")
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
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn decodes_the_model_on_this_network() {
        // The Living Room unit.
        assert_eq!(decode_model("AppleTV5,3"), "Apple TV HD (4th gen)");
        assert_eq!(decode_model("AppleTV14,1"), "Apple TV 4K (3rd gen)");
        assert_eq!(decode_model("AudioAccessory5,1"), "HomePod mini");
    }

    /// An unknown identifier must survive verbatim, not become a wrong guess.
    #[test]
    fn unknown_models_pass_through_unchanged() {
        assert_eq!(decode_model("AppleTV99,9"), "AppleTV99,9");
        assert_eq!(decode_model("iPhone16,1"), "iPhone16,1");
        assert_eq!(decode_model(""), "Unknown");
    }

    #[test]
    fn decodes_the_real_codec_and_metadata_lists() {
        // cn=0,1,2,3 and md=0,1,2 from the bench.
        assert_eq!(decode_codecs("0,1,2,3"), "PCM, ALAC, AAC, AAC-ELD");
        assert_eq!(decode_metadata("0,1,2"), "text, artwork, progress");
        assert_eq!(decode_codecs(""), "-");
        assert_eq!(decode_metadata(""), "-");
    }

    /// Unrecognised codes are skipped rather than invented.
    #[test]
    fn unknown_codes_are_skipped_not_guessed() {
        assert_eq!(decode_codecs("0,99"), "PCM");
        assert_eq!(decode_metadata("7"), "-");
    }

    #[test]
    fn seg_neutralises_topic_metacharacters() {
        assert_eq!(seg("Living Room"), "Living_Room");
        assert_eq!(seg("a/b+c#d"), "a_b_c_d");
    }
}
