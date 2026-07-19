//! `openair-sap` — SAP/SDP session announcement discovery agent.
//!
//! AES67 standardises how audio is clocked, packetised and transported, but
//! deliberately says nothing about how you *find* a stream. The ecosystem split
//! in two as a result:
//!
//! * **RAVENNA** announces over mDNS/DNS-SD and hands out SDP over RTSP — that
//!   chain is [`openair_ravenna`]'s job.
//! * **Dante in AES67 mode** announces over SAP: no queries, no resolution, no
//!   handshake. The device simply pushes its raw SDP to a well-known multicast
//!   group on UDP 9875 every few seconds, and anything listening builds a
//!   directory for free.
//!
//! This agent is that listener. It is the passive half of discovery, and the
//! two halves overlap on purpose: a node running RAV2SAP, or a modern RAVENNA
//! device with SAP publishing switched on, will appear under *both* agents.
//! That is not a duplicate to be suppressed here — the two topic trees record
//! two different observations ("this stream is announced over mDNS" and "this
//! stream is announced over SAP"), and which announcement mechanisms a stream
//! actually uses is exactly the interop question an engineer standing in front
//! of the rack is trying to answer. Correlating them into one device is the
//! Device Registry's job, not the listener's.
//!
//! # Topics
//!
//! One retained topic per attribute, matching the shape the Discovered-tab
//! builder sweeps (the same v40 field-per-topic layout as `openair-dnssd`):
//!
//! ```text
//! OpenAir/System/Protocols/sap/Device/{origin_ip}/{session}/{key}
//! ```
//!
//! Grouping is by the announcing node's IP rather than by session, because one
//! Dante device commonly announces every one of its transmit flows separately —
//! the UI should show one device with N streams.
//!
//! # Scope
//!
//! Listen only. This agent never transmits a SAP packet: publishing an
//! announcement would insert a phantom source into every routing matrix on the
//! network, which is not something a discovery tool gets to do as a side effect
//! of looking. Nothing here subscribes to RTP either.

pub mod sap;

use openair_ravenna::sdp;
use std::collections::HashMap;
use std::net::{IpAddr, Ipv4Addr, SocketAddr, UdpSocket};
use std::time::{Duration, Instant};

/// Well-known SAP groups, all on port 9875.
///
/// Three, not one, because scope choice is a per-vendor decision: Dante and
/// most AES67 gear use the admin-scoped `239.255.255.255`, the RFC 2974 global
/// group is `224.2.127.254`, and some installs are configured into the
/// organisation-local range. Listening to only one silently misses devices,
/// while a group nobody announces on costs a single unused membership.
const SAP_GROUPS: [Ipv4Addr; 3] = [
    Ipv4Addr::new(239, 255, 255, 255),
    Ipv4Addr::new(224, 2, 127, 254),
    Ipv4Addr::new(239, 195, 255, 255),
];

const SAP_PORT: u16 = 9875;

/// Retained attribute keys per stream. Order here is the UI column order, and
/// the first ten deliberately match `openair-ravenna`'s so the two protocols'
/// streams are readable side by side.
const STREAM_KEYS: [&str; 15] = [
    "stream",
    "format",
    "sample_rate",
    "channels",
    "destination",
    "rtp_port",
    "ptime_ms",
    "clock_domain",
    "refclk",
    "direction",
    "source",
    "announced_via",
    "msg_id",
    "status",
    "last_online",
];

/// How long a session survives without being re-announced.
///
/// SAP is periodic push with no goodbye guarantee — a device that is unplugged
/// simply stops talking, and the `T`-flag deletion packet only arrives on a
/// clean shutdown. Without an expiry the Discovered tab would accumulate ghosts
/// forever. RFC 2974 suggests ten announcement intervals; observed AoIP gear
/// announces every 5–30s, so five minutes covers a slow announcer with room to
/// spare while still clearing a dead one promptly.
const SESSION_TIMEOUT: Duration = Duration::from_secs(300);

/// Socket read timeout — also the reaper tick, since expiry is checked on the
/// same loop rather than from a second thread holding a lock.
const RECV_TIMEOUT: Duration = Duration::from_secs(5);

/// What we published for one announced session, so it can be cleared again.
struct Session {
    host_seg: String,
    stream_seg: String,
    last_seen: Instant,
}

/// Sanitise one MQTT topic segment. Mirrors `openair-ravenna`'s — session names
/// are operator-set free text and routinely contain spaces and slashes.
fn seg(raw: &str) -> String {
    let cleaned = raw
        .trim()
        .trim_end_matches('.')
        .replace(['/', '+', '#'], "_")
        .replace(' ', "_");
    if cleaned.is_empty() { "_".to_string() } else { cleaned }
}

/// Bind the SAP port and join every well-known group on every IPv4 interface.
///
/// Joining per-interface matters here more than in most places: an OPEN-AIR box
/// sits on a control LAN *and* an audio VLAN, and a membership on the default
/// route alone would hear nothing at all from the network that carries the
/// audio. Individual join failures are skipped rather than fatal — one
/// interface refusing multicast should not deafen the agent on the others.
fn bind_listener() -> std::io::Result<UdpSocket> {
    let socket = socket2::Socket::new(
        socket2::Domain::IPV4,
        socket2::Type::DGRAM,
        Some(socket2::Protocol::UDP),
    )?;
    // Dante Controller (or a second OPEN-AIR instance) may already hold 9875.
    // Multicast listeners are meant to coexist; without this, whoever starts
    // second gets EADDRINUSE and the operator concludes SAP "doesn't work".
    socket.set_reuse_address(true)?;
    #[cfg(unix)]
    socket.set_reuse_port(true)?;
    socket.bind(&SocketAddr::from((Ipv4Addr::UNSPECIFIED, SAP_PORT)).into())?;
    socket.set_read_timeout(Some(RECV_TIMEOUT))?;

    let socket: UdpSocket = socket.into();

    let interfaces: Vec<Ipv4Addr> = if_addrs::get_if_addrs()
        .map(|ifaces| {
            ifaces
                .into_iter()
                .filter(|i| !i.is_loopback())
                .filter_map(|i| match i.ip() {
                    IpAddr::V4(v4) => Some(v4),
                    IpAddr::V6(_) => None,
                })
                .collect()
        })
        .unwrap_or_default();

    let mut joined = 0usize;
    for group in SAP_GROUPS {
        // UNSPECIFIED first: on a single-homed host that is the membership that
        // actually works, and it costs nothing on a multi-homed one. Errors are
        // expected here (already-joined, link without multicast) and carry no
        // information worth printing.
        for iface in std::iter::once(Ipv4Addr::UNSPECIFIED).chain(interfaces.iter().copied()) {
            if socket.join_multicast_v4(&group, &iface).is_ok() {
                joined += 1;
            }
        }
    }

    if joined == 0 {
        eprintln!("⚠️  [SAP] bound :{SAP_PORT} but joined no multicast groups — check interfaces");
    } else {
        println!(
            "🔎 [SAP] listening on :{SAP_PORT} — {joined} group memberships across {} interface(s)",
            interfaces.len() + 1
        );
    }
    Ok(socket)
}

/// Blocking listen loop — run on a dedicated thread.
///
/// Publishes retained discovery topics as announcements arrive, and clears them
/// when a session is deleted or goes quiet past [`SESSION_TIMEOUT`].
pub fn run_listen_agent(mqtt_host: &str, mqtt_port: u16) {
    let mut opts = rumqttc::MqttOptions::new("open-air-sap", mqtt_host, mqtt_port);
    opts.set_keep_alive(Duration::from_secs(30));
    let (mqtt_client, mut connection) = rumqttc::Client::new(opts, 32);
    std::thread::spawn(move || {
        for _ in connection.iter() {} // drive the eventloop forever
    });

    let socket = match bind_listener() {
        Ok(s) => s,
        Err(e) => {
            eprintln!("🛑 [SAP] cannot listen on :{SAP_PORT}: {e}");
            return;
        }
    };

    // (origin, msg_id) is the session identity RFC 2974 defines, and the only
    // handle a deletion packet is guaranteed to carry.
    let mut sessions: HashMap<(IpAddr, u16), Session> = HashMap::new();
    let mut buf = [0u8; 8192];

    loop {
        match socket.recv_from(&mut buf) {
            Ok((len, from)) => {
                handle_datagram(&buf[..len], from, &mqtt_client, &mut sessions)
            }
            Err(ref e)
                if matches!(
                    e.kind(),
                    std::io::ErrorKind::WouldBlock | std::io::ErrorKind::TimedOut
                ) => {}
            Err(e) => {
                eprintln!("🛑 [SAP] receive failed: {e}");
                return;
            }
        }
        reap_expired(&mqtt_client, &mut sessions);
    }
}

/// Decode one datagram and publish or clear the session it describes.
fn handle_datagram(
    datagram: &[u8],
    from: SocketAddr,
    mqtt_client: &rumqttc::Client,
    sessions: &mut HashMap<(IpAddr, u16), Session>,
) {
    let packet = match sap::parse(datagram) {
        Ok(p) => p,
        Err(sap::SapError::Encrypted) => {
            println!("   🔒 [SAP] encrypted announcement from {from} — cannot read, ignoring");
            return;
        }
        Err(sap::SapError::Compressed) => {
            println!("   🗜️  [SAP] compressed announcement from {from} — no decompressor, ignoring");
            return;
        }
        Err(e) => {
            println!("   ⚠️  [SAP] undecodable packet from {from}: {e:?}");
            return;
        }
    };

    if !packet.is_sdp() {
        return; // Somebody else's payload type on the same port.
    }

    let key = (packet.origin, packet.msg_id);

    if packet.is_delete {
        // A deletion names the session by hash, not by name, so we can only
        // clear what we ourselves filed under that hash.
        if let Some(session) = sessions.remove(&key) {
            println!("   👋 [SAP] session deleted: {} @ {}", session.stream_seg, packet.origin);
            clear(mqtt_client, &session);
        }
        return;
    }

    let stream = sdp::parse(&packet.payload);
    if !stream.is_audio {
        // SAP carries video and data sessions too. Filing one as an AES67
        // stream would be a guess dressed as a discovery.
        return;
    }

    let session_name = if stream.session.is_empty() {
        // `s=` is mandatory in SDP but not universally honoured; fall back to
        // the message id so the stream is still visible rather than dropped.
        format!("session-{:04X}", packet.msg_id)
    } else {
        stream.session.clone()
    };

    let host_seg = seg(&packet.origin.to_string());
    let stream_seg = seg(&session_name);
    let prefix = format!("OpenAir/System/Protocols/sap/Device/{host_seg}/{stream_seg}");

    let now_secs = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0);

    let values = [
        session_name.clone(),
        stream.format_summary(),
        stream.sample_rate.to_string(),
        stream.channels.to_string(),
        stream.destination.clone(),
        stream.rtp_port.to_string(),
        stream.ptime_ms.clone(),
        stream.clock_domain.clone(),
        stream.refclk.clone(),
        stream.direction.clone(),
        packet.origin.to_string(),
        "SAP".to_string(),
        format!("{:04X}", packet.msg_id),
        "identified".to_string(),
        now_secs.to_string(),
    ];

    // SAP re-announces every few seconds; only log a session the first time it
    // is seen, or the console becomes unreadable within a minute.
    if !sessions.contains_key(&key) {
        println!(
            "   ✅ [SAP] {} / {} — {} -> {}:{}",
            packet.origin,
            session_name,
            stream.format_summary(),
            stream.destination,
            stream.rtp_port
        );
    }

    for (attr, value) in STREAM_KEYS.iter().zip(values) {
        let _ = mqtt_client.publish(
            format!("{prefix}/{attr}"),
            rumqttc::QoS::AtLeastOnce,
            true,
            value.into_bytes(),
        );
    }

    sessions.insert(key, Session { host_seg, stream_seg, last_seen: Instant::now() });
}

/// Clear sessions that have stopped announcing.
fn reap_expired(mqtt_client: &rumqttc::Client, sessions: &mut HashMap<(IpAddr, u16), Session>) {
    let now = Instant::now();
    let expired: Vec<(IpAddr, u16)> = sessions
        .iter()
        .filter(|(_, s)| now.duration_since(s.last_seen) > SESSION_TIMEOUT)
        .map(|(k, _)| *k)
        .collect();

    for key in expired {
        if let Some(session) = sessions.remove(&key) {
            println!(
                "   ⌛ [SAP] {} @ {} stopped announcing — clearing",
                session.stream_seg, key.0
            );
            clear(mqtt_client, &session);
        }
    }
}

/// Publish empty retained payloads, which the broker treats as a delete — a
/// vanished stream leaves no ghost row in the Discovered tab.
fn clear(mqtt_client: &rumqttc::Client, session: &Session) {
    let prefix = format!(
        "OpenAir/System/Protocols/sap/Device/{}/{}",
        session.host_seg, session.stream_seg
    );
    for attr in STREAM_KEYS {
        let _ = mqtt_client.publish(
            format!("{prefix}/{attr}"),
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
    fn seg_neutralises_topic_metacharacters() {
        assert_eq!(seg("Dante Out 1-2"), "Dante_Out_1-2");
        assert_eq!(seg("a/b+c#d"), "a_b_c_d");
        assert_eq!(seg("44.44.44.12"), "44.44.44.12");
        // A blank session name must never collapse the topic path by a level.
        assert_eq!(seg("   "), "_");
    }

    /// Captured verbatim off the bench network from 44.44.44.173, byte for
    /// byte as it arrived on 239.255.255.255:9875.
    ///
    /// This is the same physical node `openair-ravenna`'s tests reach over
    /// RTSP — it announces the identical session both ways. That overlap is
    /// the whole reason both agents exist, and it is why this fixture is kept
    /// as raw bytes rather than a tidied-up reconstruction: if a vendor's
    /// header layout ever stops matching what we parse, this test is the thing
    /// that notices.
    const BENCH_ANNOUNCEMENT: &[u8] = b"\x20\x00\x00\x07\x2c\x2c\x2c\xadapplication/sdp\x00\
v=0\r\n\
o=- 6 0 IN IP4 44.44.44.173\r\n\
s=Digital inputs 1-2 (42-04-BA)\r\n\
c=IN IP4 239.5.44.173/1\r\n\
t=0 0\r\n\
a=clock-domain:PTPv2 0\r\n\
m=audio 5004 RTP/AVP 98\r\n\
a=rtpmap:98 L24/48000/2\r\n\
a=recvonly\r\n\
a=framecount:48\r\n\
a=sync-time:0\r\n\
a=ptime:1\r\n\
a=ts-refclk:ptp=IEEE1588-2008:00-07-F5-FF-FE-00-54-72:0\r\n\
a=mediaclk:direct=0\r\n";

    #[test]
    fn decodes_a_real_announcement_off_the_bench() {
        let packet = sap::parse(BENCH_ANNOUNCEMENT).unwrap();
        assert!(!packet.is_delete && packet.is_sdp());
        assert_eq!(packet.origin, "44.44.44.173".parse::<IpAddr>().unwrap());
        assert_eq!(packet.msg_id, 7);

        let stream = sdp::parse(&packet.payload);
        assert!(stream.is_audio);
        assert_eq!(stream.session, "Digital inputs 1-2 (42-04-BA)");
        assert_eq!(stream.destination, "239.5.44.173");
        assert_eq!(stream.rtp_port, 5004);
        assert_eq!(stream.format_summary(), "L24 48000Hz 2ch");
        assert_eq!(stream.clock_domain, "PTPv2 0");
        assert_eq!(stream.direction, "recvonly");

        // The topic this lands on. Parentheses are legal in a topic segment;
        // only the spaces need neutralising.
        assert_eq!(seg(&stream.session), "Digital_inputs_1-2_(42-04-BA)");
    }

    /// The end-to-end shape for a Dante-style announcement, which differs from
    /// the bench capture above in payload-type handling and scope.
    #[test]
    fn a_dante_aes67_announcement_becomes_a_stream() {
        let mut packet = vec![0x20, 0x00, 0x12, 0x34, 44, 44, 44, 12];
        packet.extend_from_slice(b"application/sdp\0");
        packet.extend_from_slice(
            b"v=0\r\n\
o=- 1423986 1423986 IN IP4 44.44.44.12\r\n\
s=DanteDesk : 2\r\n\
c=IN IP4 239.69.12.34/32\r\n\
t=0 0\r\n\
a=clock-domain:PTPv2 0\r\n\
m=audio 5004 RTP/AVP 96\r\n\
a=rtpmap:96 L24/48000/2\r\n\
a=sendonly\r\n\
a=ptime:1\r\n\
a=ts-refclk:ptp=IEEE1588-2008:00-1D-C1-FF-FE-50-01-3B:0\r\n\
a=mediaclk:direct=0\r\n",
        );

        let parsed = sap::parse(&packet).unwrap();
        assert!(parsed.is_sdp() && !parsed.is_delete);

        let stream = sdp::parse(&parsed.payload);
        assert!(stream.is_audio);
        assert_eq!(stream.session, "DanteDesk : 2");
        assert_eq!(stream.destination, "239.69.12.34"); // /32 TTL suffix stripped
        assert_eq!(stream.rtp_port, 5004);
        assert_eq!(stream.format_summary(), "L24 48000Hz 2ch");
        assert_eq!(stream.direction, "sendonly");

        // And the topic segment that colon-and-space name lands on.
        assert_eq!(seg(&stream.session), "DanteDesk_:_2");
    }

    /// SAP is not audio-only. A video session on 9875 must not be filed as an
    /// AES67 stream just because it arrived on the audio-discovery port.
    #[test]
    fn video_sessions_on_9875_are_not_claimed() {
        let mut packet = vec![0x20, 0x00, 0x00, 0x09, 10, 0, 0, 7];
        packet.extend_from_slice(b"v=0\r\ns=Camera 3\r\nm=video 5006 RTP/AVP 96\r\n");
        let parsed = sap::parse(&packet).unwrap();
        assert!(!sdp::parse(&parsed.payload).is_audio);
    }
}
