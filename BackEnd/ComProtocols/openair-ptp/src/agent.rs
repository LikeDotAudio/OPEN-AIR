//! The MQTT agent: publish discovered clocks as retained topics.
//!
//! Publishing policy differs from every other discovery agent here, and for a
//! reason worth stating: PTP is *continuous, high-rate* traffic. gPTP Sync runs
//! at 8 messages a second per port by default, and a device announcing itself
//! over mDNS does so every few minutes. Republishing a retained topic per Sync
//! would put thousands of writes a minute on the bus to say nothing new.
//!
//! So the agent publishes on **state change and on a slow heartbeat**, not per
//! packet. The live packet-by-packet view is the `ptp-monitor` binary's job —
//! that is a tool you watch, not a state store.

use crate::flow::FlowTracker;
use crate::message::{format_clock_id, ClockQuality};
use crate::monitor::{ClockTable, Observation, Transports};
use std::time::{Duration, Instant};

/// Retained attribute keys per clock port. Order here is the UI column order.
pub const CLOCK_KEYS: [&str; 19] = [
    "clock_id",
    "port",
    "variant",
    "domain",
    "role",
    "grandmaster",
    "gm_class",
    "gm_class_meaning",
    "gm_accuracy",
    "time_source",
    "steps_removed",
    "priority1",
    "priority2",
    "sync_interval_s",
    "two_step",
    "subdomain",
    "messages",
    "status",
    "last_online",
];

/// How often to refresh retained topics even when nothing changed.
const HEARTBEAT: Duration = Duration::from_secs(30);

/// Delay before the FIRST flush.
///
/// Shorter than the heartbeat so a launcher checking whether discovery works
/// does not have to wait half a minute for the first evidence. Long enough that
/// the counters mean something: PTP Sync runs at 1-8/s, so ten seconds is
/// hundreds of chances to have heard one.
const FIRST_FLUSH: Duration = Duration::from_secs(10);

/// Drop a clock that has gone quiet for this long.
///
/// PTP is continuous by nature: a healthy clock is never silent for 30s at any
/// standard rate. Silence therefore means gone, not idle.
const CLOCK_TIMEOUT: Duration = Duration::from_secs(30);

fn seg(raw: &str) -> String {
    let cleaned = raw.trim().replace(['/', '+', '#'], "_").replace(' ', "_");
    if cleaned.is_empty() { "_".to_string() } else { cleaned }
}

/// Blocking listen loop — run on a dedicated thread.
pub fn run_listen_agent(mqtt_host: &str, mqtt_port: u16) {
    let mut opts = rumqttc::MqttOptions::new("open-air-ptp", mqtt_host, mqtt_port);
    opts.set_keep_alive(Duration::from_secs(30));
    let (mqtt_client, mut connection) = rumqttc::Client::new(opts, 64);
    std::thread::spawn(move || {
        for _ in connection.iter() {}
    });

    let transports = Transports::open();
    for problem in &transports.problems {
        eprintln!("⚠️  [PTP] {problem}");
    }
    if !transports.any_open() {
        eprintln!("🛑 [PTP] no transport could be opened — agent not running");
        report_agent_state(&mqtt_client, "unavailable", &transports.problems.join(" | "));
        return;
    }

    // A partial capture is still worth running, but the bus must say which
    // half is missing — "no gPTP clocks" and "could not listen for gPTP" look
    // identical downstream otherwise.
    let state = if transports.problems.is_empty() { "listening" } else { "partial" };
    let detail = if transports.problems.is_empty() {
        format!(
            "{} UDP port(s), L2 {}",
            transports.udp.len(),
            if transports.l2.is_some() { "yes" } else { "no" }
        )
    } else {
        transports.problems.join(" | ")
    };
    println!("🔎 [PTP] {state}: {detail}");
    report_agent_state(&mqtt_client, state, &detail);

    let mut tracker = FlowTracker::default();
    let mut table = ClockTable::default();
    let mut published: std::collections::HashMap<String, String> = Default::default();
    // Start the clock in the past so the first flush lands at FIRST_FLUSH.
    let mut last_flush = Instant::now()
        .checked_sub(HEARTBEAT - FIRST_FLUSH)
        .unwrap_or_else(Instant::now);

    // Reception counters, split by transport.
    //
    // Published because the split is diagnostic on its own: raw AF_PACKET
    // capture sits BELOW netfilter and UDP does not, so "L2 flowing, UDP zero"
    // is the unmistakable signature of a host firewall dropping inbound UDP —
    // not of a network without PTP on it. Anything reading the bus (the
    // launcher does) can tell those apart without a packet capture.
    let mut udp_seen: u64 = 0;
    let mut l2_seen: u64 = 0;

    crate::monitor::run(
        &transports,
        &mut tracker,
        |obs| {
            match &obs {
                Observation::V2(_, _, meta) | Observation::V1(_, meta) => {
                    if meta.port.is_some() { udp_seen += 1 } else { l2_seen += 1 }
                }
                Observation::Undecodable { .. } => {}
            }
            match &obs {
                Observation::V2(msg, _, meta) => {
                    table.record(msg, meta);
                }
                // PTPv1 is recorded too, widened onto the same 64-bit identity
                // via the EUI-64 convention. Counting it but not recording it
                // (which this did) made a live v1 device invisible in the tab
                // while the agent cheerfully reported it was listening.
                Observation::V1(msg, meta) => {
                    table.record_v1(msg, meta);
                }
                Observation::Undecodable { .. } => {}
            }

            if last_flush.elapsed() >= HEARTBEAT {
                last_flush = Instant::now();
                flush(&mqtt_client, &mut table, &mut published);
                report_reception(&mqtt_client, udp_seen, l2_seen, !transports.udp.is_empty());
            }
        },
        || false,
    );
}

/// Publish every known clock, and clear those that have gone quiet.
fn flush(
    mqtt_client: &rumqttc::Client,
    table: &mut ClockTable,
    published: &mut std::collections::HashMap<String, String>,
) {
    let now = Instant::now();
    let now_secs = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0);

    let mut live = std::collections::HashSet::new();

    for clock in table.clocks.values() {
        if now.saturating_duration_since(clock.last_seen) > CLOCK_TIMEOUT {
            continue;
        }
        let id_seg = seg(&format_clock_id(&clock.key.clock_identity));
        let topic_seg = format!("{id_seg}-{}-d{}", clock.key.port_number, clock.domain);
        live.insert(topic_seg.clone());

        let quality = ClockQuality {
            class: clock.grandmaster_class.unwrap_or(0),
            accuracy: clock.grandmaster_accuracy.unwrap_or(0xFE),
            offset_scaled_log_variance: 0,
        };
        let dash = || "-".to_string();

        let values = [
            format_clock_id(&clock.key.clock_identity),
            clock.key.port_number.to_string(),
            clock.variant.label().to_string(),
            clock.domain.to_string(),
            if clock.is_grandmaster() { "grandmaster" } else { "clock" }.to_string(),
            clock.grandmaster.map(|g| format_clock_id(&g)).unwrap_or_else(dash),
            clock.grandmaster_class.map(|c| c.to_string()).unwrap_or_else(dash),
            clock.grandmaster_class.map(|_| quality.class_meaning().to_string()).unwrap_or_else(dash),
            clock.grandmaster_accuracy.map(|_| quality.accuracy_meaning().to_string()).unwrap_or_else(dash),
            clock.time_source.map(|t| time_source_name(t).to_string()).unwrap_or_else(dash),
            clock.steps_removed.map(|s| s.to_string()).unwrap_or_else(dash),
            clock.priority1.map(|p| p.to_string()).unwrap_or_else(dash),
            clock.priority2.map(|p| p.to_string()).unwrap_or_else(dash),
            clock.sync_interval.map(|i| format!("{i:.4}")).unwrap_or_else(dash),
            clock.two_step.to_string(),
            clock.subdomain.clone().unwrap_or_else(dash),
            clock.message_summary(),
            "identified".to_string(),
            now_secs.to_string(),
        ];

        let prefix = format!("OpenAir/System/Protocols/ptp/Device/{topic_seg}");
        // Only write what changed. A clock's attributes are static for hours at
        // a time; rewriting them every heartbeat is pure bus noise.
        for (key, value) in CLOCK_KEYS.iter().zip(values) {
            let topic = format!("{prefix}/{key}");
            if *key != "last_online" && published.get(&topic).is_some_and(|p| *p == value) {
                continue;
            }
            let _ = mqtt_client.publish(
                topic.clone(),
                rumqttc::QoS::AtLeastOnce,
                true,
                value.clone().into_bytes(),
            );
            published.insert(topic, value);
        }
    }

    // Clear clocks that stopped talking.
    let stale: Vec<String> = published
        .keys()
        .filter_map(|t| {
            let seg = t.strip_prefix("OpenAir/System/Protocols/ptp/Device/")?;
            let seg = seg.split('/').next()?;
            (!live.contains(seg)).then(|| seg.to_string())
        })
        .collect::<std::collections::HashSet<_>>()
        .into_iter()
        .collect();

    for seg in stale {
        println!("   ⌛ [PTP] {seg} stopped announcing — clearing");
        let prefix = format!("OpenAir/System/Protocols/ptp/Device/{seg}");
        for key in CLOCK_KEYS {
            let topic = format!("{prefix}/{key}");
            let _ = mqtt_client.publish(topic.clone(), rumqttc::QoS::AtLeastOnce, true, Vec::new());
            published.remove(&topic);
        }
    }

    table.clocks.retain(|_, c| now.saturating_duration_since(c.last_seen) <= CLOCK_TIMEOUT);
}

fn time_source_name(t: u8) -> &'static str {
    match t {
        0x10 => "atomic clock",
        0x20 => "GNSS/GPS",
        0x30 => "terrestrial radio",
        0x40 => "PTP",
        0x50 => "NTP",
        0x60 => "hand set",
        0x90 => "other",
        0xA0 => "internal oscillator",
        _ => "reserved",
    }
}

/// Publish what has actually been received, per transport.
fn report_reception(mqtt_client: &rumqttc::Client, udp: u64, l2: u64, udp_open: bool) {
    // `udp_blocked` is the conclusion, not the raw number, so a consumer does
    // not have to re-derive the netfilter reasoning to act on it.
    let blocked = udp_open && udp == 0 && l2 > 0;
    for (topic, payload) in [
        ("OpenAir/System/Protocols/ptp/Agent/udp_seen", udp.to_string()),
        ("OpenAir/System/Protocols/ptp/Agent/l2_seen", l2.to_string()),
        ("OpenAir/System/Protocols/ptp/Agent/udp_blocked", blocked.to_string()),
    ] {
        let _ = mqtt_client.publish(topic, rumqttc::QoS::AtLeastOnce, true, payload.into_bytes());
    }
}

/// Report whether this agent can see the network.
///
/// Same reasoning as the AVB agent: the orchestrator infers `online` from the
/// presence of a `config.ini`, which cannot know that a capability is missing.
fn report_agent_state(mqtt_client: &rumqttc::Client, state: &str, detail: &str) {
    for (topic, payload) in [
        ("OpenAir/System/Protocols/ptp/Agent/state", state),
        ("OpenAir/System/Protocols/ptp/Agent/detail", detail),
    ] {
        let _ = mqtt_client.publish(
            topic,
            rumqttc::QoS::AtLeastOnce,
            true,
            payload.as_bytes().to_vec(),
        );
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn topic_segments_keep_clock_identities_readable() {
        assert_eq!(seg("00:0A:92:FF:FE:01:56:A3"), "00:0A:92:FF:FE:01:56:A3");
        assert_eq!(seg("a/b+c#d"), "a_b_c_d");
    }

    /// One device can run several ports and domains; the topic segment has to
    /// separate them or they overwrite each other.
    #[test]
    fn segment_distinguishes_port_and_domain() {
        let id = seg("00:0A:92:FF:FE:01:56:A3");
        let a = format!("{id}-{}-d{}", 1, 0);
        let b = format!("{id}-{}-d{}", 1, 127);
        let c = format!("{id}-{}-d{}", 2, 0);
        assert_ne!(a, b, "domains must not collide");
        assert_ne!(a, c, "ports must not collide");
    }

    #[test]
    fn key_count_is_stable() {
        assert_eq!(CLOCK_KEYS.len(), 19);
    }
}
