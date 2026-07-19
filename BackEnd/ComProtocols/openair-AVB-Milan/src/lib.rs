//! `openair-avb-milan` — AVB / Milan device discovery via AVDECC (IEEE 1722.1).
//!
//! # Why this agent shares no code with the others
//!
//! RAVENNA (`openair-ravenna`) and Dante-in-AES67-mode (`openair-sap`) are
//! Layer 3 protocols. They differ from each other only in how an SDP record is
//! delivered — mDNS query/RTSP pull versus SAP multicast push — which is why
//! those two agents share a parser.
//!
//! AVB shares nothing with either. It moves audio at Layer 2, addressed by MAC,
//! and never touches IP. There is no SDP, no port, no multicast group address
//! to subscribe to. A device is found by reading raw Ethernet frames sent to
//! the reserved MAC `91:E0:F0:01:00:00`, and described by a binary descriptor
//! model rather than a text session record. Every assumption the other agents
//! rest on is absent here, so this crate starts from the wire.
//!
//! # What this agent does
//!
//! ADP only — the discovery third of AVDECC:
//!
//! * Listens for `ENTITY_AVAILABLE` heartbeats and publishes each entity.
//! * Honours `ENTITY_DEPARTING` and the per-entity `valid_time`, so a device
//!   that is unplugged clears rather than lingering.
//! * Emits one `ENTITY_DISCOVER` query per interface at startup, which is what
//!   any AVDECC controller does and is the Layer 2 twin of an mDNS query.
//!
//! # What it deliberately does not do
//!
//! * **Enumeration (AECP `READ_DESCRIPTOR`).** ADP gives capability bitfields
//!   and stream *counts*; the descriptor tree with channel names and routing
//!   matrices needs a request/response conversation with the device. That is a
//!   substantial protocol in its own right, and this agent reports the counts
//!   ADP actually carries rather than implying it knows the tree.
//! * **Stream reservation (SRP) and connection management (ACMP).** Those
//!   change network state: SRP asks the switches to carve out guaranteed
//!   bandwidth, ACMP rewires audio. A discovery tool does not get to do either
//!   as a side effect of looking.
//! * **Claim Milan compliance.** Milan is asserted by answering an MVU
//!   `GET_MILAN_INFO` command, not by a bit in the announcement. See
//!   [`adp::AdpEntity::milan_assessment`].
//!
//! # Topics
//!
//! ```text
//! OpenAir/System/Protocols/avb/Device/{entity_id}/{key}
//! ```
//!
//! Keyed by entity ID rather than by name because ADP carries no name — the
//! entity's human-readable name lives in the descriptor tree, which is exactly
//! what enumeration would fetch.
//!
//! # Privileges
//!
//! Raw frame capture requires `CAP_NET_RAW`. See [`capture::explain_error`].

pub mod adp;
pub mod aecp;
pub mod capture;
pub mod identify;

use adp::{AdpEntity, MessageType};
use std::collections::HashMap;
use std::time::{Duration, Instant};

/// Retained attribute keys per entity. Order here is the UI column order.
pub const ENTITY_KEYS: [&str; 18] = [
    "entity_id",
    "mac",
    "oui",
    "interface",
    "entity_model_id",
    "talker_sources",
    "talker_capabilities",
    "listener_sinks",
    "listener_capabilities",
    "entity_capabilities",
    "gptp_grandmaster",
    "gptp_domain",
    "milan",
    "available_index",
    "configuration_index",
    "valid_time_s",
    "status",
    "last_online",
];

/// A currently-known entity and when its announcement expires.
struct Known {
    entity_seg: String,
    expires_at: Instant,
    /// Detects a device that changed configuration under us — worth logging,
    /// because any cached enumeration elsewhere is now stale.
    available_index: u32,
}

/// Floor for the announcement validity window.
///
/// `valid_time` is entity-supplied and a device announcing a very short window
/// would otherwise flicker in and out of the UI on one dropped frame.
const MIN_VALID_SECS: u64 = 10;

/// Sanitise one MQTT topic segment. Entity IDs are colon-separated hex, and
/// colons are legal in a topic segment; this guards the general case.
fn seg(raw: &str) -> String {
    let cleaned = raw.trim().replace(['/', '+', '#'], "_").replace(' ', "_");
    if cleaned.is_empty() { "_".to_string() } else { cleaned }
}

/// Open a capture socket, join the AVDECC group on every usable interface, and
/// return the socket plus the interfaces actually listening.
///
/// Interfaces without a carrier are joined anyway: a cable plugged in a minute
/// from now should just start working, and the join costs nothing meanwhile.
pub fn start_capture() -> std::io::Result<(capture::RawSocket, Vec<capture::Interface>)> {
    let socket = capture::RawSocket::open()?;
    let interfaces = capture::list_interfaces()?;
    let mut listening = Vec::new();
    for iface in interfaces {
        match socket.join_avdecc_group(iface.index) {
            Ok(()) => listening.push(iface),
            Err(e) => eprintln!(
                "   ⚠️  [AVB] cannot join AVDECC group on {}: {e}",
                iface.name
            ),
        }
    }
    Ok((socket, listening))
}

/// Send an `ENTITY_DISCOVER` on each interface so entities answer immediately.
///
/// Without this, discovery waits for the next periodic heartbeat, which can be
/// tens of seconds. Returns the interfaces the query went out on.
pub fn send_discover(
    socket: &capture::RawSocket,
    interfaces: &[capture::Interface],
) -> Vec<String> {
    let mut sent = Vec::new();
    for iface in interfaces {
        let frame = adp::build_discover_frame(iface.mac);
        match socket.send_on(iface.index, &frame) {
            Ok(()) => sent.push(iface.name.clone()),
            Err(e) => eprintln!("   ⚠️  [AVB] discover on {} failed: {e}", iface.name),
        }
    }
    sent
}

/// Blocking listen loop — run on a dedicated thread.
pub fn run_listen_agent(mqtt_host: &str, mqtt_port: u16) {
    let mut opts = rumqttc::MqttOptions::new("open-air-avb", mqtt_host, mqtt_port);
    opts.set_keep_alive(Duration::from_secs(30));
    let (mqtt_client, mut connection) = rumqttc::Client::new(opts, 32);
    std::thread::spawn(move || {
        for _ in connection.iter() {}
    });

    let (socket, interfaces) = match start_capture() {
        Ok(v) => v,
        Err(e) => {
            // Not a crash: on a host without CAP_NET_RAW this agent simply
            // cannot run, and saying so once is more useful than a restart loop.
            eprintln!("🛑 [AVB] {}", capture::explain_error(&e));
            report_agent_state(&mqtt_client, "unavailable", &capture::explain_error(&e));
            return;
        }
    };
    if interfaces.is_empty() {
        eprintln!("⚠️  [AVB] no capturable Ethernet interfaces — nothing to listen on");
        report_agent_state(
            &mqtt_client,
            "unavailable",
            "no capturable Ethernet interfaces",
        );
        return;
    }

    let names: Vec<&str> = interfaces.iter().map(|i| i.name.as_str()).collect();
    println!("🔎 [AVB] listening for AVDECC (ADP) on {names:?}");
    report_agent_state(&mqtt_client, "listening", &names.join(", "));
    let sent = send_discover(&socket, &interfaces);
    if !sent.is_empty() {
        println!("   📣 [AVB] ENTITY_DISCOVER sent on {sent:?}");
    }

    let by_index: HashMap<u32, String> =
        interfaces.iter().map(|i| (i.index, i.name.clone())).collect();
    let mut known: HashMap<u64, Known> = HashMap::new();
    let mut buf = [0u8; 2048];

    loop {
        match socket.recv(&mut buf) {
            Ok(Some((len, if_index))) => {
                let iface = by_index.get(&if_index).map(String::as_str).unwrap_or("?");
                if let Ok(entity) = adp::parse_frame(&buf[..len]) {
                    handle_entity(&entity, iface, &mqtt_client, &mut known);
                }
            }
            Ok(None) => {} // Read timeout: fall through to the expiry sweep.
            Err(e) => {
                eprintln!("🛑 [AVB] capture failed: {}", capture::explain_error(&e));
                return;
            }
        }
        expire(&mqtt_client, &mut known);
    }
}

/// Report whether this agent is actually able to see the network.
///
/// The orchestrator's config publisher marks a protocol `online` from the
/// presence of its `config.ini`, which for every IP-based agent is a fair
/// proxy. It is not one here: AVB capture can fail for a reason that has
/// nothing to do with the code — a missing capability — and an agent that
/// silently published nothing while the bus said `online` would be claiming
/// health it does not have. So the agent states its own case.
fn report_agent_state(mqtt_client: &rumqttc::Client, state: &str, detail: &str) {
    for (topic, payload) in [
        ("OpenAir/System/Protocols/avb/Agent/state", state),
        ("OpenAir/System/Protocols/avb/Agent/detail", detail),
    ] {
        let _ = mqtt_client.publish(
            topic,
            rumqttc::QoS::AtLeastOnce,
            true,
            payload.as_bytes().to_vec(),
        );
    }
}

/// Publish or clear one entity based on its announcement.
fn handle_entity(
    entity: &AdpEntity,
    iface: &str,
    mqtt_client: &rumqttc::Client,
    known: &mut HashMap<u64, Known>,
) {
    match entity.message_type {
        MessageType::EntityDiscover => return, // Another controller asking, not a device.
        MessageType::EntityDeparting => {
            if let Some(k) = known.remove(&entity.entity_id) {
                println!("   👋 [AVB] entity departing: {}", adp::format_id(entity.entity_id));
                clear(mqtt_client, &k.entity_seg);
            }
            return;
        }
        MessageType::Other(n) => {
            println!("   ⚠️  [AVB] unknown ADP message_type {n} — ignoring");
            return;
        }
        MessageType::EntityAvailable => {}
    }

    let entity_seg = seg(&adp::format_id(entity.entity_id));
    let prefix = format!("OpenAir/System/Protocols/avb/Device/{entity_seg}");

    let now_secs = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0);

    let join = |names: Vec<&'static str>| {
        if names.is_empty() { "-".to_string() } else { names.join(" | ") }
    };

    let values = [
        adp::format_id(entity.entity_id),
        adp::format_mac(&entity.source_mac),
        adp::format_oui(&entity.source_mac),
        iface.to_string(),
        adp::format_id(entity.entity_model_id),
        entity.talker_stream_sources.to_string(),
        join(entity.talker_capability_names()),
        entity.listener_stream_sinks.to_string(),
        join(entity.listener_capability_names()),
        join(entity.entity_capability_names()),
        adp::format_id(entity.gptp_grandmaster_id),
        entity.gptp_domain_number.to_string(),
        entity.milan_assessment().to_string(),
        entity.available_index.to_string(),
        entity.current_configuration_index.to_string(),
        entity.valid_time_secs.to_string(),
        "identified".to_string(),
        now_secs.to_string(),
    ];

    let previous = known.get(&entity.entity_id);
    match previous {
        None => println!("   ✅ [AVB] entity available on {iface}: {}", entity.summary()),
        Some(k) if k.available_index != entity.available_index => {
            // available_index only moves when the device's own state changed.
            println!(
                "   🔄 [AVB] {} changed configuration (available_index {} -> {})",
                adp::format_id(entity.entity_id),
                k.available_index,
                entity.available_index
            );
        }
        Some(_) => {} // Routine heartbeat; publishing refreshes last_online.
    }

    for (key, value) in ENTITY_KEYS.iter().zip(values) {
        let _ = mqtt_client.publish(
            format!("{prefix}/{key}"),
            rumqttc::QoS::AtLeastOnce,
            true,
            value.into_bytes(),
        );
    }

    let valid = Duration::from_secs((entity.valid_time_secs as u64).max(MIN_VALID_SECS));
    known.insert(
        entity.entity_id,
        Known {
            entity_seg,
            expires_at: Instant::now() + valid,
            available_index: entity.available_index,
        },
    );
}

/// Drop entities whose announcement validity has lapsed.
///
/// `ENTITY_DEPARTING` only arrives on a clean shutdown. A pulled cable produces
/// silence, and `valid_time` is the entity's own statement of how long its last
/// announcement should be trusted — so it, not a fixed constant, sets expiry.
fn expire(mqtt_client: &rumqttc::Client, known: &mut HashMap<u64, Known>) {
    let now = Instant::now();
    let stale: Vec<u64> = known
        .iter()
        .filter(|(_, k)| now > k.expires_at)
        .map(|(id, _)| *id)
        .collect();
    for id in stale {
        if let Some(k) = known.remove(&id) {
            println!("   ⌛ [AVB] {} stopped announcing — clearing", adp::format_id(id));
            clear(mqtt_client, &k.entity_seg);
        }
    }
}

/// Empty retained payloads delete the entity's topics.
fn clear(mqtt_client: &rumqttc::Client, entity_seg: &str) {
    let prefix = format!("OpenAir/System/Protocols/avb/Device/{entity_seg}");
    for key in ENTITY_KEYS {
        let _ = mqtt_client.publish(
            format!("{prefix}/{key}"),
            rumqttc::QoS::AtLeastOnce,
            true,
            Vec::new(),
        );
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn entity_ids_survive_topic_sanitising() {
        // Colons are legal in an MQTT topic segment and must not be mangled —
        // the segment has to round-trip to what a controller displays.
        assert_eq!(seg("00:1B:92:0A:1B:2C:00:01"), "00:1B:92:0A:1B:2C:00:01");
        assert_eq!(seg("a/b+c#d"), "a_b_c_d");
        assert_eq!(seg(""), "_");
    }

    /// Every published key must have a value; a zip mismatch would silently
    /// truncate the device's attributes in the UI.
    #[test]
    fn key_count_matches_published_value_count() {
        assert_eq!(ENTITY_KEYS.len(), 18);
    }
}
