//! `openair-nmos` — AMWA NMOS discovery (IS-04 / IS-09).
//!
//! NMOS is how professional media-over-IP gear finds itself. Unlike the printer
//! or AirPlay case — many services, one device — each NMOS service is a distinct
//! **API role**, and one host commonly runs several:
//!
//! | Service | Typical port | Role |
//! |---|---|---|
//! | `_nmos-node._tcp` | 3212 | Node API — a device offering senders/receivers |
//! | `_nmos-query._tcp` | 3211 | Query API — what clients ask to find things |
//! | `_nmos-register._tcp` | 3210 | Registration API (current name) |
//! | `_nmos-registration._tcp` | 3210 | Registration API (legacy name, same service) |
//! | `_nmos-system._tcp` | 10641 | System API (IS-09) — global config, PTP domain |
//!
//! # Grouping: by host **and port**, not by host
//!
//! Two Node APIs on one host (`:3212` and `:3300`) are genuinely two nodes and
//! must stay separate rows — collapsing by hostname would hide one.
//!
//! But `_nmos-register` and `_nmos-registration` on `:3210` are **one service
//! under two names**: the spec renamed it and implementations advertise both for
//! compatibility. Those must merge, or every registry appears twice.
//!
//! Host+port separates the first case and merges the second, which is why it is
//! the key.
//!
//! # `api_auth` gets its own column
//!
//! The TXT record states whether the API requires authorisation. `api_auth=false`
//! means an unauthenticated HTTP API is controlling media routing — worth seeing
//! at a glance rather than buried in a TXT blob.
//!
//! # Scope
//!
//! Discovery only. The Node/Query/Registration APIs are never called: nothing is
//! enumerated, registered, or connected. This crate previously declared itself a
//! stub; that marker is now `discovery-only`, which is the honest description —
//! IS-04 discovery works, IS-05 connection management does not exist.

use mdns_sd::{ServiceDaemon, ServiceEvent};
use std::collections::{BTreeSet, HashMap};
use std::time::Duration;

/// Implementation state. Discovery is real; the IS-04/IS-05 HTTP APIs are not
/// implemented, so this is deliberately not the word "complete".
pub const STATUS: &str = "discovery-only";

/// NMOS service types, with the role label shown in the table.
///
/// `_nmos-register` and `_nmos-registration` share a label deliberately — see
/// the grouping note above.
const NMOS_SERVICES: [(&str, &str); 5] = [
    ("_nmos-node._tcp.local.", "Node"),
    ("_nmos-query._tcp.local.", "Query"),
    ("_nmos-register._tcp.local.", "Registration"),
    ("_nmos-registration._tcp.local.", "Registration"),
    ("_nmos-system._tcp.local.", "System"),
];

const DEVICE_KEYS: [&str; 10] = [
    "service",
    "role",
    "api_versions",
    "api_proto",
    "api_auth",
    "priority",
    "host",
    "port",
    "addresses",
    "last_online",
];

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

/// Human-readable authorisation state.
///
/// `api_auth` is a documented boolean, but absence is not the same as `false`:
/// a registry that never advertises the key has not told us it is open. `?`
/// preserves that distinction instead of asserting a security property.
pub fn auth_label(api_auth: Option<&String>) -> &'static str {
    match api_auth.map(|v| v.trim().to_ascii_lowercase()) {
        Some(v) if v == "true" => "required",
        Some(v) if v == "false" => "NONE",
        _ => "?",
    }
}

/// Numeric sort key for `vMAJOR.MINOR`, so v1.10 ranks above v1.9.
fn version_key(v: &str) -> (u32, u32) {
    let t = v.trim_start_matches('v');
    let mut it = t.split('.');
    (
        it.next().and_then(|s| s.parse().ok()).unwrap_or(0),
        it.next().and_then(|s| s.parse().ok()).unwrap_or(0),
    )
}

/// Summarise advertised API versions, newest first.
///
/// A client negotiates to the highest common version, so that is the number
/// that matters; the full list stays visible behind it.
pub fn summarise_versions(api_ver: &str) -> String {
    let mut versions: Vec<&str> = api_ver
        .split(',')
        .map(|v| v.trim())
        .filter(|v| !v.is_empty())
        .collect();
    if versions.is_empty() {
        return "-".to_string();
    }
    versions.sort_by_key(|v| version_key(v));
    let newest = versions.last().copied().unwrap_or("-");
    if versions.len() == 1 {
        newest.to_string()
    } else {
        format!("{newest} (of {})", versions.join(", "))
    }
}

#[derive(Default, Clone)]
struct NmosService {
    instance: String,
    role: String,
    txt: HashMap<String, String>,
    addresses: BTreeSet<String>,
    host: String,
    port: u16,
}

/// Blocking browse loop — run on a dedicated thread.
pub fn run_browse_agent(mqtt_host: &str, mqtt_port: u16) {
    let mut opts = rumqttc::MqttOptions::new("open-air-nmos", mqtt_host, mqtt_port);
    opts.set_keep_alive(Duration::from_secs(30));
    let (mqtt_client, mut connection) = rumqttc::Client::new(opts, 32);
    std::thread::spawn(move || {
        for _ in connection.iter() {}
    });

    let mdns = match ServiceDaemon::new() {
        Ok(d) => d,
        Err(e) => {
            eprintln!("❌ [NMOS] could not start mDNS daemon: {e}");
            return;
        }
    };

    let (tx, rx) = std::sync::mpsc::channel::<(String, ServiceEvent)>();
    for (stype, role) in NMOS_SERVICES {
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
            Err(e) => eprintln!("   ⚠️  [NMOS] cannot browse {stype}: {e}"),
        }
    }
    drop(tx);

    println!("🚀 [NMOS] browsing IS-04 Node/Query/Registration + IS-09 System");

    // Key: host:port — see the grouping note in the module docs.
    let mut services: HashMap<String, NmosService> = HashMap::new();

    while let Ok((role, event)) = rx.recv() {
        let ServiceEvent::ServiceResolved(info) = event else {
            continue;
        };
        let host = info.get_hostname().trim_end_matches('.').to_string();
        let port = info.get_port();
        let key = format!("{host}:{port}");

        let entry = services.entry(key).or_default();
        entry.host = host.clone();
        entry.port = port;
        entry.role = role.clone();
        let fullname = info.get_fullname().to_string();
        entry.instance = fullname
            .split_once("._")
            .map(|(s, _)| s.to_string())
            .unwrap_or(fullname);
        for a in info.get_addresses() {
            let s = a.to_string();
            // nmos-cpp advertises every interface including loopback and IPv6
            // link-local; neither helps anyone reach the API.
            if s.contains('.') && !s.starts_with("127.") {
                entry.addresses.insert(s);
            }
        }
        for prop in info.get_properties().iter() {
            let v = prop.val_str().to_string();
            if !v.is_empty() {
                entry.txt.insert(prop.key().to_ascii_lowercase(), v);
            }
        }

        let s = entry.clone();
        let get = |k: &str| s.txt.get(k).cloned().unwrap_or_default();

        let values = [
            s.instance.clone(),
            s.role.clone(),
            summarise_versions(&get("api_ver")),
            { let p = get("api_proto"); if p.is_empty() { "-".into() } else { p } },
            auth_label(s.txt.get("api_auth")).to_string(),
            { let p = get("pri"); if p.is_empty() { "-".into() } else { p } },
            s.host.clone(),
            s.port.to_string(),
            s.addresses.iter().cloned().collect::<Vec<_>>().join(", "),
            now_secs().to_string(),
        ];

        let prefix = format!(
            "OpenAir/System/Protocols/nmos/Device/{}_{}",
            seg(&s.host),
            s.port
        );
        println!(
            "   ✅ [NMOS] {} @ {}:{} — API {} auth:{}",
            s.role,
            s.host,
            s.port,
            summarise_versions(&get("api_ver")),
            auth_label(s.txt.get("api_auth"))
        );
        for (k, value) in DEVICE_KEYS.iter().zip(values) {
            let _ = mqtt_client.publish(
                format!("{prefix}/{k}"),
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

    /// This crate is no longer a stub, and the marker must say so — the old test
    /// asserted `STATUS == "stub"` precisely so implementing it could not pass
    /// silently while the README still called it unimplemented.
    #[test]
    fn status_reflects_that_discovery_is_implemented() {
        assert_eq!(STATUS, "discovery-only");
    }

    /// Absence must not be reported as "open" — that would be a security claim
    /// the announcement never made.
    #[test]
    fn auth_distinguishes_absent_from_false() {
        assert_eq!(auth_label(Some(&"false".to_string())), "NONE");
        assert_eq!(auth_label(Some(&"true".to_string())), "required");
        assert_eq!(auth_label(None), "?");
        assert_eq!(auth_label(Some(&"".to_string())), "?");
    }

    /// The real advertisement from the bench.
    #[test]
    fn summarises_versions_newest_first() {
        assert_eq!(
            summarise_versions("v1.0,v1.1,v1.2,v1.3"),
            "v1.3 (of v1.0, v1.1, v1.2, v1.3)"
        );
        // The System API advertises a single version.
        assert_eq!(summarise_versions("v1.0"), "v1.0");
        assert_eq!(summarise_versions(""), "-");
    }

    /// Lexical sorting would rank v1.9 above v1.10.
    #[test]
    fn version_sort_is_numeric_not_lexical() {
        let s = summarise_versions("v1.9,v1.10");
        assert!(s.starts_with("v1.10"), "got {s}");
    }
}
