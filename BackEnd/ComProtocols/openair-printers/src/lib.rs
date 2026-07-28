//! `openair-printers` — network printer discovery.
//!
//! Printers are the most standardised thing on a typical network. Every modern
//! one implements the **Bonjour Printing Specification** (the basis of AirPrint,
//! Mopria and IPP Everywhere), which means the TXT record is not vendor soup —
//! it is a documented schema this agent can decode into real columns.
//!
//! # The design problem: one printer, six announcements
//!
//! A single Brother HL-L2405W advertises **six** mDNS services:
//!
//! | Service | Port | What it is |
//! |---|---|---|
//! | `_ipp._tcp` | 631 | IPP — the modern default |
//! | `_ipps._tcp` | 443 | IPP over TLS |
//! | `_ipp-tls._tcp` | 631 | IPP with STARTTLS |
//! | `_printer._tcp` | 515 | LPD/LPR — the legacy path |
//! | `_pdl-datastream._tcp` | 9100 | raw socket ("JetDirect") |
//! | `_http._tcp` | 80 | the admin web UI |
//!
//! Listing those as six rows would be technically accurate and practically
//! useless. They are **one printer with six ways in**, so this agent emits one
//! row and turns the service list into a `transports` column — which is the
//! genuinely useful fact, because it tells you how you can actually print to it.
//!
//! Grouping is by **`UUID`** from the TXT record: it is identical across all six
//! announcements, stable across reboots, and survives a DHCP address change.
//! Hostname would break the moment a printer had two interfaces; the friendly
//! name is user-editable.
//!
//! # Capabilities, decoded
//!
//! The spec encodes capabilities as `T`/`F` flags (`Color=F`, `Duplex=F`,
//! `Scan=F`). Those are answerable questions — "can it do colour?" — so they
//! become Yes/No columns rather than being left as a wall of `k=v` text. A
//! printer that does not report a flag shows `?`, never `No`: absent is not the
//! same as false, and guessing would make the table lie.

use mdns_sd::{ServiceDaemon, ServiceEvent};
use std::collections::{BTreeSet, HashMap};
use std::time::Duration;

/// Every service type a Bonjour-compliant printer may advertise.
///
/// `_http._tcp` is included only to catch the admin UI of a printer already
/// known from another service — it is far too generic to identify a printer on
/// its own, so a host seen ONLY over `_http._tcp` is never published here.
const PRINTER_SERVICES: [(&str, &str); 6] = [
    ("_ipp._tcp.local.", "ipp"),
    ("_ipps._tcp.local.", "ipps"),
    ("_ipp-tls._tcp.local.", "ipp-tls"),
    ("_printer._tcp.local.", "lpd"),
    ("_pdl-datastream._tcp.local.", "raw9100"),
    ("_http._tcp.local.", "http"),
];

/// Column order in the Discovered tab: identity, then what it can do, then how
/// to reach it, then the bookkeeping.
const DEVICE_KEYS: [&str; 17] = [
    "printer",
    "manufacturer",
    "model",
    "color",
    "duplex",
    "scan",
    "fax",
    "paper_max",
    "transports",
    "languages",
    "addresses",
    // Neither is advertised. Both are recovered from the SLAAC IPv6 address,
    // which carries the host's MAC in its low 64 bits — `mac` is the address
    // itself, `vendor` is who holds that IEEE block. Blank for a host using
    // privacy addressing, where the interface ID is genuinely random.
    "mac",
    "vendor",
    "admin_url",
    "uuid",
    "status",
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

/// Decode a Bonjour printing `T`/`F` capability flag.
///
/// Returns `?` when the key is absent. A printer that does not advertise `Scan`
/// might still scan — the spec does not require the flag — so reporting "No"
/// would be asserting something the announcement never said.
pub fn flag(value: Option<&String>) -> &'static str {
    match value.map(|v| v.trim().to_ascii_uppercase()) {
        Some(v) if v == "T" => "Yes",
        Some(v) if v == "F" => "No",
        _ => "?",
    }
}

/// Shorten the `pdl` MIME list into the page description languages that matter.
///
/// Raw `pdl` is unreadable in a table cell:
/// `application/octet-stream,image/urf,image/pwg-raster`. What an operator wants
/// is "does it take PDF / PostScript / raster", so map to short names and drop
/// `application/octet-stream`, which every printer claims and which says nothing.
pub fn summarise_pdl(pdl: &str) -> String {
    let mut out: Vec<&str> = Vec::new();
    for item in pdl.split(',') {
        let i = item.trim().to_ascii_lowercase();
        let name = match i.as_str() {
            "application/pdf" => "PDF",
            "application/postscript" => "PostScript",
            "application/vnd.hp-pcl" | "application/vnd.hp-pcl5" => "PCL",
            "image/urf" => "AirPrint(URF)",
            "image/pwg-raster" => "PWG-raster",
            "image/jpeg" => "JPEG",
            "image/png" => "PNG",
            "application/octet-stream" => continue, // meaningless: everyone claims it
            "" => continue,
            _ => continue,
        };
        if !out.contains(&name) {
            out.push(name);
        }
    }
    if out.is_empty() { "-".to_string() } else { out.join(", ") }
}

/// Everything learned about one physical printer, merged across its services.
#[derive(Default, Clone)]
struct Printer {
    name: String,
    txt: HashMap<String, String>,
    transports: BTreeSet<String>,
    addresses: BTreeSet<String>,
}

/// Blocking browse loop — run on a dedicated thread.
pub fn run_browse_agent(mqtt_host: &str, mqtt_port: u16) {
    let mut opts = rumqttc::MqttOptions::new("open-air-printers", mqtt_host, mqtt_port);
    opts.set_keep_alive(Duration::from_secs(30));
    let (mqtt_client, mut connection) = rumqttc::Client::new(opts, 32);
    let vendors = openair_maclookup::MacVendors::start();
    std::thread::spawn(move || {
        for _ in connection.iter() {}
    });

    let mdns = match ServiceDaemon::new() {
        Ok(d) => d,
        Err(e) => {
            eprintln!("❌ [PRINTERS] could not start mDNS daemon: {e}");
            return;
        }
    };

    let (tx, rx) = std::sync::mpsc::channel::<(String, ServiceEvent)>();
    for (stype, label) in PRINTER_SERVICES {
        match mdns.browse(stype) {
            Ok(receiver) => {
                let tx = tx.clone();
                let label = label.to_string();
                std::thread::spawn(move || {
                    while let Ok(ev) = receiver.recv() {
                        if tx.send((label.clone(), ev)).is_err() {
                            break;
                        }
                    }
                });
            }
            Err(e) => eprintln!("   ⚠️  [PRINTERS] cannot browse {stype}: {e}"),
        }
    }
    drop(tx);

    println!("🚀 [PRINTERS] browsing IPP/IPPS/LPD/raw-9100 (one row per printer, not per service)");

    // Keyed by UUID — the only identifier stable across all six announcements.
    let mut printers: HashMap<String, Printer> = HashMap::new();

    while let Ok((transport, event)) = rx.recv() {
        let ServiceEvent::ServiceResolved(info) = event else {
            continue;
        };

        let mut txt: HashMap<String, String> = HashMap::new();
        for prop in info.get_properties().iter() {
            txt.insert(prop.key().to_ascii_lowercase(), prop.val_str().to_string());
        }

        // No UUID means this is not a Bonjour printing announcement — most
        // likely a generic _http._tcp host that happens to be on the network.
        let Some(uuid) = txt.get("uuid").cloned().filter(|u| !u.is_empty()) else {
            continue;
        };

        let fullname = info.get_fullname().to_string();
        let name = fullname
            .split_once("._")
            .map(|(s, _)| s.to_string())
            .unwrap_or_else(|| fullname.clone());

        let entry = printers.entry(uuid.clone()).or_default();
        entry.name = name.clone();
        entry.transports.insert(transport.clone());
        for a in info.get_addresses() {
            let s = a.to_string();
            // IPv6 link-local is noise in a table; the v4 address is what people use.
            if s.contains('.') {
                entry.addresses.insert(s);
            }
        }
        // Merge TXT: later services fill gaps but never blank an existing value.
        // `_pdl-datastream` carries a thinner record than `_ipp`, so a naive
        // overwrite would strip capabilities the printer had already reported.
        for (k, v) in txt {
            if v.is_empty() {
                continue;
            }
            entry.txt.entry(k).or_insert(v);
        }

        let p = entry.clone();
        let get = |k: &str| p.txt.get(k).cloned().unwrap_or_default();

        let manufacturer = {
            let m = get("usb_mfg");
            if m.is_empty() { "Unknown".to_string() } else { m }
        };
        let model = {
            let m = get("usb_mdl");
            let ty = get("ty");
            if !m.is_empty() { m } else if !ty.is_empty() { ty } else { "Unknown".into() }
        };
        let friendly = {
            let ty = get("ty");
            if ty.is_empty() { p.name.clone() } else { ty }
        };

        let values = [
            friendly.clone(),
            manufacturer,
            model,
            flag(p.txt.get("color")).to_string(),
            flag(p.txt.get("duplex")).to_string(),
            flag(p.txt.get("scan")).to_string(),
            flag(p.txt.get("fax")).to_string(),
            { let pm = get("papermax"); if pm.is_empty() { "-".into() } else { pm } },
            p.transports.iter().cloned().collect::<Vec<_>>().join(", "),
            summarise_pdl(&get("pdl")),
            p.addresses.iter().cloned().collect::<Vec<_>>().join(", "),
            {
                let addrs: Vec<String> = p.addresses.iter().cloned().collect();
                vendors
                    .mac_of_any(addrs.iter().map(String::as_str))
                    .map(|m| m.to_string())
                    .unwrap_or_else(|| "-".to_string())
            },
            {
                let addrs: Vec<String> = p.addresses.iter().cloned().collect();
                vendors
                    .vendor_of_any(addrs.iter().map(String::as_str))
                    .unwrap_or_else(|| "-".to_string())
            },
            { let a = get("adminurl"); if a.is_empty() { "-".into() } else { a } },
            uuid.clone(),
            "identified".to_string(),
            now_secs().to_string(),
        ];

        let prefix = format!(
            "OpenAir/System/Protocols/printers/Device/{}",
            seg(&friendly)
        );
        println!(
            "   ✅ [PRINTERS] {friendly} — {} via {}",
            p.addresses.iter().next().cloned().unwrap_or_else(|| "?".into()),
            p.transports.iter().cloned().collect::<Vec<_>>().join("/")
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
    fn flags_distinguish_false_from_absent() {
        assert_eq!(flag(Some(&"T".to_string())), "Yes");
        assert_eq!(flag(Some(&"F".to_string())), "No");
        assert_eq!(flag(Some(&"t".to_string())), "Yes"); // case-insensitive
        // The important case: not advertised is NOT the same as "No".
        assert_eq!(flag(None), "?");
        assert_eq!(flag(Some(&"".to_string())), "?");
    }

    /// The real `pdl` from the Brother HL-L2405W on this network.
    #[test]
    fn pdl_summary_drops_the_meaningless_entry() {
        let pdl = "application/octet-stream,image/urf,image/pwg-raster";
        assert_eq!(summarise_pdl(pdl), "AirPrint(URF), PWG-raster");
        // octet-stream alone tells you nothing, so it must not stand in as content.
        assert_eq!(summarise_pdl("application/octet-stream"), "-");
        assert_eq!(summarise_pdl(""), "-");
    }

    #[test]
    fn pdl_summary_recognises_the_common_languages() {
        let s = summarise_pdl("application/pdf,application/postscript,image/jpeg");
        assert!(s.contains("PDF"));
        assert!(s.contains("PostScript"));
        assert!(s.contains("JPEG"));
    }

    #[test]
    fn seg_neutralises_topic_metacharacters() {
        assert_eq!(seg("Brother HL-L2405W"), "Brother_HL-L2405W");
        assert_eq!(seg("a/b+c#d"), "a_b_c_d");
    }
}
