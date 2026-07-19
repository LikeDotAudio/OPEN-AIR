//! `openair-ravenna` — RAVENNA / AES67 audio stream discovery.
//!
//! A RAVENNA node announces itself over mDNS and describes its audio streams
//! with SDP, fetched over RTSP. This agent follows that chain end to end:
//!
//! 1. **mDNS** — browse `_ravenna._tcp` and `_rtsp._tcp` for stream
//!    announcements, plus `_http._tcp` for the node's config interface.
//! 2. **RTSP DESCRIBE** — ask each announced session for its SDP record at
//!    `rtsp://<ip>:554/by-name/<session>`.
//! 3. **SDP** — parse out what an engineer needs: encoding, sample rate,
//!    channel count, multicast destination, packet time, and the PTP clock
//!    domain the stream is locked to.
//!
//! # Why the SDP fetch is not optional
//!
//! Port 554 proves nothing on its own — IP cameras answer RTSP too. The SDP is
//! what distinguishes an audio node from a doorbell: an `m=audio` line with an
//! `L24/48000/2`-style rtpmap. Publishing every RTSP responder as a "RAVENNA
//! device" would be a guess dressed as a discovery, so a service is only filed
//! here once its own SDP says it carries audio.
//!
//! # Grouping
//!
//! One physical node commonly announces several streams — a desk might publish
//! `Digital inputs 1-2` and a monitor feed from the same host. Streams are
//! therefore grouped by **hostname**, so the UI shows one device with N streams
//! rather than N unrelated rows.
//!
//! # Scope
//!
//! Discovery and description only. No RTP receive, no stream subscription, no
//! connection management. Reading an SDP is exactly what any receiver does
//! before deciding whether to subscribe, and it changes nothing on the device.

pub mod sdp;

use mdns_sd::{ServiceDaemon, ServiceEvent};
use std::collections::HashMap;
use std::io::{Read, Write};
use std::net::{TcpStream, ToSocketAddrs};
use std::time::Duration;

/// Service types that lead to a RAVENNA node.
///
/// `_ravenna._tcp` is definitive when present; many devices only advertise the
/// generic `_rtsp._tcp`, which is why the SDP check exists.
const SERVICE_TYPES: [&str; 2] = ["_ravenna._tcp.local.", "_rtsp._tcp.local."];

/// Retained attribute keys per stream. Order here is the UI column order.
const STREAM_KEYS: [&str; 12] = [
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
    "status",
    "last_online",
];

const RTSP_TIMEOUT: Duration = Duration::from_secs(4);

/// Sanitise one MQTT topic segment.
fn seg(raw: &str) -> String {
    raw.trim()
        .trim_end_matches('.')
        .replace(['/', '+', '#'], "_")
        .replace(' ', "_")
}

/// Percent-encode a session name for use in an RTSP URL.
///
/// Session names are operator-set and contain spaces and parentheses —
/// `Digital inputs 1-2 (42-04-BA)` is a real one. Only unreserved characters
/// are passed through.
fn url_encode(raw: &str) -> String {
    let mut out = String::with_capacity(raw.len());
    for b in raw.bytes() {
        match b {
            b'A'..=b'Z' | b'a'..=b'z' | b'0'..=b'9' | b'-' | b'_' | b'.' | b'~' => {
                out.push(b as char)
            }
            _ => out.push_str(&format!("%{b:02X}")),
        }
    }
    out
}

/// Fetch the SDP for one session via RTSP DESCRIBE.
///
/// Returns `None` when the device does not answer, or answers without SDP —
/// both of which mean "do not claim this is a RAVENNA stream".
pub fn describe(ip: &str, port: u16, session: &str) -> Option<String> {
    let url = format!("rtsp://{ip}:{port}/by-name/{}", url_encode(session));
    let addr = format!("{ip}:{port}").to_socket_addrs().ok()?.next()?;
    let mut stream = TcpStream::connect_timeout(&addr, RTSP_TIMEOUT).ok()?;
    stream.set_read_timeout(Some(RTSP_TIMEOUT)).ok()?;
    stream.set_write_timeout(Some(RTSP_TIMEOUT)).ok()?;

    let request = format!(
        "DESCRIBE {url} RTSP/1.0\r\nCSeq: 1\r\nAccept: application/sdp\r\n\
         User-Agent: OPEN-AIR-discovery\r\n\r\n"
    );
    stream.write_all(request.as_bytes()).ok()?;

    // Read until the socket goes quiet or a sane cap is hit. These records are a
    // few hundred bytes; anything larger is not an SDP we understand.
    let mut buf = Vec::new();
    let mut chunk = [0u8; 1024];
    while buf.len() < 8192 {
        match stream.read(&mut chunk) {
            Ok(0) => break,
            Ok(n) => {
                buf.extend_from_slice(&chunk[..n]);
                // Header + body delivered; stop rather than wait for the timeout.
                if buf.windows(4).any(|w| w == b"\r\n\r\n") && buf.len() > 120 {
                    break;
                }
            }
            Err(_) => break,
        }
    }

    let text = String::from_utf8_lossy(&buf).to_string();
    if !text.starts_with("RTSP/1.0 200") {
        return None;
    }
    Some(text)
}

/// Blocking browse loop — run on a dedicated thread.
pub fn run_browse_agent(mqtt_host: &str, mqtt_port: u16) {
    let mut opts = rumqttc::MqttOptions::new("open-air-ravenna", mqtt_host, mqtt_port);
    opts.set_keep_alive(Duration::from_secs(30));
    let (mqtt_client, mut connection) = rumqttc::Client::new(opts, 32);
    std::thread::spawn(move || {
        for _ in connection.iter() {}
    });

    let mdns = match ServiceDaemon::new() {
        Ok(d) => d,
        Err(e) => {
            eprintln!("❌ [RAVENNA] could not start mDNS daemon: {e}");
            return;
        }
    };

    let (tx, rx) = std::sync::mpsc::channel::<ServiceEvent>();
    for stype in SERVICE_TYPES {
        match mdns.browse(stype) {
            Ok(receiver) => {
                let tx = tx.clone();
                std::thread::spawn(move || {
                    while let Ok(ev) = receiver.recv() {
                        if tx.send(ev).is_err() {
                            break;
                        }
                    }
                });
            }
            Err(e) => eprintln!("   ⚠️  [RAVENNA] cannot browse {stype}: {e}"),
        }
    }
    drop(tx);

    println!("🚀 [RAVENNA] browsing {:?} (discovery + SDP description only)", SERVICE_TYPES);

    // Session -> host, so a vanished announcement clears the right topics.
    let mut published: HashMap<String, String> = HashMap::new();

    while let Ok(event) = rx.recv() {
        match event {
            ServiceEvent::ServiceResolved(info) => {
                let addresses: Vec<String> =
                    info.get_addresses().iter().map(|a| a.to_string()).collect();
                let Some(ip) = addresses.iter().find(|a| a.contains('.')).cloned() else {
                    continue; // IPv6-only announcement; RAVENNA here is v4.
                };
                let host = info.get_hostname().trim_end_matches('.').to_string();
                let fullname = info.get_fullname().to_string();
                // "Desk preMO._rtsp._tcp.local." -> "Desk preMO"
                let session = fullname
                    .split_once("._")
                    .map(|(s, _)| s.to_string())
                    .unwrap_or_else(|| fullname.clone());

                // The SDP is what proves this is audio. No SDP, no claim.
                let Some(raw) = describe(&ip, info.get_port(), &session) else {
                    println!("   ⏭️  [RAVENNA] {session} @ {ip} did not return SDP — skipping");
                    continue;
                };
                let stream = sdp::parse(&raw);
                if !stream.is_audio {
                    println!("   ⏭️  [RAVENNA] {session} @ {ip} is not an audio stream — skipping");
                    continue;
                }

                let now_secs = std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .map(|d| d.as_secs())
                    .unwrap_or(0);

                let host_seg = seg(&host);
                let stream_seg = seg(&session);
                let prefix = format!(
                    "OpenAir/System/Protocols/ravenna/Device/{host_seg}/{stream_seg}"
                );

                let values = [
                    session.clone(),
                    stream.format_summary(),
                    stream.sample_rate.to_string(),
                    stream.channels.to_string(),
                    stream.destination.clone(),
                    stream.rtp_port.to_string(),
                    stream.ptime_ms.clone(),
                    stream.clock_domain.clone(),
                    stream.refclk.clone(),
                    stream.direction.clone(),
                    "identified".to_string(),
                    now_secs.to_string(),
                ];

                println!(
                    "   ✅ [RAVENNA] {host} / {session} — {} -> {}:{} ({})",
                    stream.format_summary(),
                    stream.destination,
                    stream.rtp_port,
                    stream.clock_domain
                );

                for (key, value) in STREAM_KEYS.iter().zip(values) {
                    let _ = mqtt_client.publish(
                        format!("{prefix}/{key}"),
                        rumqttc::QoS::AtLeastOnce,
                        true,
                        value.into_bytes(),
                    );
                }
                published.insert(stream_seg, host_seg);
            }
            ServiceEvent::ServiceRemoved(_stype, fullname) => {
                let session = fullname
                    .split_once("._")
                    .map(|(s, _)| s.to_string())
                    .unwrap_or_else(|| fullname.clone());
                let stream_seg = seg(&session);
                // Only clear what we actually published — a removal for a service
                // that never passed the audio check is not ours to act on.
                if let Some(host_seg) = published.remove(&stream_seg) {
                    println!("   👋 [RAVENNA] removed {session}");
                    let prefix = format!(
                        "OpenAir/System/Protocols/ravenna/Device/{host_seg}/{stream_seg}"
                    );
                    for key in STREAM_KEYS {
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
    fn url_encoding_handles_real_session_names() {
        // A real stream name from the bench.
        assert_eq!(
            url_encode("Digital inputs 1-2 (42-04-BA)"),
            "Digital%20inputs%201-2%20%2842-04-BA%29"
        );
        assert_eq!(url_encode("Desk preMO"), "Desk%20preMO");
        // Unreserved characters must pass through untouched.
        assert_eq!(url_encode("a-z_0.9~"), "a-z_0.9~");
    }

    #[test]
    fn seg_neutralises_topic_metacharacters() {
        assert_eq!(seg("Desk preMO"), "Desk_preMO");
        assert_eq!(seg("a/b+c#d"), "a_b_c_d");
        assert_eq!(seg("host.local."), "host.local");
    }
}
