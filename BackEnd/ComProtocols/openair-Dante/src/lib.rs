//! `openair-dante` — Dante discovery, in both of its personalities.
//!
//! Dante announces itself two entirely different ways depending on what it is
//! talking to, and this agent watches both — labelling each result with **how**
//! it was found, because that difference is operationally meaningful.
//!
//! # 1. Native Dante — mDNS
//!
//! Dante uses mDNS with Audinate's proprietary service tags:
//!
//! | Service | Meaning |
//! |---|---|
//! | `_netaudio-arc._udp` | Audinate Routing Control — the device's control endpoint |
//! | `_netaudio-cmc._udp` | Conmon control |
//! | `_netaudio-dbc._udp` | Device browsing/config |
//! | `_netaudio-chan._udp` | Per-channel advertisements |
//!
//! This is how Dante Controller populates its routing matrix. It is enough to
//! *find and describe* a device — but connection management is proprietary, so
//! unlike RAVENNA there is no SDP to read and no standard way to subscribe.
//! This agent therefore reports what a Dante device **is**, not what it streams.
//!
//! # 2. AES67 mode — SAP, and why it is NOT handled here
//!
//! Tick "Enable AES67" in Dante Controller and the device stops describing those
//! streams over mDNS entirely, and starts pushing SDP payloads to the SAP
//! multicast group `239.255.255.255:9875`.
//!
//! That half lives in **`openair-sap`**, not here, for two reasons:
//!
//! 1. **SAP is vendor-neutral.** Anything announcing AES67 over SAP lands on
//!    that group — RAVENNA gear, RAV2SAP translators, Dante in AES67 mode. A
//!    listener that filed all of it under "Dante" would be mislabelling most of
//!    it. What SAP tells you is *how it was announced*, never who made it.
//! 2. **One socket, one owner.** Two agents cannot both bind UDP 9875; the
//!    second silently gets nothing. This agent originally shipped its own
//!    listener and collided with `openair-sap` — the Dante stream tab stayed
//!    empty while SAP quietly worked. Duplicated listeners fail this way.
//!
//! So: Dante devices appear in the `dante` tab (found over mDNS); AES67 streams
//! — Dante's or anyone else's — appear in the `sap` tab.

pub mod sap;

use mdns_sd::{ServiceDaemon, ServiceEvent};
use std::time::Duration;

/// Audinate's proprietary mDNS service tags.
const DANTE_SERVICES: [&str; 4] = [
    "_netaudio-arc._udp.local.",
    "_netaudio-cmc._udp.local.",
    "_netaudio-dbc._udp.local.",
    "_netaudio-chan._udp.local.",
];

/// SAP multicast group and port (RFC 2974 / AES67).

/// Retained keys per Dante device (mDNS path).
/// `mac` and `vendor` are recovered, not advertised: Dante announces over mDNS,
/// which carries no hardware address, but a SLAAC IPv6 address holds the MAC in
/// its low 64 bits. `vendor` sits beside the device's OWN `manufacturer` claim
/// on purpose — `mf=PreSonus` is what the box says, the OUI is what IEEE
/// registered, and an OEM module in someone else's chassis makes them differ.
const DEVICE_KEYS: [&str; 13] = [
    "device", "manufacturer", "model", "discovery", "services",
    "channels", "addresses", "mac", "vendor", "port", "hostname", "status",
    "last_online",
];

/// Split a Dante mDNS instance name into (device, channel).
///
/// `_netaudio-chan` advertises ONE SERVICE PER CHANNEL, named
/// `Ch10@Metro16-DANTE2AVB`. Taking those at face value produced sixteen rows
/// for a single sixteen-channel interface — technically accurate, operationally
/// useless. The device is the part after `@`; the channel is counted instead.
fn split_instance(instance: &str) -> (String, Option<String>) {
    match instance.split_once('@') {
        Some((channel, device)) => (device.to_string(), Some(channel.to_string())),
        None => (instance.to_string(), None),
    }
}

/// Retained keys per Dante channel.
///
/// The per-channel TXT is genuinely useful — it is where the flow's real audio
/// parameters live, and they can differ from the device defaults. Summarising
/// channels to a count (as an earlier version did) threw that away.
const CHANNEL_KEYS: [&str; 10] = [
    "channel", "device", "id", "sample_rate", "bit_depth",
    "latency_ms", "frames_per_packet", "flow_channels", "redundancy", "last_online",
];

/// Nanoseconds -> milliseconds, kept human. Dante reports `latency_ns=1000000`;
/// "1 ms" is what an engineer thinks in.
fn latency_ms(ns: &str) -> String {
    match ns.trim().parse::<f64>() {
        Ok(v) if v > 0.0 => {
            let ms = v / 1_000_000.0;
            if (ms - ms.round()).abs() < 0.001 { format!("{}", ms.round() as i64) }
            else { format!("{ms:.3}") }
        }
        _ => "-".to_string(),
    }
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

/// Blocking mDNS browse loop — run on a dedicated thread.
///
/// Spawns the SAP listener alongside it, so one call starts both personalities.
pub fn run_browse_agent(mqtt_host: &str, mqtt_port: u16) {
    let mut opts = rumqttc::MqttOptions::new("open-air-dante", mqtt_host, mqtt_port);
    opts.set_keep_alive(Duration::from_secs(30));
    let (mqtt_client, mut connection) = rumqttc::Client::new(opts, 32);
    let vendors = openair_maclookup::MacVendors::start();
    std::thread::spawn(move || {
        for _ in connection.iter() {}
    });

    let mdns = match ServiceDaemon::new() {
        Ok(d) => d,
        Err(e) => {
            eprintln!("❌ [DANTE] could not start mDNS daemon: {e}");
            return;
        }
    };

    let (tx, rx) = std::sync::mpsc::channel::<(String, ServiceEvent)>();
    for stype in DANTE_SERVICES {
        match mdns.browse(stype) {
            Ok(receiver) => {
                let tx = tx.clone();
                std::thread::spawn(move || {
                    while let Ok(ev) = receiver.recv() {
                        if tx.send((stype.to_string(), ev)).is_err() {
                            break;
                        }
                    }
                });
            }
            Err(e) => eprintln!("   ⚠️  [DANTE] cannot browse {stype}: {e}"),
        }
    }
    drop(tx);

    println!("🚀 [DANTE] browsing {:?}", DANTE_SERVICES);

    // A Dante device advertises several of these services; accumulate which ones
    // each device offers so the table shows one row per device, not four.
    let mut services_seen: std::collections::HashMap<String, std::collections::BTreeSet<String>> =
        std::collections::HashMap::new();
    // Channel names per device, so 16 `_netaudio-chan` advertisements become a
    // channel COUNT on one device row rather than 16 rows.
    let mut channels_seen: std::collections::HashMap<String, std::collections::BTreeSet<String>> =
        std::collections::HashMap::new();
    // Identity arrives on the `arc` service; `chan` advertisements carry none.
    // Remember the good values so a later channel update cannot overwrite them
    // with "Unknown".
    let mut identity_seen: std::collections::HashMap<String, (String, String)> =
        std::collections::HashMap::new();

    while let Ok((stype, event)) = rx.recv() {
        if let ServiceEvent::ServiceResolved(info) = event {
            let addresses: Vec<String> =
                info.get_addresses().iter().map(|a| a.to_string()).collect();
            let host = info.get_hostname().trim_end_matches('.').to_string();
            let fullname = info.get_fullname().to_string();
            let instance = fullname
                .split_once("._")
                .map(|(s, _)| s.to_string())
                .unwrap_or_else(|| fullname.clone());
            let (device, channel) = split_instance(&instance);
            if let Some(ch) = channel.clone() {
                channels_seen.entry(device.clone()).or_default().insert(ch);
            }

            // Short tag: "_netaudio-arc._udp.local." -> "arc"
            let tag = stype
                .trim_start_matches("_netaudio-")
                .split('.')
                .next()
                .unwrap_or(&stype)
                .to_string();
            let entry = services_seen.entry(device.clone()).or_default();
            entry.insert(tag);
            let services = entry.iter().cloned().collect::<Vec<_>>().join(", ");

            // TXT carries the useful identity: mf=PreSonus, model=…, versions.
            let mut txt = std::collections::HashMap::new();
            for prop in info.get_properties().iter() {
                txt.insert(prop.key().to_ascii_lowercase(), prop.val_str().to_string());
            }
            let get = |k: &str| txt.get(k).cloned().unwrap_or_default();
            // Only the `arc` service carries mf/model. Keep the best value seen
            // so far rather than letting a channel advertisement blank it out.
            let mf_now = get("mf");
            let model_now = {
                let m = get("model");
                let info_s = get("router_info");
                if !info_s.is_empty() { info_s } else { m }
            };
            let known = identity_seen.entry(device.clone()).or_default();
            if !mf_now.is_empty() { known.0 = mf_now; }
            if !model_now.is_empty() { known.1 = model_now; }
            let manufacturer = if known.0.is_empty() { "Unknown".to_string() } else { known.0.clone() };
            let model = if known.1.is_empty() { "Unknown".to_string() } else { known.1.clone() };
            let channel_count = channels_seen.get(&device).map(|c| c.len()).unwrap_or(0);

            // Channel advertisement: publish its own parameters UNDER the device,
            // then stop — a channel is not a device and must not overwrite the
            // device row's identity with its own thinner TXT.
            if let Some(ch) = channel {
                let mut ctxt = std::collections::HashMap::new();
                for prop in info.get_properties().iter() {
                    ctxt.insert(prop.key().to_ascii_lowercase(), prop.val_str().to_string());
                }
                let cg = |k: &str| ctxt.get(k).cloned().unwrap_or_default();
                let cprefix = format!(
                    "OpenAir/System/Protocols/dante/Device/{}/Channel/{}",
                    seg(&device), seg(&ch)
                );
                let cvalues = [
                    ch.clone(),
                    device.clone(),
                    cg("id"),
                    cg("rate"),
                    { let e = cg("enc"); if e.is_empty() { cg("en") } else { e } },
                    latency_ms(&cg("latency_ns")),
                    cg("fpp"),
                    cg("nchan"),
                    cg("nred"),
                    now_secs().to_string(),
                ];
                for (key, value) in CHANNEL_KEYS.iter().zip(cvalues) {
                    let _ = mqtt_client.publish(
                        format!("{cprefix}/{key}"),
                        rumqttc::QoS::AtLeastOnce,
                        true,
                        value.into_bytes(),
                    );
                }
                continue;
            }

            let prefix = format!(
                "OpenAir/System/Protocols/dante/Device/{}",
                seg(&device)
            );
            let values = [
                device.clone(),
                manufacturer,
                model,
                "Dante (mDNS)".to_string(),
                services,
                if channel_count > 0 { channel_count.to_string() } else { "-".to_string() },
                addresses.join(", "),
                vendors
                    .mac_of_any(addresses.iter().map(String::as_str))
                    .map(|m| m.to_string())
                    .unwrap_or_else(|| "-".to_string()),
                vendors
                    .vendor_of_any(addresses.iter().map(String::as_str))
                    .unwrap_or_else(|| "-".to_string()),
                info.get_port().to_string(),
                host.clone(),
                "identified".to_string(),
                now_secs().to_string(),
            ];
            println!("   ✅ [DANTE] {device} @ {host} — services: {}, channels: {channel_count}",
                services_seen.get(&device).map(|s| s.len()).unwrap_or(0));
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
}

#[cfg(test)]
mod tests {
    use super::*;

    /// The bug this guards: a 16-channel interface produced 16 device rows.
    #[test]
    fn channel_advertisements_resolve_to_their_device() {
        assert_eq!(
            split_instance("Ch10@Metro16-DANTE2AVB"),
            ("Metro16-DANTE2AVB".to_string(), Some("Ch10".to_string()))
        );
        // A device-level service has no channel part.
        assert_eq!(
            split_instance("Metro16-DANTE2AVB"),
            ("Metro16-DANTE2AVB".to_string(), None)
        );
    }

    #[test]
    fn latency_is_reported_in_milliseconds() {
        // Dante's own value from the bench.
        assert_eq!(latency_ms("1000000"), "1");
        assert_eq!(latency_ms("250000"), "0.250");
        assert_eq!(latency_ms(""), "-");
        assert_eq!(latency_ms("garbage"), "-");
    }

    #[test]
    fn seg_neutralises_topic_metacharacters() {
        assert_eq!(seg("Metro16-DANTE2AVB"), "Metro16-DANTE2AVB");
        assert_eq!(seg("Digital inputs 1-2"), "Digital_inputs_1-2");
        assert_eq!(seg("a/b+c#d"), "a_b_c_d");
    }

    /// End-to-end: a real SAP packet must yield usable stream properties.
    #[test]
    fn sap_packet_yields_stream_properties() {
        let sdp_text = "v=0\no=- 6 0 IN IP4 44.44.44.173\ns=Digital inputs 1-2\n\
                        c=IN IP4 239.5.44.173/1\nm=audio 5004 RTP/AVP 98\n\
                        a=rtpmap:98 L24/48000/2\na=ptime:1\n";
        let mut pkt = vec![0x20u8, 0, 0x12, 0x34, 44, 44, 44, 173];
        pkt.extend_from_slice(b"application/sdp\0");
        pkt.extend_from_slice(sdp_text.as_bytes());

        let ann = sap::parse(&pkt).expect("valid SAP");
        assert_eq!(ann.origin, "44.44.44.173");
        let stream = sdp::parse(&ann.sdp);
        assert!(stream.is_audio);
        assert_eq!(stream.sample_rate, 48000);
        assert_eq!(stream.channels, 2);
        assert_eq!(stream.destination, "239.5.44.173");
        assert_eq!(stream.format_summary(), "L24 48000Hz 2ch");
    }
}
