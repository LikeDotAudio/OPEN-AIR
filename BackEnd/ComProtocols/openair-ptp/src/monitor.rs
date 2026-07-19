//! The capture loop shared by the live monitor and the MQTT agent.
//!
//! Polls every transport in turn, parses whatever arrives, correlates it into
//! exchanges, and hands each observation to a callback. Keeping the loop here
//! rather than in the binary means the agent and the CLI see byte-for-byte the
//! same stream — a monitor that showed something the agent did not publish
//! would be a debugging tool that lies.

use crate::flow::{Correlation, FlowTracker, PortKey};
use crate::message::{self, PtpMessage, Variant};
use crate::net::{self, Captured, L2Capture, UdpCapture};
use crate::v1::{self, V1Message};
use std::collections::HashMap;
use std::time::Instant;

/// One parsed observation from the wire.
pub enum Observation {
    /// A PTPv2 or gPTP message, with the exchange it completed (if any).
    V2(Box<PtpMessage>, Option<Correlation>, Meta),
    /// A PTPv1 message. Kept separate because it shares no structure with v2.
    V1(Box<V1Message>, Meta),
    /// Something arrived on a PTP transport that is not PTP we understand.
    Undecodable { reason: String, meta: Meta },
}

/// Where an observation came from.
#[derive(Debug, Clone)]
pub struct Meta {
    pub source: String,
    pub port: Option<u16>,
    pub interface: String,
    pub at: Instant,
}

/// Which transports actually opened.
pub struct Transports {
    pub udp: Vec<UdpCapture>,
    pub l2: Option<L2Capture>,
    pub interfaces: Vec<(String, u32, [u8; 6], std::net::Ipv4Addr)>,
    /// Human-readable notes about what failed to open and why. Reported rather
    /// than swallowed: hearing only gPTP because the UDP bind was refused is a
    /// legitimate partial result *provided it says so*.
    pub problems: Vec<String>,
}

impl Transports {
    /// Open everything that will open. Never fails outright — a partial
    /// capture is still useful, and the caller decides whether it is enough.
    pub fn open() -> Self {
        let interfaces = net::list_interfaces().unwrap_or_default();
        let mut problems = Vec::new();
        let mut udp = Vec::new();

        for port in [net::PORT_EVENT, net::PORT_GENERAL] {
            match UdpCapture::open(port, &interfaces) {
                Ok(c) => udp.push(c),
                Err(e) => problems.push(format!(
                    "UDP port {port} unavailable ({}) — PTPv1 and PTPv2-over-UDP will not be seen",
                    net::explain_error(&e)
                )),
            }
        }

        let l2 = match L2Capture::open(&interfaces) {
            Ok(c) => Some(c),
            Err(e) => {
                problems.push(format!(
                    "raw capture unavailable ({}) — gPTP and PTPv2-over-Ethernet will not be seen",
                    net::explain_error(&e)
                ));
                None
            }
        };

        Self { udp, l2, interfaces, problems }
    }

    pub fn any_open(&self) -> bool {
        !self.udp.is_empty() || self.l2.is_some()
    }

    fn interface_name(&self, index: u32) -> String {
        self.interfaces
            .iter()
            .find(|(_, i, _, _)| *i == index)
            .map(|(n, _, _, _)| n.clone())
            .unwrap_or_else(|| "?".to_string())
    }
}

/// Parse one captured payload into an observation.
///
/// The version discrimination lives here because it is the crux of a mixed
/// network: v1 and v2 arrive on the same socket, from the same group, on the
/// same port, and only the leading bytes tell them apart.
pub fn classify(cap: &Captured, tracker: &mut FlowTracker, at: Instant) -> Observation {
    let meta = Meta {
        source: cap.source.clone(),
        port: cap.port,
        interface: cap.interface.clone(),
        at,
    };

    if v1::is_v1(&cap.payload) {
        return match v1::parse(&cap.payload) {
            Ok(m) => Observation::V1(Box::new(m), meta),
            Err(e) => Observation::Undecodable { reason: format!("PTPv1: {e:?}"), meta },
        };
    }

    match message::parse(&cap.payload, cap.variant) {
        Ok(m) => {
            let correlation = tracker.observe(&m, at);
            Observation::V2(Box::new(m), correlation, meta)
        }
        Err(e) => Observation::Undecodable { reason: format!("{e:?}"), meta },
    }
}

/// Run the capture loop until `should_stop` returns true, invoking `on` for
/// every observation.
pub fn run<F, S>(transports: &Transports, tracker: &mut FlowTracker, mut on: F, should_stop: S)
where
    F: FnMut(Observation),
    S: Fn() -> bool,
{
    let mut buf = vec![0u8; 2048];
    let name_of = |i: u32| transports.interface_name(i);

    while !should_stop() {
        let mut idle = true;

        for sock in &transports.udp {
            if let Ok(Some(cap)) = sock.recv(&mut buf) {
                idle = false;
                on(classify(&cap, tracker, Instant::now()));
            }
        }

        if let Some(l2) = &transports.l2 {
            if let Ok(Some(cap)) = l2.recv(&mut buf, &name_of) {
                idle = false;
                on(classify(&cap, tracker, Instant::now()));
            }
        }

        if idle {
            // Every socket has a 200ms read timeout, so an idle pass has
            // already slept. This only avoids a hot spin if they all return
            // immediately for some reason.
            std::thread::sleep(std::time::Duration::from_millis(1));
        }
    }
}

/// A clock seen on the network, accumulated across messages.
#[derive(Debug, Clone)]
pub struct ClockRecord {
    pub key: PortKey,
    pub variant: Variant,
    pub domain: u8,
    /// From Announce: the grandmaster this clock reports following.
    pub grandmaster: Option<[u8; 8]>,
    pub grandmaster_class: Option<u8>,
    pub grandmaster_accuracy: Option<u8>,
    pub time_source: Option<u8>,
    pub steps_removed: Option<u16>,
    pub priority1: Option<u8>,
    pub priority2: Option<u8>,
    pub utc_offset: Option<i16>,
    /// True once a two-step Sync has been seen from this port.
    pub two_step: bool,
    pub sync_interval: Option<f64>,
    pub announce_interval: Option<f64>,
    pub message_counts: HashMap<&'static str, u64>,
    /// PTPv1 only: the subdomain NAME (`_DFLT`, `_ALT1`…). v1 has no numeric
    /// domain, so the name is the authoritative identifier and the numeric
    /// `domain` field is a display convenience mapped from it.
    pub subdomain: Option<String>,
    pub source: String,
    pub interface: String,
    pub last_seen: Instant,
}

impl ClockRecord {
    fn new(key: PortKey, meta: &Meta) -> Self {
        Self {
            key,
            variant: key.variant,
            domain: key.domain,
            grandmaster: None,
            grandmaster_class: None,
            grandmaster_accuracy: None,
            time_source: None,
            steps_removed: None,
            priority1: None,
            priority2: None,
            utc_offset: None,
            two_step: false,
            sync_interval: None,
            announce_interval: None,
            message_counts: HashMap::new(),
            subdomain: None,
            source: meta.source.clone(),
            interface: meta.interface.clone(),
            last_seen: meta.at,
        }
    }

    /// Is this port claiming to be the grandmaster itself?
    pub fn is_grandmaster(&self) -> bool {
        self.steps_removed == Some(0)
    }

    /// Message mix, e.g. `Sync ×15, Follow_Up ×14`.
    ///
    /// This is what makes a row with no Announce data still worth reading: a
    /// port emitting only `Pdelay_Req` is a very different thing from one
    /// emitting Sync and Follow_Up, and without it both render as a line of
    /// dashes that looks like a broken parser.
    pub fn message_summary(&self) -> String {
        let mut counts: Vec<(&&str, &u64)> = self.message_counts.iter().collect();
        counts.sort_by(|a, b| b.1.cmp(a.1).then(a.0.cmp(b.0)));
        counts.iter().map(|(k, v)| format!("{k} ×{v}")).collect::<Vec<_>>().join(", ")
    }
}

/// Accumulates per-port state from the observation stream.
#[derive(Default)]
pub struct ClockTable {
    pub clocks: HashMap<PortKey, ClockRecord>,
}

impl ClockTable {
    pub fn record(&mut self, msg: &PtpMessage, meta: &Meta) -> &ClockRecord {
        let key = PortKey::of(msg);
        let entry = self.clocks.entry(key).or_insert_with(|| ClockRecord::new(key, meta));
        entry.last_seen = meta.at;
        entry.source = meta.source.clone();
        if meta.interface != "udp" {
            entry.interface = meta.interface.clone();
        }
        *entry.message_counts.entry(msg.message_type.label()).or_insert(0) += 1;

        match msg.message_type {
            message::MessageType::Sync => {
                entry.two_step = msg.is_two_step();
                entry.sync_interval = Some(msg.interval_secs());
            }
            message::MessageType::Announce => {
                entry.announce_interval = Some(msg.interval_secs());
                if let Some(a) = &msg.announce {
                    entry.grandmaster = Some(a.grandmaster_identity);
                    entry.grandmaster_class = Some(a.grandmaster_quality.class);
                    entry.grandmaster_accuracy = Some(a.grandmaster_quality.accuracy);
                    entry.time_source = Some(a.time_source);
                    entry.steps_removed = Some(a.steps_removed);
                    entry.priority1 = Some(a.grandmaster_priority1);
                    entry.priority2 = Some(a.grandmaster_priority2);
                    entry.utc_offset = Some(a.current_utc_offset);
                }
            }
            _ => {}
        }
        &self.clocks[&key]
    }

    /// Record a PTPv1 message.
    ///
    /// v1 identifies a clock by a 6-byte UUID rather than a 64-bit clock
    /// identity, so it is widened with the same `FF:FE` splice PTPv2 uses. That
    /// is what lets one physical box running both stacks appear as one device
    /// instead of two unrelated identifiers — the whole point of watching v1
    /// and v2 on one NIC.
    pub fn record_v1(&mut self, msg: &V1Message, meta: &Meta) -> &ClockRecord {
        let key = PortKey {
            clock_identity: v1::uuid_as_clock_identity(&msg.source_uuid),
            port_number: msg.source_port_id,
            // v1 subdomains are names, not numbers. Mapped only so the topic
            // and the column line up with v2; `subdomain` carries the truth.
            domain: match msg.subdomain.as_str() {
                "_ALT1" => 1,
                "_ALT2" => 2,
                "_ALT3" => 3,
                _ => 0,
            },
            variant: Variant::V1,
        };
        let entry = self.clocks.entry(key).or_insert_with(|| ClockRecord::new(key, meta));
        entry.last_seen = meta.at;
        entry.source = meta.source.clone();
        entry.subdomain = Some(msg.subdomain.clone());
        *entry.message_counts.entry(msg.message_type.label()).or_insert(0) += 1;
        &self.clocks[&key]
    }

    /// Distinct grandmasters currently claimed, per domain+variant.
    ///
    /// More than one in the same domain means an unresolved BMCA election or a
    /// split network — devices following different grandmasters are not on the
    /// same time and cannot exchange audio.
    pub fn grandmasters_by_domain(&self) -> HashMap<(u8, Variant), Vec<[u8; 8]>> {
        let mut out: HashMap<(u8, Variant), Vec<[u8; 8]>> = HashMap::new();
        for c in self.clocks.values() {
            if let Some(gm) = c.grandmaster {
                let list = out.entry((c.domain, c.variant)).or_default();
                if !list.contains(&gm) {
                    list.push(gm);
                }
            }
        }
        out
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::message::parse;

    const GM: [u8; 8] = [0x00, 0x0A, 0x92, 0xFF, 0xFE, 0x01, 0x56, 0xA3];
    const OTHER: [u8; 8] = [0xAA, 0xBB, 0xCC, 0xFF, 0xFE, 0x00, 0x00, 0x01];

    fn meta() -> Meta {
        Meta {
            source: "00:0A:92:01:56:A3".into(),
            port: None,
            interface: "enp5s0f0".into(),
            at: Instant::now(),
        }
    }

    fn announce(clock: [u8; 8], gm: [u8; 8], steps: u16, domain: u8) -> PtpMessage {
        let mut p = vec![0u8; 34];
        p[0] = (1 << 4) | 0xB;
        p[1] = 0x02;
        p[4] = domain;
        p[20..28].copy_from_slice(&clock);
        p[28..30].copy_from_slice(&1u16.to_be_bytes());
        p[33] = 0x00;
        let mut body = vec![0u8; 30];
        body[14] = 6; // clockClass
        body[19..27].copy_from_slice(&gm);
        body[27..29].copy_from_slice(&steps.to_be_bytes());
        p.extend_from_slice(&body);
        parse(&p, Variant::V2Ethernet).unwrap()
    }

    #[test]
    fn announce_populates_the_grandmaster_record() {
        let mut table = ClockTable::default();
        let rec = table.record(&announce(GM, GM, 0, 0), &meta());
        assert_eq!(rec.grandmaster, Some(GM));
        assert_eq!(rec.grandmaster_class, Some(6));
        // stepsRemoved 0: this port IS the grandmaster.
        assert!(rec.is_grandmaster());
    }

    /// Two grandmasters in one domain is the diagnosis worth surfacing —
    /// devices following different clocks cannot exchange audio.
    #[test]
    fn competing_grandmasters_in_one_domain_are_visible() {
        let mut table = ClockTable::default();
        table.record(&announce(GM, GM, 0, 0), &meta());
        table.record(&announce(OTHER, OTHER, 0, 0), &meta());

        let by_domain = table.grandmasters_by_domain();
        // The helper sets transportSpecific = 1, so parse() promotes these to
        // gPTP — the variant is part of the key, which is what keeps a gPTP
        // clock and an L2 PTPv2 clock in domain 0 from being merged.
        let gms = &by_domain[&(0, Variant::Gptp)];
        assert_eq!(gms.len(), 2, "both grandmasters must be reported, not merged");
    }

    /// The same clock in two domains is two records, not one overwritten.
    #[test]
    fn domains_are_tracked_separately() {
        let mut table = ClockTable::default();
        table.record(&announce(GM, GM, 0, 0), &meta());
        table.record(&announce(GM, GM, 0, 127), &meta());
        assert_eq!(table.clocks.len(), 2);
    }

    #[test]
    fn message_counts_accumulate_per_type() {
        let mut table = ClockTable::default();
        table.record(&announce(GM, GM, 0, 0), &meta());
        let rec = table.record(&announce(GM, GM, 0, 0), &meta());
        assert_eq!(rec.message_counts["Announce"], 2);
    }

    /// A live PTPv1 device must produce a row, not just a counter tick.
    ///
    /// This is the bug the PTP tab exposed: v1 messages were classified,
    /// counted, and then dropped on the floor, so `44.44.44.154` — the busiest
    /// PTP talker on the bench — was invisible while the agent reported itself
    /// healthy. Counting traffic you do not record is worse than not seeing it.
    #[test]
    fn ptpv1_devices_become_rows() {
        let mut table = ClockTable::default();
        let mut p = vec![0u8; 44];
        p[0..2].copy_from_slice(&1u16.to_be_bytes());
        p[4..9].copy_from_slice(b"_DFLT");
        p[20] = 1; // event
        p[22..28].copy_from_slice(&[0x00, 0x0A, 0x92, 0x02, 0x77, 0x5B]);
        p[28..30].copy_from_slice(&1u16.to_be_bytes());
        p[32] = 0; // control = Sync
        let msg = v1::parse(&p).unwrap();

        let rec = table.record_v1(&msg, &meta());
        assert_eq!(rec.variant, Variant::V1);
        assert_eq!(rec.subdomain.as_deref(), Some("_DFLT"));
        // Widened onto the v2 identity convention so one physical box running
        // both stacks is one device, not two unrelated identifiers.
        assert_eq!(
            crate::message::format_clock_id(&rec.key.clock_identity),
            "00:0A:92:FF:FE:02:77:5B"
        );
        assert_eq!(rec.message_summary(), "Sync ×1");
        assert_eq!(table.clocks.len(), 1);
    }

    /// A row whose port only ever sends Pdelay_Req has no Announce data, so
    /// every quality column is blank. The message mix is what keeps that row
    /// informative instead of looking like a parser failure.
    #[test]
    fn message_summary_orders_by_frequency() {
        let mut table = ClockTable::default();
        for _ in 0..3 {
            table.record(&announce(GM, GM, 0, 0), &meta());
        }
        let rec = &table.clocks[&PortKey::of(&announce(GM, GM, 0, 0))];
        assert_eq!(rec.message_summary(), "Announce ×3");
    }

    /// v1 and v2 arriving on the same socket must be told apart by content.
    #[test]
    fn classify_routes_v1_and_v2_from_the_same_transport() {
        let mut tracker = FlowTracker::default();

        let mut v1_payload = vec![0u8; 44];
        v1_payload[0..2].copy_from_slice(&1u16.to_be_bytes());
        v1_payload[22..28].copy_from_slice(&[0x00, 0x0A, 0x92, 0x01, 0x56, 0xA3]);
        let cap = Captured {
            payload: v1_payload,
            variant: Variant::V2Udp, // what the transport guessed
            source: "44.44.44.1".into(),
            port: Some(319),
            interface: "udp".into(),
        };
        assert!(matches!(
            classify(&cap, &mut tracker, Instant::now()),
            Observation::V1(..)
        ));

        let mut v2_payload = vec![0u8; 34];
        v2_payload[1] = 0x02;
        v2_payload.extend_from_slice(&[0u8; 10]);
        let cap2 = Captured {
            payload: v2_payload,
            variant: Variant::V2Udp,
            source: "44.44.44.1".into(),
            port: Some(319),
            interface: "udp".into(),
        };
        assert!(matches!(
            classify(&cap2, &mut tracker, Instant::now()),
            Observation::V2(..)
        ));
    }
}
