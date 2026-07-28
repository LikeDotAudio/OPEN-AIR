//! Discovered-device panels and live tables — the Rust port of the Python
//! `build_discovered_gui.py` this replaces.
//!
//! Collects the retained discovery topics every protocol agent publishes and
//! turns them into two things:
//!
//! - **panel files** under `FrontEnd/Gui_Frames/0_discovered/`, because folders
//!   make tabs: one directory per device category is one tab in the UI.
//! - **live row topics** under `OpenAir/System/Gui/Discovered/<category>`, which
//!   the `OcaTable` widget subscribes to.
//!
//! The split matters. A panel file is a snapshot, so a table written to disk
//! only changes when something regenerates it AND the browser is reloaded. The
//! live topic carries rows appearing, vanishing and changing state without
//! either. Columns and new categories still need a rebuild — that is the one
//! thing live rows cannot deliver, and the only reason to reload.
//!
//! Running in-process rather than as a spawned interpreter removes three things
//! that existed only to support the subprocess: the flock that stopped rescans
//! stacking up duplicate watchers (one process, one task, an `AtomicBool`), the
//! paho 1.x/2.x callback shim, and a second five-second collect just to hand a
//! device map to the instrument-panel builder. It also fixes a latent bug: the
//! Python connected to a hardcoded `127.0.0.1`, which is not the broker in the
//! container (compose sets `MQTT_HOST=broker`). This uses the host the
//! orchestrator was actually configured with.

use std::collections::{BTreeMap, BTreeSet};
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use chrono::{Local, TimeZone};
use serde::Serialize;

/// Where live table rows are published, one retained topic per category.
pub const LIVE_TABLE_PREFIX: &str = "OpenAir/System/Gui/Discovered";

/// Narration for the browser's Discovery Activity feed.
///
/// The VISA scan already narrates itself, but VISA is one agent out of a dozen:
/// everything DNS-SD, Cast, Dante, PTP, RAVENNA, SAP and the printers find only
/// ever appeared on stdout. Whoever is using the UI cannot see stdout, so the
/// page looked frozen while the terminal scrolled.
///
/// Non-retained: it is an event stream. A page loaded an hour from now must not
/// be shown a device appearing as though it were happening right then — the
/// device records themselves are retained, the narration about them is not.
pub const ACTIVITY_TOPIC: &str = "OpenAir/System/Discovery/Activity";

const RESCAN_TOPIC: &str = "OpenAir/System/Protocols/visa/Device/Rescan";
const CLEAR_TOPIC: &str = "OpenAir/System/Protocols/visa/Device/Clear";
const SCAN_STATE_TOPIC: &str = "OpenAir/System/Protocols/visa/Scan/State";

/// How long the retained replay must be silent before it counts as finished.
const QUIET_MS: u64 = 750;

/// Upper bound on waiting for the replay, so a chatty bus cannot stall a scan.
const MAX_SETTLE_SECONDS: u64 = 30;

/// Above this many changes in one pass, narrate the count instead of every row.
/// The first pass after a restart sees ~100 devices "appear" at once; a hundred
/// lines of that buries the two changes that actually mattered.
const ACTIVITY_DETAIL_LIMIT: usize = 8;

/// How recently a device must have answered to count as ONLINE.
///
/// Retained MQTT topics are the state store, so a device unplugged weeks ago
/// still has retained state and still appears in this table. Without an age
/// check every row looks equally current — which is how a table ends up showing
/// a month-old reading next to a live one with no visual difference.
const ONLINE_WINDOW_SECONDS: f64 = 15.0 * 60.0;

/// Fields carried in each row for the widget's benefit but never shown as
/// columns — row colouring, the write-topic binding, raw identity strings.
const HIDDEN_COLUMNS: [&str; 7] = [
    "last_online",
    "connected",
    "raw_idn",
    "device_type",
    "_row_state",
    "_topic_prefix",
    "reachable",
];

/// `{field: value}` for one device.
pub type Fields = BTreeMap<String, String>;
/// `{block name: fields}` for one category.
pub type Blocks = BTreeMap<String, Fields>;
/// `{category: blocks}` — the whole discovered world.
pub type Collected = BTreeMap<String, Blocks>;

/// Everything the mirror thread maintains from the bus.
#[derive(Default)]
pub struct State {
    pub collected: Collected,
    /// Latest value of the VISA scan-state topic. While a scan runs every row
    /// is provisional, which changes how rows are coloured.
    pub scanning: bool,
    /// Retained `<category>/config` topics found under our own output prefix,
    /// left by an older `OcaTable` that published its node definition alongside
    /// the rows. Dead weight on the broker, and one keystroke away from
    /// overwriting the row topic.
    pub stale_gui_config: BTreeSet<String>,
    /// `{protocol: publishes received}`, counted at the socket before parsing.
    pub arrived: BTreeMap<String, usize>,
    /// Retained publishes received. The broker replays the retained tree as one
    /// burst on subscribe; this counter is how the burst is known to be over.
    pub retained_seen: usize,
}

// ── Collection ───────────────────────────────────────────────────────────────

/// The topic filters the mirror subscribes to. One per protocol agent, plus the
/// scan state and our own output tree.
/// The whole protocol tree in ONE filter, rather than one filter per agent.
///
/// Two reasons, and the first is a bug this cost real time to find. Subscribing
/// to a dozen filters at once did not reliably take: the first ten were honoured
/// and the rest silently were not, so `avb` and `ptp` — last in the list — never
/// received a single message and their tabs simply never appeared. No error was
/// raised anywhere, by the client or the broker. One filter cannot be partially
/// applied.
///
/// The second reason is that the per-agent list was duplicated knowledge. Every
/// entry had to match a branch in `ingest`, so adding an agent meant editing two
/// places and a missing tab was the only symptom of forgetting the second. The
/// filter is now broad and `ingest` alone decides what is a device: anything
/// that is not `.../Device/...` or `.../Stream/...` falls straight through.
///
/// `SCAN_STATE_TOPIC` and `CLEAR_TOPIC` both live under this prefix, so they
/// come along with it.
const SUBSCRIPTIONS: [&str; 2] = [
    "OpenAir/System/Protocols/#",
    // Our own output tree, narrowed to exactly the legacy `<category>/config`
    // topics we exist to delete. `Discovered/#` would also replay every table we
    // publish — tens of kilobytes of rows we already have, read back for nothing.
    "OpenAir/System/Gui/Discovered/+/config",
];

/// Insert `value` only if the key is absent — Python's `dict.setdefault`.
fn set_default(fields: &mut Fields, key: &str, value: String) {
    fields.entry(key.to_string()).or_insert(value);
}

/// Fold one retained message into the collected map.
///
/// Every branch mirrors the shape its agent publishes; the shapes differ
/// because the things being described differ. A Dante interface has channels
/// under it, a PTP box has one row per *port* (a NIC can run v1, v2 and gPTP at
/// once and each is an independent clock that can disagree with the others),
/// and a VISA instrument is identified by model plus device index.
pub fn ingest(state: &mut State, topic: &str, payload: &str, retained: bool) {
    let value = payload.trim();

    if topic == SCAN_STATE_TOPIC {
        state.scanning = value == "scanning";
        return;
    }
    if topic == CLEAR_TOPIC {
        // The Discovered tab's CLEAR button. The write daemon wipes the retained
        // device topics; this drops what we already mirrored so a rebuild agrees.
        //
        // Both guards are load-bearing, and the same two the write daemon applies
        // to this topic. A retained message is STATE, not a command: the browser
        // leaves one behind, so every reconnect would replay it and empty the
        // mirror — and an empty mirror does not just write empty tables, it
        // PRUNES every tab. The truthiness check matters for the same reason:
        // the retained payload sitting on this bench's broker right now is
        // `{"value":0}`, which is the button at rest, not a request to wipe.
        if !retained && crate::is_truthy_trigger(payload) {
            state.collected.clear();
        }
        return;
    }
    if let Some(rest) = topic.strip_prefix(&format!("{LIVE_TABLE_PREFIX}/")) {
        // Rows we published ourselves; nothing to collect. The exception is the
        // `<category>/config` siblings left by an older widget.
        if rest.ends_with("/config") && !payload.is_empty() {
            state.stale_gui_config.insert(topic.to_string());
        }
        return;
    }

    let parts: Vec<&str> = topic.split('/').collect();
    // OpenAir/System/Protocols/{proto}/{Device|Stream}/...
    if parts.len() < 6 || (parts[4] != "Device" && parts[4] != "Stream") {
        return;
    }
    let proto = parts[3];
    let rest = &parts[5..];
    if value.is_empty() {
        return;
    }

    match proto {
        "visa" => {
            // {type}/{model}/Dev{n}/{key}
            if rest.len() != 4 || rest[3] == "Write" || rest[3] == "Read" {
                return;
            }
            let (dev_type, model, dev_n, key) = (rest[0], rest[1], rest[2], rest[3]);
            let block = format!("{model} ({dev_n})");
            let entry = state
                .collected
                .entry(dev_type.to_string())
                .or_default()
                .entry(block)
                .or_default();
            entry.insert(key.to_string(), value.to_string());
            // The device's own topic prefix, kept because the Write topic cannot
            // be rebuilt from the row fields (the Dev index appears nowhere in
            // them) and per-device instrument panels bind to exactly that topic.
            entry.insert(
                "_topic_prefix".to_string(),
                format!(
                    "{}/Device/{dev_type}/{model}/{dev_n}",
                    parts[..4].join("/")
                ),
            );
        }
        "midi" => {
            // {Input|Output}/Dev{n}/{key}
            if rest.len() != 3 {
                return;
            }
            let (direction, dev_n, key) = (rest[0], rest[1], rest[2]);
            let block = format!("{direction} {dev_n}");
            let entry = state
                .collected
                .entry("midi".to_string())
                .or_default()
                .entry(block)
                .or_default();
            // 'type' is widget vocabulary in panel JSON, so it cannot also be a
            // column name.
            let key = if key == "type" { "direction" } else { key };
            entry.insert(key.to_string(), value.to_string());
            set_default(entry, "port", format!("{direction} {dev_n}"));
        }
        "chromecast" => {
            // {category}/{friendly_name}/{key} — the Cast agent has already
            // decoded the TXT record and chosen a category, so this is a
            // straight passthrough. One tab per category (Speaker, Video Cast,
            // Smart Display …), which is the point: 40 raw mDNS rows become a
            // handful of meaningful ones.
            if rest.len() != 3 {
                return;
            }
            let (category, friendly, key) = (rest[0], rest[1], rest[2]);
            state
                .collected
                .entry(format!("cast_{category}"))
                .or_default()
                .entry(friendly.replace('_', " "))
                .or_default()
                .insert(key.to_string(), value.to_string());
        }
        "appletv" | "nmos" | "printers" => {
            // All three are already merged to one entry per thing by their agent
            // (Apple TV by hostname, NMOS by host+port, printers by the Bonjour
            // UUID), so this is a straight passthrough.
            if rest.len() != 2 {
                return;
            }
            state
                .collected
                .entry(proto.to_string())
                .or_default()
                .entry(rest[0].replace('_', " "))
                .or_default()
                .insert(rest[1].to_string(), value.to_string());
        }
        "dante" => {
            // Two shapes under one protocol, matching Dante's split personality:
            //   Device/{name}/{key}                  — native, found over mDNS
            //   Device/{device}/Channel/{ch}/{key}    — a channel of one
            // AES67-over-SAP streams belong to openair-sap and land in the `sap`
            // tab: SAP is vendor-neutral, so filing it under "Dante" would
            // mislabel RAVENNA and translator traffic too.
            if parts[4] != "Device" {
                return;
            }
            if rest.len() == 2 {
                state
                    .collected
                    .entry("dante".to_string())
                    .or_default()
                    .entry(rest[0].replace('_', " "))
                    .or_default()
                    .insert(rest[1].to_string(), value.to_string());
            } else if rest.len() == 4 && rest[1] == "Channel" {
                // Channels live under their device, so a 16-channel interface is
                // one device row plus 16 channel rows, not 16 devices.
                let (dev, ch, key) = (rest[0], rest[2], rest[3]);
                state
                    .collected
                    .entry("dante_channels".to_string())
                    .or_default()
                    .entry(format!("{ch} @ {dev}"))
                    .or_default()
                    .insert(key.to_string(), value.to_string());
            }
        }
        "ravenna" => {
            // {host}/{stream}/{key} — one tab for all RAVENNA audio, one row per
            // stream, labelled with its host. A single node commonly publishes
            // several streams, so host is context rather than a separate tab.
            if rest.len() != 3 {
                return;
            }
            let (host, stream_name, key) = (rest[0], rest[1], rest[2]);
            let entry = state
                .collected
                .entry("ravenna".to_string())
                .or_default()
                .entry(format!("{} @ {host}", stream_name.replace('_', " ")))
                .or_default();
            entry.insert(key.to_string(), value.to_string());
            set_default(entry, "host", host.to_string());
        }
        "sap" => {
            // {origin_ip}/{session}/{key} — SAP is the announcement mechanism
            // Dante uses in AES67 mode, so this is the same kind of stream
            // RAVENNA publishes, discovered by the opposite means (passive
            // multicast push rather than mDNS query). Its own tab rather than
            // merged into RAVENNA's: a stream appearing in both is the useful
            // signal, not noise.
            if rest.len() != 3 {
                return;
            }
            let (origin, session_name, key) = (rest[0], rest[1], rest[2]);
            let entry = state
                .collected
                .entry("sap".to_string())
                .or_default()
                .entry(format!("{} @ {origin}", session_name.replace('_', " ")))
                .or_default();
            entry.insert(key.to_string(), value.to_string());
            set_default(entry, "source", origin.to_string());
        }
        "avb" => {
            // {entity_id}/{key} — AVDECC entities, keyed by entity ID because
            // ADP carries no human-readable name at all; the name lives in the
            // AEM descriptor tree, which discovery does not fetch.
            if rest.len() != 2 {
                return;
            }
            state
                .collected
                .entry("avb".to_string())
                .or_default()
                .entry(rest[0].to_string())
                .or_default()
                .insert(rest[1].to_string(), value.to_string());
        }
        "ptp" => {
            // {clock_id}-{port}-d{domain}/{key} — one row per PTP *port*, not
            // per device. Merging ports by device would hide exactly the
            // disagreement worth seeing.
            if rest.len() != 2 {
                return;
            }
            let (segment, key) = (rest[0], rest[1]);
            // The clock id is itself colon-separated and may contain dashes, so
            // split from the RIGHT and keep anything that does not match as-is.
            let block = match segment.rsplitn(3, '-').collect::<Vec<_>>()[..] {
                [dom, port_no, clock] if dom.starts_with('d') => {
                    format!("{clock} port {port_no} (domain {})", &dom[1..])
                }
                _ => segment.to_string(),
            };
            state
                .collected
                .entry("ptp".to_string())
                .or_default()
                .entry(block)
                .or_default()
                .insert(key.to_string(), value.to_string());
        }
        "dnssd" => {
            // {service_type}/{instance}/{key} — one category for all DNS-SD
            // services, one block per instance, grouped by type.
            if rest.len() != 3 {
                return;
            }
            let (service_type, instance, key) = (rest[0], rest[1], rest[2]);
            state
                .collected
                .entry("dnssd".to_string())
                .or_default()
                .entry(format!("{instance} ({service_type})"))
                .or_default()
                .insert(key.to_string(), value.to_string());
        }
        _ => {}
    }
}

// ── Rows and columns ─────────────────────────────────────────────────────────

/// Column order per protocol family; remaining keys append alphabetically.
fn preferred_columns(family: &str) -> &'static [&'static str] {
    match family {
        "visa" => &["model", "manufacturer", "serial", "firmware", "resource", "status", "notes", "last_seen"],
        "midi" => &["port", "name", "direction"],
        "dnssd" => &["instance", "service_type", "hostname", "addresses", "port", "txt", "status", "last_seen"],
        // What the stream IS, then where it goes, then how it is clocked.
        "ravenna" => &["stream", "host", "format", "sample_rate", "channels", "destination",
                       "rtp_port", "ptime_ms", "clock_domain", "direction", "refclk", "status", "last_seen"],
        // Mirrors RAVENNA's order — same stream facts, different announcement
        // path — with the SAP-specific origin and msg id at the end.
        "sap" => &["stream", "source", "format", "sample_rate", "channels", "destination",
                   "rtp_port", "ptime_ms", "clock_domain", "direction", "refclk",
                   "announced_via", "msg_id", "status", "last_seen"],
        // Identity, then what it can carry, then the clock it follows —
        // grandmaster mismatch is the usual reason an entity won't pass audio.
        "avb" => &["entity_id", "mac", "oui", "interface", "talker_sources", "listener_sinks",
                   "talker_capabilities", "listener_capabilities", "gptp_grandmaster",
                   "gptp_domain", "milan", "entity_model_id", "configuration_index",
                   "valid_time_s", "status", "last_seen"],
        // grandmaster + gm_class answer "is time healthy?", which is the
        // question a PTP tab exists for. `messages` sits high on purpose: a port
        // that only sends Pdelay_Req has no Announce data, so every quality
        // column is blank. The message mix is what tells you that row is a
        // peer-delay-only port rather than a parse failure.
        "ptp" => &["clock_id", "port", "variant", "subdomain", "domain", "role", "messages",
                   "grandmaster", "gm_class", "gm_class_meaning", "gm_accuracy", "time_source",
                   "steps_removed", "priority1", "priority2", "sync_interval_s", "two_step",
                   "status", "last_seen"],
        "chromecast" => &["friendly_name", "model", "device_type", "capabilities", "status_text",
                          "addresses", "port", "hostname", "protocol_version", "cast_id",
                          "status", "last_seen"],
        _ => &[],
    }
}

/// Which column family a category's table follows.
fn family_of(category: &str) -> &str {
    if category.starts_with("cast_") {
        "chromecast"
    } else if matches!(category, "midi" | "dnssd" | "ravenna" | "sap" | "avb" | "ptp") {
        category
    } else {
        "visa"
    }
}

/// Classify a device row as `online` | `offline` | `unknown`.
///
/// Recency is the primary signal, because every agent publishes `last_online`.
/// `connected` is only published by the VISA agent (it means "*IDN? answered"),
/// so its ABSENCE must not count as offline — DNS-SD rows have no such field,
/// and treating missing as false marked every live service red.
///
/// An explicit `connected = 0` does override recency: a device probed seconds
/// ago that failed to answer is not online, however fresh the timestamp.
///
/// `unknown` is deliberate rather than folded into `offline`: a row with no
/// timestamp at all (a probe that half-answered) is a different situation from
/// one we know is stale, and colouring it red would assert more than we know.
pub fn row_state(fields: &Fields, now: f64) -> &'static str {
    let falsey = |k: &str| {
        matches!(
            fields.get(k).map(|v| v.trim()),
            Some("0") | Some("false") | Some("False")
        )
    };

    // Explicit negative from an agent that actually measures it.
    if falsey("connected") {
        return "offline";
    }
    // The VISA heartbeat's verdict: the instrument's transport stopped answering
    // repeated probes. Distinct from `connected`, which records whether *IDN?
    // ever answered — an instrument can be identified and later unplugged, and
    // only this notices within 30s instead of waiting out the online window.
    if falsey("reachable") {
        return "offline";
    }

    match fields.get("last_online").map(|v| v.trim()) {
        None | Some("") => "unknown",
        Some(raw) => match raw.parse::<f64>() {
            Err(_) => "unknown",
            Ok(ts) => {
                let age = now - ts;
                if (0.0..=ONLINE_WINDOW_SECONDS).contains(&age) {
                    "online"
                } else {
                    "offline"
                }
            }
        },
    }
}

/// Device map -> table rows, with the unix `last_online` rendered readable.
pub fn rows_for(category: &str, blocks: &Blocks, scanning: bool) -> (Vec<String>, Vec<Fields>) {
    let now = unix_now();
    let mut rows: Vec<Fields> = Vec::new();

    for fields in blocks.values() {
        let mut row = fields.clone();
        if let Some(raw) = fields.get("last_online") {
            let readable = raw
                .trim()
                .parse::<f64>()
                .ok()
                .and_then(|secs| Local.timestamp_opt(secs as i64, 0).single())
                .map(|dt| dt.format("%Y-%m-%d %H:%M:%S").to_string())
                .unwrap_or_else(|| raw.clone());
            row.insert("last_seen".to_string(), readable);
        }
        // Consumed by OcaTable for row colouring; hidden from the columns.
        // While a scan is running every row is provisional — the instrument may
        // be gone and we simply have not re-probed it yet. Showing last scan's
        // green during a live scan asserts something we do not currently know.
        let state = if scanning { "unknown" } else { row_state(&row, now) };
        row.insert("_row_state".to_string(), state.to_string());
        rows.push(row);
    }

    // An empty category still needs columns, or its tab renders as a bare box.
    // It gets the family's full preferred set: those are the columns a device of
    // this kind will have, so the table that appears before anything is found
    // has the same shape as the one that fills in afterwards — and filling it in
    // needs no reload, because the headers did not change.
    if rows.is_empty() {
        let headers = preferred_columns(family_of(category))
            .iter()
            .map(|c| c.to_string())
            .collect();
        return (headers, rows);
    }

    let keys: BTreeSet<&String> = rows.iter().flat_map(|r| r.keys()).collect();
    let preferred: Vec<String> = preferred_columns(family_of(category))
        .iter()
        .filter(|c| keys.contains(&c.to_string()))
        .map(|c| c.to_string())
        .collect();
    let rest: Vec<String> = keys
        .iter()
        .map(|k| (*k).clone())
        .filter(|k| !preferred.contains(k) && !HIDDEN_COLUMNS.contains(&k.as_str()))
        .collect();

    ([preferred, rest].concat(), rows)
}

// ── Tab grouping ─────────────────────────────────────────────────────────────
//
// Folders make tabs, so nesting a category inside a group folder nests its tab.
// Without this every discovery lands in one flat row of ~18 tabs, which stops
// being navigable about half way along.
//
// The `N_` prefix orders the groups; the numbers are deliberately sparse so a
// new group can be slotted between two existing ones without renumbering (and
// renumbering is not free — the validator treats sibling prefix collisions as an
// error, and folder names are identity here).
//
// NMOS sits in Audio_Over_IP rather than "Other" because it is media-over-IP
// infrastructure, not a peripheral: an IS-04 registry is what AES67 senders and
// receivers register WITH. It also carries video, so if that group is ever
// renamed, rename it to something like "Media_Over_IP".
const GROUPS: [(&str, &[&str]); 3] = [
    ("4_Audio_Over_IP", &["ravenna", "sap", "midi", "dante", "dante_channels", "avb", "nmos"]),
    ("10_Google and Apple", &["appletv"]), // plus every cast_* category
    ("12_Other", &["printers", "dnssd"]),
];

/// Categories promoted OUT of the group folders to sit as their own top-level
/// tab, in the same shape as `0_Scan`: `0_discovered/<folder>/<Name>.json` with
/// no intermediate category directory.
///
/// PTP earns this because it is not one more discovered device family — it is
/// the clock every AES67 and AVB stream is disciplined to. When audio drops out
/// this is the first tab you open, and burying it inside Audio_Over_IP puts it
/// at the same depth as the things it explains. The `5_` prefix sits it directly
/// after `4_Audio_Over_IP`, which is where you look next.
const TOP_LEVEL_TABS: [(&str, (&str, &str)); 1] = [("ptp", ("5_PTP", "PTP"))];

/// Network categories whose tab exists whether or not anything was discovered.
///
/// A tab is a folder, and the browser reads the folder tree once at page load —
/// so a category appearing for the FIRST time is the one change live rows cannot
/// deliver. Pre-creating these turns discovery into a pure row update: the tab is
/// already there, empty, and fills in without a reload.
///
/// It also removes a sharp edge. `prune` deletes any category the mirror is not
/// currently holding, so a category that merely arrived late — or whose agent
/// could not open a privileged socket this run — used to have its tab destroyed.
/// These are never pruned.
///
/// `cast_*` is deliberately absent: the category comes from the device's own TXT
/// record, so the set is open-ended and cannot be listed ahead of time.
const ALWAYS_PRESENT_PROTOCOLS: [&str; 11] = [
    "midi", "dnssd", "ravenna", "sap", "dante", "dante_channels", "avb", "ptp", "printers",
    "appletv", "nmos",
];

/// Every category that gets a tab regardless of what is on the bus.
///
/// The instrument half is READ from the panel-template manifest rather than
/// listed here, for the same reason `group_for` defaults to Lab_Instruments: a
/// second copy of the instrument-type list is a second thing to keep in sync,
/// and the symptom of forgetting is a tab that never appears.
fn always_present(root: &Path) -> BTreeSet<String> {
    let mut cats: BTreeSet<String> =
        ALWAYS_PRESENT_PROTOCOLS.iter().map(|s| s.to_string()).collect();
    let manifest = root.join("BackEnd").join("Instruments").join("manifest.json");
    match std::fs::read_to_string(&manifest) {
        Ok(body) => match serde_json::from_str::<serde_json::Value>(&body) {
            Ok(serde_json::Value::Object(map)) => cats.extend(map.keys().cloned()),
            _ => println!("⚠️  [DISCOVERED-GUI] {} is not a JSON object", manifest.display()),
        },
        // Not fatal: without it the instrument tabs simply go back to appearing
        // only once something is discovered.
        Err(e) => println!("⚠️  [DISCOVERED-GUI] no instrument manifest ({e}) — instrument tabs will appear only when found"),
    }
    cats
}

fn top_level_tab(category: &str) -> Option<(&'static str, &'static str)> {
    TOP_LEVEL_TABS
        .iter()
        .find(|(c, _)| *c == category)
        .map(|(_, folder)| *folder)
}

/// Which group folder a category's tab belongs in.
///
/// Lab instruments are the DEFAULT rather than an explicit list, because VISA
/// categories come from the instrument knowledge base at scan time — DMM,
/// Oscilloscope, Generator, Spectrum, Load, LCR, Power… Listing them here would
/// mean a newly-recognised instrument type silently landing in the wrong group
/// (or worse, at the top level) until someone remembered to update this map.
/// Everything discovered over the network is named explicitly; whatever is left
/// came off the bench.
fn group_for(category: &str) -> &'static str {
    if category.starts_with("cast_") {
        return "10_Google and Apple";
    }
    for (group, members) in GROUPS.iter() {
        if members.contains(&category) {
            return group;
        }
    }
    "1_Lab_Instruments"
}

// ── Panel documents ──────────────────────────────────────────────────────────
//
// These are structs rather than `serde_json::json!` maps on purpose. A JSON
// object is unordered in theory, but the UI renders a block's fields in the
// order they appear, so key order here is layout: build the scan panel from a
// map and serde's alphabetical ordering silently moves the RESCAN button below
// the activity feed. Struct fields serialize in declaration order, which makes
// the layout explicit and stable.

#[derive(Serialize)]
struct En {
    #[serde(rename = "En")]
    en: String,
}

impl En {
    fn new(text: impl Into<String>) -> Self {
        Self { en: text.into() }
    }
}

#[derive(Serialize)]
struct Behavior {
    overflow_ns: &'static str,
}

#[derive(Serialize)]
struct ActiveLabel {
    active: LabelText,
}

#[derive(Serialize)]
struct LabelText {
    text: En,
}

#[derive(Serialize)]
struct ToggleLabel {
    active: LabelText,
    inactive: LabelText,
}

#[derive(Serialize)]
struct Layout {
    height: u32,
    width: serde_json::Value,
}

#[derive(Serialize)]
struct Actuator {
    #[serde(rename = "type")]
    kind: &'static str,
    topic: &'static str,
    label: ToggleLabel,
    layout: Layout,
}

#[derive(Serialize)]
struct LabelField {
    #[serde(rename = "type")]
    kind: &'static str,
    label: ActiveLabel,
}

#[derive(Serialize)]
struct ActivityField {
    #[serde(rename = "type")]
    kind: &'static str,
    description: En,
    layout: Layout,
}

/// Field order IS the panel layout — see the note above.
#[derive(Serialize)]
struct ScanFields {
    rescan: Actuator,
    clear: Actuator,
    last_scan: LabelField,
    activity: ActivityField,
}

#[derive(Serialize)]
struct ScanControls {
    #[serde(rename = "type")]
    kind: &'static str,
    label: ActiveLabel,
    fields: ScanFields,
}

#[derive(Serialize)]
struct ScanBin {
    #[serde(rename = "type")]
    kind: &'static str,
    description: En,
    behavior: Behavior,
    blocks: BTreeMap<String, ScanControls>,
}

#[derive(Serialize)]
struct TableBlock {
    #[serde(rename = "type")]
    kind: &'static str,
    description: En,
    /// Live rows. `data` below is the cold-start snapshot so the table is
    /// populated the moment the panel loads; this topic then replaces it as
    /// devices change, with no rebuild and no browser refresh.
    topic: String,
    headers: Vec<String>,
    data: Vec<Fields>,
    #[serde(rename = "Sort")]
    sort: bool,
}

#[derive(Serialize)]
struct TableBin {
    #[serde(rename = "type")]
    kind: &'static str,
    description: En,
    behavior: Behavior,
    blocks: BTreeMap<String, TableBlock>,
}

// ── Writing ──────────────────────────────────────────────────────────────────

fn unix_now() -> f64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs_f64())
        .unwrap_or(0.0)
}

fn out_dir(root: &Path) -> PathBuf {
    root.join("FrontEnd").join("Gui_Frames").join("0_discovered")
}

fn write_json<T: Serialize>(path: &Path, doc: &T) -> std::io::Result<()> {
    let body = serde_json::to_string_pretty(doc)
        .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))?;
    std::fs::write(path, body)
}

/// The Discovered tab's control panel: RESCAN and CLEAR actuators wired to the
/// orchestrator's listeners, a scan-time stamp, and the live activity feed.
/// Written on every run — `0_Scan` sorts first in the tab.
fn write_scan_panel(root: &Path, device_count: usize, scanning: bool) -> std::io::Result<()> {
    let scan_dir = out_dir(root).join("0_Scan");
    std::fs::create_dir_all(&scan_dir)?;
    let stamp = Local::now().format("%Y-%m-%d %H:%M:%S").to_string();

    let status = if scanning {
        "⏳ SCAN IN PROGRESS — rows below are last scan's results and are shown amber until it finishes.".to_string()
    } else {
        format!("Last scan: {stamp} — {device_count} device(s).")
    };

    let doc = BTreeMap::from([(
        "Device_Scan".to_string(),
        ScanBin {
            kind: "OcaBin",
            description: En::new("Device discovery controls"),
            behavior: Behavior { overflow_ns: "auto" },
            blocks: BTreeMap::from([(
                "Controls".to_string(),
                ScanControls {
                    kind: "OcaBlock",
                    label: ActiveLabel { active: LabelText { text: En::new("Device Discovery") } },
                    fields: ScanFields {
                        rescan: Actuator {
                            kind: "_GuiActuator",
                            topic: RESCAN_TOPIC,
                            label: ToggleLabel {
                                active: LabelText { text: En::new("RESCANNING...") },
                                inactive: LabelText { text: En::new("RESCAN DEVICES") },
                            },
                            layout: Layout { height: 50, width: serde_json::json!(250) },
                        },
                        clear: Actuator {
                            kind: "_GuiActuator",
                            topic: CLEAR_TOPIC,
                            label: ToggleLabel {
                                active: LabelText { text: En::new("CLEARING...") },
                                inactive: LabelText { text: En::new("CLEAR ALL DEVICES") },
                            },
                            layout: Layout { height: 50, width: serde_json::json!(250) },
                        },
                        last_scan: LabelField {
                            kind: "_GuiLabel",
                            label: ActiveLabel {
                                active: LabelText {
                                    text: En::new(format!(
                                        "{status} Rows update live; reload only to pick up new tabs or columns."
                                    )),
                                },
                            },
                        },
                        // The live feed. Everything the agents narrate on the bus
                        // lands here, which is the whole point: a scan used to be
                        // visible only in the orchestrator's stdout, so pressing
                        // RESCAN from the browser looked like it did nothing.
                        activity: ActivityField {
                            kind: "_GuiScanActivity",
                            description: En::new("Discovery Activity"),
                            layout: Layout { height: 340, width: serde_json::json!("100%") },
                        },
                    },
                },
            )]),
        },
    )]);

    write_json(&scan_dir.join("Scan.json"), &doc)?;
    println!("[discovered-gui] wrote scan control panel ({device_count} device(s) at {stamp})");
    Ok(())
}

/// Delete category folders whose devices vanished, or that moved group after a
/// knowledge-base fix.
///
/// Pruning walks INSIDE the group folders: a top-level sweep would see the group
/// names, fail to find them in `collected`, and delete every tab on each run.
fn prune(root: &Path, collected: &Collected) {
    let dir = out_dir(root);
    if !dir.is_dir() {
        return;
    }
    // Folder -> category for the promoted tabs. These live at the top level and
    // would otherwise be swept as "ungrouped leftovers" on the very next run —
    // which is exactly what happened to a hand-made 5_PTP/ directory.
    let promoted: BTreeMap<&str, &str> =
        TOP_LEVEL_TABS.iter().map(|(cat, (folder, _))| (*folder, *cat)).collect();
    let group_names: Vec<&str> = std::iter::once("1_Lab_Instruments")
        .chain(GROUPS.iter().map(|(g, _)| *g))
        .collect();

    // Categories that keep their folder: everything currently on the bus, plus
    // everything that gets a tab whether or not it is.
    let mut keep: BTreeSet<String> = collected.keys().cloned().collect();
    keep.extend(always_present(root));

    let wanted: BTreeSet<(String, String)> = keep
        .iter()
        .filter(|c| top_level_tab(c).is_none())
        .map(|c| (group_for(c).to_string(), c.clone()))
        .collect();

    let mut entries: Vec<_> = match std::fs::read_dir(&dir) {
        Ok(e) => e.flatten().collect(),
        Err(_) => return,
    };
    entries.sort_by_key(|e| e.file_name());

    for entry in entries {
        let path = entry.path();
        let name = entry.file_name().to_string_lossy().to_string();
        if name == "0_Scan" || !path.is_dir() {
            continue;
        }
        if let Some(category) = promoted.get(name.as_str()) {
            // Keep it while its category still has devices; drop the whole folder
            // when it does not, so an empty tab does not linger.
            if !keep.contains(*category) {
                let _ = std::fs::remove_dir_all(&path);
                println!("[discovered-gui] pruned empty top-level tab {name}/");
            }
            continue;
        }
        if group_names.contains(&name.as_str()) {
            let mut cats: Vec<_> = match std::fs::read_dir(&path) {
                Ok(e) => e.flatten().collect(),
                Err(_) => continue,
            };
            cats.sort_by_key(|e| e.file_name());
            for cat in cats {
                let cat_name = cat.file_name().to_string_lossy().to_string();
                if cat.path().is_dir() && !wanted.contains(&(name.clone(), cat_name.clone())) {
                    let _ = std::fs::remove_dir_all(cat.path());
                    println!("[discovered-gui] pruned stale category {name}/{cat_name}/");
                }
            }
            // An empty group folder would render as an empty tab.
            if std::fs::read_dir(&path).map(|mut e| e.next().is_none()).unwrap_or(false) {
                let _ = std::fs::remove_dir(&path);
                println!("[discovered-gui] pruned empty group {name}/");
            }
        } else {
            // A category left at the top level by an earlier, ungrouped build.
            // Remove it so it does not shadow the grouped copy.
            let _ = std::fs::remove_dir_all(&path);
            println!("[discovered-gui] pruned ungrouped leftover {name}/");
        }
    }
}

/// Write one panel per category. Returns how many were written.
pub fn write_panels(root: &Path, collected: &Collected, scanning: bool) -> std::io::Result<usize> {
    prune(root, collected);

    // The union, not just what was discovered: an always-present category with
    // no devices still gets its (empty) panel, so its tab is there to fill in.
    let empty = Blocks::new();
    let mut categories: BTreeSet<String> = collected.keys().cloned().collect();
    categories.extend(always_present(root));

    let mut written = 0;
    for category in &categories {
        let category = category.as_str();
        let blocks = collected.get(category).unwrap_or(&empty);
        let (folder, doc_name, cat_dir) = match top_level_tab(category) {
            Some((folder, doc_name)) => (folder, doc_name.to_string(), out_dir(root).join(folder)),
            None => {
                let folder = group_for(category);
                (folder, category.to_string(), out_dir(root).join(folder).join(category))
            }
        };
        std::fs::create_dir_all(&cat_dir)?;
        let (headers, rows) = rows_for(category, blocks, scanning);
        let n_rows = rows.len();
        let n_cols = headers.len();

        // The library OcaTable (libControl/text/OcaTable) — the component built
        // for exactly this: sticky header, zebra rows, row-count footer, own
        // scroll region.
        let doc = BTreeMap::from([(
            doc_name.clone(),
            TableBin {
                kind: "OcaBin",
                description: En::new(format!("Discovered {category} devices (scan snapshot)")),
                behavior: Behavior { overflow_ns: "auto" },
                blocks: BTreeMap::from([(
                    "Devices".to_string(),
                    TableBlock {
                        kind: "OcaTable",
                        description: En::new(format!("Discovered {category} devices")),
                        topic: format!("{LIVE_TABLE_PREFIX}/{category}"),
                        headers,
                        data: rows,
                        sort: true,
                    },
                )]),
            },
        )]);

        write_json(&cat_dir.join(format!("{doc_name}.json")), &doc)?;
        written += 1;
        println!("[discovered-gui] wrote {folder}/{doc_name} ({n_rows} device(s), {n_cols} columns)");
    }
    Ok(written)
}

// ── Publishing ───────────────────────────────────────────────────────────────

/// Publish each category's rows to its live topic. Returns categories sent.
pub fn publish_live_tables(client: &rumqttc::Client, collected: &Collected, scanning: bool) -> usize {
    let mut sent = 0;
    for (category, blocks) in collected.iter() {
        let (_headers, rows) = rows_for(category, blocks, scanning);
        if let Ok(payload) = serde_json::to_vec(&rows) {
            let _ = client.publish(
                format!("{LIVE_TABLE_PREFIX}/{category}"),
                rumqttc::QoS::AtLeastOnce,
                true,
                payload,
            );
            sent += 1;
        }
    }
    sent
}

/// Put one narration line on the bus for the browser's activity feed.
///
/// QoS 0, non-retained — same reasoning as the orchestrator's scan log: losing a
/// line of commentary under load is preferable to slowing discovery for it.
pub fn publish_activity(client: &rumqttc::Client, level: &str, message: impl AsRef<str>, source: &str) {
    let payload = serde_json::json!({
        "level": level,        // "info" | "ok" | "warn" | "error"
        "message": message.as_ref(),
        "source": source,      // which agent family the line is about
        "ts": unix_now(),
    });
    let _ = client.publish(ACTIVITY_TOPIC, rumqttc::QoS::AtMostOnce, false, payload.to_string());
}

/// `{(category, block): row_state}` for everything currently collected.
fn device_states(collected: &Collected, scanning: bool) -> BTreeMap<(String, String), &'static str> {
    let now = unix_now();
    collected
        .iter()
        .flat_map(|(category, blocks)| {
            blocks.iter().map(move |(name, fields)| {
                let state = if scanning { "unknown" } else { row_state(fields, now) };
                ((category.clone(), name.clone()), state)
            })
        })
        .collect()
}

/// Announce what changed between two device snapshots.
///
/// Only appearances, disappearances and online/offline transitions are narrated.
/// Field churn is deliberately silent: `last_online` moves on almost every pass,
/// and a feed that says "something changed" twice a second says nothing at all.
fn narrate_changes(
    client: &rumqttc::Client,
    before: &BTreeMap<(String, String), &'static str>,
    after: &BTreeMap<(String, String), &'static str>,
) {
    let added: Vec<_> = after.keys().filter(|k| !before.contains_key(*k)).cloned().collect();
    let removed: Vec<_> = before.keys().filter(|k| !after.contains_key(*k)).cloned().collect();
    let flipped: Vec<_> = after
        .iter()
        .filter(|(k, v)| before.get(*k).map(|b| b != *v).unwrap_or(false))
        .map(|(k, _)| k.clone())
        .collect();

    // Per-category counts read better than 53 individual lines the first time a
    // watcher sees a populated bus.
    let summarize = |keys: &[(String, String)], verb: &str, level: &str| {
        let mut counts: BTreeMap<&str, usize> = BTreeMap::new();
        for (category, _) in keys {
            *counts.entry(category.as_str()).or_insert(0) += 1;
        }
        for (category, n) in counts {
            publish_activity(client, level, format!("{n} device(s) {verb}"), category);
        }
    };

    for (keys, verb, level) in [(&added, "appeared", "ok"), (&removed, "vanished", "warn")] {
        if keys.is_empty() {
            continue;
        }
        if keys.len() > ACTIVITY_DETAIL_LIMIT {
            summarize(keys, verb, level);
        } else {
            for (category, name) in keys {
                publish_activity(client, level, format!("{name} {verb}"), category);
            }
        }
    }

    // Liveness flips summarize by DESTINATION STATE, not as one lump. They arrive
    // in waves: every device an agent last touched at the same moment crosses the
    // staleness window together, so an agent restart turns the whole table amber
    // in one pass. One line per device is then ~80 lines that say one thing.
    let mut by_state: BTreeMap<&'static str, Vec<(String, String)>> = BTreeMap::new();
    for key in flipped {
        by_state.entry(after[&key]).or_default().push(key);
    }
    for (state, keys) in by_state {
        let level = match state {
            "online" => "ok",
            "offline" => "warn",
            _ => "info",
        };
        if keys.len() > ACTIVITY_DETAIL_LIMIT {
            summarize(&keys, &format!("went {state}"), level);
        } else {
            for (category, name) in &keys {
                publish_activity(client, level, format!("{name} is now {state}"), category);
            }
        }
    }
}

// ── The mirror ───────────────────────────────────────────────────────────────

/// A live view of the retained discovery tree, plus a client to publish with.
#[derive(Clone)]
pub struct Mirror {
    state: Arc<Mutex<State>>,
    client: rumqttc::Client,
    root: PathBuf,
}

/// Only one watcher task may run, however many scans have finished.
///
/// The orchestrator asked for a watcher after EVERY scan, so the subprocess
/// version needed an flock to stop N copies republishing identical rows and
/// narrating every change N times. In-process this is the whole of that logic.
static WATCHER_RUNNING: AtomicBool = AtomicBool::new(false);

impl Mirror {
    /// Subscribe to every agent's discovery tree and keep mirroring it.
    ///
    /// The connection lives on its own OS thread because rumqttc's sync
    /// `Connection::iter()` blocks, and this is called from inside the tokio
    /// runtime.
    pub fn spawn(root: PathBuf, host: &str, port: u16) -> Self {
        let mut opts = rumqttc::MqttOptions::new("open-air-discovered-gui", host, port);
        opts.set_keep_alive(Duration::from_secs(30));
        // rumqttc defaults to a 10 KB incoming limit, and an oversized packet is
        // not skipped — it kills the connection. A single Discovered table on a
        // busy bench passes 10 KB easily (this bench's dnssd rows are 28 KB), so
        // the default turned one large retained payload into a mirror that
        // silently stopped receiving. Sized for the whole retained tree instead.
        opts.set_max_packet_size(4 * 1024 * 1024, 4 * 1024 * 1024);
        // Every retained device topic on a busy bench arrives in one burst on
        // subscribe; a small queue here drops them on the floor.
        let (client, mut connection) = rumqttc::Client::new(opts, 256);

        let state = Arc::new(Mutex::new(State::default()));
        let thread_state = state.clone();
        let sub_client = client.clone();
        std::thread::spawn(move || {
            for notification in connection.iter() {
                match notification {
                    // Subscribing on ConnAck rather than once at startup, because
                    // rumqttc restores the SESSION on reconnect but not the
                    // SUBSCRIPTIONS. Any blip — broker restart, oversized packet,
                    // a second process stealing the client id — otherwise leaves
                    // this connected and subscribed to nothing, still holding the
                    // devices it saw before the drop. That failure is invisible:
                    // the tables keep rendering, frozen, with no error anywhere.
                    Ok(rumqttc::Event::Incoming(rumqttc::Packet::ConnAck(_))) => {
                        // ONE SubscribeFilter list, not a loop of subscribe()
                        // calls. This runs on the eventloop's own thread — the
                        // thread that drains the request queue — so a burst of
                        // individual requests queues against a drainer that
                        // cannot run until the burst finishes. Fifteen of them
                        // left the last five silently unsubscribed, which shows
                        // up as two permanently missing tabs (avb and ptp) with
                        // no error anywhere. One packet cannot half-arrive.
                        // QoS 0, and that is load-bearing rather than lazy. The
                        // broker QUEUES QoS>0 messages per subscriber and drops
                        // whatever exceeds `max_queued_messages` (mosquitto
                        // defaults to 1000); the retained replay on this bench is
                        // ~1400. Subscribing at QoS 1 therefore lost several
                        // hundred retained messages with no error on either side
                        // — and what it lost was, by definition, the protocols
                        // that only ever publish retained state and never
                        // republish it. MIDI's tab was empty for exactly this
                        // reason while chatty agents like Cast looked fine.
                        //
                        // QoS 0 costs nothing here: retained state is re-sent in
                        // full on every subscribe, so the recovery for a dropped
                        // message is the reconnect that was going to happen anyway.
                        let filters = SUBSCRIPTIONS.iter().map(|f| {
                            rumqttc::SubscribeFilter::new(f.to_string(), rumqttc::QoS::AtMostOnce)
                        });
                        if let Err(e) = sub_client.subscribe_many(filters) {
                            // Never swallowed: an unsubscribed mirror still
                            // renders, just frozen and empty, so a dropped
                            // subscribe is invisible unless it is said out loud.
                            println!("⚠️  [DISCOVERED-GUI] subscribe failed: {e}");
                        }
                    }
                    Ok(rumqttc::Event::Incoming(rumqttc::Packet::Publish(publish))) => {
                        let payload = String::from_utf8_lossy(&publish.payload).to_string();
                        // Counted here, at the socket, before any parsing can
                        // drop it — this is what separates "the message never
                        // arrived" from "it arrived and ingest made nothing of
                        // it", which look identical from a missing tab.
                        let arrived = publish
                            .topic
                            .split('/')
                            .nth(3)
                            .unwrap_or("?")
                            .to_string();
                        if let Ok(mut guard) = thread_state.lock() {
                            *guard.arrived.entry(arrived).or_insert(0) += 1;
                            if publish.retain {
                                guard.retained_seen += 1;
                            }
                            ingest(&mut guard, &publish.topic, &payload, publish.retain);
                        }
                    }
                    Err(e) => {
                        // The eventloop reconnects on its own; log once per blip
                        // rather than spinning silently.
                        println!("⚠️  [DISCOVERED-GUI] mirror connection: {e}");
                        std::thread::sleep(Duration::from_secs(1));
                    }
                    _ => {}
                }
            }
        });

        Self { state, client, root }
    }

    /// Record that a scan started or finished, without waiting for the
    /// scan-state topic to round-trip the broker.
    ///
    /// The mirror does subscribe to that topic, so this is belt and braces —
    /// but the scan loop rebuilds panels in the same breath as it announces the
    /// state change, and losing that race means publishing a table whose rows
    /// claim to be current while the scan that would invalidate them is running.
    pub fn set_scanning(&self, scanning: bool) {
        if let Ok(mut guard) = self.state.lock() {
            guard.scanning = scanning;
        }
    }

    /// A snapshot of the collected tree and the current scan state.
    fn snapshot(&self) -> (Collected, bool) {
        match self.state.lock() {
            Ok(g) => (g.collected.clone(), g.scanning),
            Err(_) => (Collected::new(), false),
        }
    }

    /// `build()` off the async runtime.
    ///
    /// The build writes a tree of files and waits out an interpreter, which is
    /// long enough to matter: called directly from the scan task it would hold a
    /// tokio worker thread for the whole of it. Awaited rather than detached, so
    /// the two builds a scan performs cannot overlap and race on `Gui_Frames`.
    pub async fn build_async(&self) {
        let mirror = self.clone();
        let _ = tokio::task::spawn_blocking(move || mirror.build()).await;
    }

    /// Rebuild every panel file, then seed the live topics.
    ///
    /// Fire-and-forget by contract: a failed regeneration must never abort a
    /// scan, so every error is reported and swallowed.
    pub fn build(&self) {
        let (collected, scanning) = self.snapshot();
        let devices: usize = collected.values().map(|b| b.len()).sum();

        // What the socket actually delivered, per protocol. Worth a line on every
        // build: a protocol missing from here has a subscription problem, one
        // present here but absent from the panels below has a parsing problem,
        // and without it those two look identical — a tab that is simply not
        // there. Diagnosing exactly that took considerably longer than printing
        // it would have.
        if let Ok(guard) = self.state.lock() {
            let arrived: Vec<String> =
                guard.arrived.iter().map(|(p, n)| format!("{p}={n}")).collect();
            println!("[discovered-gui] received by protocol: {}", arrived.join(" "));
        }

        let written = match write_panels(&self.root, &collected, scanning) {
            Ok(n) => n,
            Err(e) => {
                println!("⚠️  [DISCOVERED-GUI] panel write failed: {e}");
                return;
            }
        };
        if let Err(e) = write_scan_panel(&self.root, devices, scanning) {
            println!("⚠️  [DISCOVERED-GUI] scan panel write failed: {e}");
        }

        // One control surface per discovered instrument, stamped from the
        // backend template library. Runs from the map just collected rather than
        // re-reading the bus, and in-process rather than as a second writer, so
        // it cannot race the panel tree this just wrote.
        let instruments = crate::instruments::devices_from_collected(&self.root, &collected);
        let (panels, built) = crate::instruments::build(&self.root, &instruments);
        println!("[discovered-gui] instrument panels: {built} device(s), {panels} file(s)");

        // Seed the live topics too, so a panel written now has rows the instant
        // it loads rather than waiting for the watcher's first change.
        publish_live_tables(&self.client, &collected, scanning);

        // Drop the retained `<category>/config` leftovers. MQTT deletes retained
        // state by publishing an empty payload to the exact topic.
        let stale: Vec<String> = self
            .state
            .lock()
            .map(|mut g| std::mem::take(&mut g.stale_gui_config).into_iter().collect())
            .unwrap_or_default();
        for topic in &stale {
            let _ = client_publish_empty(&self.client, topic);
        }
        if !stale.is_empty() {
            println!("[discovered-gui] cleared {} stale /config topic(s)", stale.len());
        }

        // Tell the browser the tab structure changed — a rebuild is the one thing
        // live rows cannot deliver, so this is where "reload" is actually warranted.
        publish_activity(
            &self.client,
            "info",
            format!("panels rebuilt — {written} categor(ies), {devices} device(s); reload for new tabs or columns"),
            "discovery",
        );

        if written == 0 {
            println!("[discovered-gui] no retained discovery topics found — only the scan panel written");
        }
    }

    /// Republish rows whenever the retained tree changes, and narrate what moved.
    ///
    /// Publish-only on purpose. `build()` owns the panel FILES; two writers would
    /// race, and only a new category or column actually requires a file rewrite.
    /// Rows change constantly and are exactly what this keeps live.
    ///
    /// Republishing only on change keeps an idle bench quiet: PTP alone would
    /// otherwise put a full table on the bus every couple of seconds forever.
    pub fn spawn_watcher(&self) {
        if WATCHER_RUNNING.swap(true, Ordering::SeqCst) {
            return;
        }
        let mirror = self.clone();
        tokio::spawn(async move {
            let (collected, scanning) = mirror.snapshot();
            let devices: usize = collected.values().map(|b| b.len()).sum();
            println!("[discovered-gui] watching — live rows -> {LIVE_TABLE_PREFIX}/<category>");
            publish_activity(
                &mirror.client,
                "info",
                format!(
                    "watching {} categor(ies), {devices} device(s) — live rows are on the bus",
                    collected.len()
                ),
                "discovery",
            );

            let mut last: Option<String> = None;
            let mut seen = device_states(&collected, scanning);
            loop {
                tokio::time::sleep(Duration::from_secs(2)).await;
                let (collected, scanning) = mirror.snapshot();
                // Row STATE is time-dependent, not just content-dependent: a
                // device goes stale because the clock moved, with no new message
                // to change the fingerprint. Folding the states in is what makes
                // the table turn amber on its own.
                let current = device_states(&collected, scanning);
                let fingerprint = serde_json::to_string(&(&collected, &current)).unwrap_or_default();
                if Some(&fingerprint) == last.as_ref() {
                    continue;
                }
                last = Some(fingerprint);
                let n = publish_live_tables(&mirror.client, &collected, scanning);
                narrate_changes(&mirror.client, &seen, &current);
                seen = current;
                println!("[discovered-gui] live update: {n} table(s)");
            }
        });
    }

    /// Wait for the broker's retained replay to finish.
    ///
    /// Not a fixed sleep. Retained state arrives as one burst on subscribe, and
    /// on a populated bench that burst is thousands of messages — the five
    /// seconds this replaces covered maybe half of it. Building against half a
    /// mirror does not merely write partial tables: `prune` deletes every
    /// category that has not arrived yet, so a short wait silently destroys
    /// tabs for hardware that is sitting right there.
    ///
    /// Quiescence is measured on RETAINED publishes only. Live traffic never
    /// stops — this bench pushes thousands of Cast and DNS-SD updates a minute —
    /// so waiting for the socket as a whole to go quiet would always run to the
    /// cap. The replay, by contrast, ends.
    pub async fn settle(&self) {
        let deadline = std::time::Instant::now() + Duration::from_secs(MAX_SETTLE_SECONDS);
        let mut last = usize::MAX;
        loop {
            tokio::time::sleep(Duration::from_millis(QUIET_MS)).await;
            let seen = self.state.lock().map(|g| g.retained_seen).unwrap_or(0);
            if seen == last {
                return;
            }
            if std::time::Instant::now() >= deadline {
                println!(
                    "⚠️  [DISCOVERED-GUI] retained replay still arriving after {MAX_SETTLE_SECONDS}s ({seen} messages) — building anyway"
                );
                return;
            }
            last = seen;
        }
    }
}

/// Delete a retained topic: MQTT does this with an empty retained payload.
fn client_publish_empty(client: &rumqttc::Client, topic: &str) -> Result<(), rumqttc::ClientError> {
    client.publish(topic, rumqttc::QoS::AtLeastOnce, true, Vec::<u8>::new())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn fields(pairs: &[(&str, &str)]) -> Fields {
        pairs.iter().map(|(k, v)| (k.to_string(), v.to_string())).collect()
    }

    #[test]
    fn visa_topic_becomes_a_row_with_its_write_prefix() {
        let mut state = State::default();
        for (topic, payload) in [
            ("OpenAir/System/Protocols/visa/Device/DMM/34401A/Dev0/model", "34401A"),
            ("OpenAir/System/Protocols/visa/Device/DMM/34401A/Dev0/serial", "MY123"),
            // Write/Read are command topics, not fields.
            ("OpenAir/System/Protocols/visa/Device/DMM/34401A/Dev0/Write", "MEAS?"),
        ] {
            ingest(&mut state, topic, payload, true);
        }
        let row = &state.collected["DMM"]["34401A (Dev0)"];
        assert_eq!(row["model"], "34401A");
        assert_eq!(row["serial"], "MY123");
        assert!(!row.contains_key("Write"));
        assert_eq!(
            row["_topic_prefix"],
            "OpenAir/System/Protocols/visa/Device/DMM/34401A/Dev0"
        );
    }

    #[test]
    fn ptp_segment_splits_from_the_right() {
        let mut state = State::default();
        // The clock id contains both colons and dashes, which is why this splits
        // from the right rather than the left.
        ingest(&mut state, "OpenAir/System/Protocols/ptp/Device/00:1d:c1:ff-fe-02-3/role", "master", true);
        assert!(state.collected["ptp"].contains_key("00:1d:c1:ff-fe-02 port 3 (domain 3)") == false);
        // Only a trailing `d<domain>` segment is treated as structured.
        assert!(state.collected["ptp"].contains_key("00:1d:c1:ff-fe-02-3"));

        ingest(&mut state, "OpenAir/System/Protocols/ptp/Device/00:1d:c1:ff-fe-02-1-d0/role", "slave", true);
        assert!(state.collected["ptp"].contains_key("00:1d:c1:ff-fe-02 port 1 (domain 0)"));
    }

    #[test]
    fn missing_connected_is_not_offline() {
        // A DNS-SD row has no `connected` field at all; treating absence as false
        // marked every live service red.
        let now = 1_000_000.0;
        let fresh = fields(&[("last_online", &format!("{}", now - 10.0))]);
        assert_eq!(row_state(&fresh, now), "online");

        let stale = fields(&[("last_online", &format!("{}", now - 3600.0))]);
        assert_eq!(row_state(&stale, now), "offline");

        // No timestamp is 'unknown', not 'offline' — colouring it red would
        // assert more than we know.
        assert_eq!(row_state(&fields(&[("model", "x")]), now), "unknown");

        // An explicit negative overrides a fresh timestamp.
        let mut probed = fields(&[("last_online", &format!("{}", now))]);
        probed.insert("connected".into(), "0".into());
        assert_eq!(row_state(&probed, now), "offline");

        // As does the heartbeat's verdict.
        let mut unreachable = fields(&[("last_online", &format!("{}", now))]);
        unreachable.insert("reachable".into(), "false".into());
        assert_eq!(row_state(&unreachable, now), "offline");
    }

    #[test]
    fn preferred_columns_lead_and_hidden_ones_never_appear() {
        let mut blocks = Blocks::new();
        // Stamped from the current clock, not a literal: `rows_for` classifies
        // against wall-clock now, so a baked-in timestamp makes the row's state
        // depend on the date the test is run.
        let now = unix_now();
        blocks.insert(
            "34401A (Dev0)".to_string(),
            fields(&[
                ("serial", "MY123"),
                ("model", "34401A"),
                ("zzz_extra", "1"),
                ("_topic_prefix", "x"),
                ("connected", "1"),
                ("last_online", &format!("{now}")),
            ]),
        );
        let (headers, rows) = rows_for("DMM", &blocks, false);

        // Preferred order first, then whatever is left alphabetically.
        assert_eq!(headers[0], "model");
        assert_eq!(headers[1], "serial");
        assert_eq!(headers.last().unwrap(), "zzz_extra");
        // last_seen is derived from last_online and IS a column.
        assert!(headers.contains(&"last_seen".to_string()));
        // The hidden set never becomes a column…
        for hidden in HIDDEN_COLUMNS {
            assert!(!headers.contains(&hidden.to_string()), "{hidden} leaked into headers");
        }
        // …but is still carried in the row for the widget's own use.
        assert_eq!(rows[0]["_topic_prefix"], "x");
        assert_eq!(rows[0]["_row_state"], "online");
    }

    #[test]
    fn a_scan_in_progress_makes_every_row_provisional() {
        let mut blocks = Blocks::new();
        blocks.insert("a".to_string(), fields(&[("last_online", "99999999999")]));
        let (_, rows) = rows_for("DMM", &blocks, true);
        assert_eq!(rows[0]["_row_state"], "unknown");
    }

    #[test]
    fn categories_land_in_the_right_tab_group() {
        // Network discoveries are named explicitly…
        assert_eq!(group_for("ravenna"), "4_Audio_Over_IP");
        assert_eq!(group_for("printers"), "12_Other");
        assert_eq!(group_for("cast_Speaker"), "10_Google and Apple");
        // …and anything left came off the bench, including instrument types
        // nobody has added to a list yet.
        assert_eq!(group_for("DMM"), "1_Lab_Instruments");
        assert_eq!(group_for("SomeNewInstrumentType"), "1_Lab_Instruments");
        // PTP is promoted out of the groups entirely.
        assert_eq!(top_level_tab("ptp"), Some(("5_PTP", "PTP")));
        assert_eq!(top_level_tab("DMM"), None);
    }

    /// A real panel, as the Python builder wrote it for this bench's N9340B.
    ///
    /// Kept verbatim as the equivalence check for the port: same retained topics
    /// in, same document out — including header order, which column names are
    /// hidden, and how a unix `last_online` is rendered.
    const GOLDEN_SPECTRUM: &str = r#"{
      "Spectrum": {
        "type": "OcaBin",
        "description": { "En": "Discovered Spectrum devices (scan snapshot)" },
        "behavior": { "overflow_ns": "auto" },
        "blocks": {
          "Devices": {
            "type": "OcaTable",
            "description": { "En": "Discovered Spectrum devices" },
            "topic": "OpenAir/System/Gui/Discovered/Spectrum",
            "headers": ["model", "manufacturer", "serial", "firmware",
                        "resource", "status", "notes", "last_seen"],
            "data": [{
              "connected": "1",
              "_topic_prefix": "OpenAir/System/Protocols/visa/Device/Spectrum/N9340B/Dev0",
              "device_type": "Spectrum",
              "firmware": "A.02.07",
              "last_online": "1785199667",
              "manufacturer": "Keysight Technologies",
              "model": "N9340B",
              "notes": "Handheld (100 kHz - 3 GHz)",
              "raw_idn": "Keysight Technologies,N9340B,CN03480580,A.02.07",
              "resource": "TCPIP::44.44.44.66::INSTR",
              "serial": "CN03480580",
              "status": "identified",
              "reachable": "1",
              "last_seen": "2026-07-27 20:47:47"
            }],
            "Sort": true
          }
        }
      }
    }"#;

    #[test]
    fn matches_the_panel_the_python_builder_wrote() {
        let mut state = State::default();
        let prefix = "OpenAir/System/Protocols/visa/Device/Spectrum/N9340B/Dev0";
        for (key, value) in [
            ("connected", "1"),
            ("device_type", "Spectrum"),
            ("firmware", "A.02.07"),
            ("last_online", "1785199667"),
            ("manufacturer", "Keysight Technologies"),
            ("model", "N9340B"),
            ("notes", "Handheld (100 kHz - 3 GHz)"),
            ("raw_idn", "Keysight Technologies,N9340B,CN03480580,A.02.07"),
            ("resource", "TCPIP::44.44.44.66::INSTR"),
            ("serial", "CN03480580"),
            ("status", "identified"),
            ("reachable", "1"),
        ] {
            ingest(&mut state, &format!("{prefix}/{key}"), value, true);
        }

        let root = std::env::temp_dir().join(format!("openair-discovered-{}", std::process::id()));
        let _ = std::fs::remove_dir_all(&root);
        write_panels(&root, &state.collected, false).expect("panels written");

        let written = std::fs::read_to_string(
            root.join("FrontEnd/Gui_Frames/0_discovered/1_Lab_Instruments/Spectrum/Spectrum.json"),
        )
        .expect("Spectrum panel exists at the grouped path");
        let _ = std::fs::remove_dir_all(&root);

        let mut ours: serde_json::Value = serde_json::from_str(&written).unwrap();
        let golden: serde_json::Value = serde_json::from_str(GOLDEN_SPECTRUM).unwrap();

        // `_row_state` is the one field that depends on the wall clock rather
        // than the input, so it is asserted by its own tests instead.
        ours["Spectrum"]["blocks"]["Devices"]["data"][0]
            .as_object_mut()
            .unwrap()
            .remove("_row_state");

        assert_eq!(ours, golden);
    }

    #[test]
    fn only_a_live_truthy_clear_empties_the_mirror() {
        let seeded = || {
            let mut state = State::default();
            ingest(
                &mut state,
                "OpenAir/System/Protocols/visa/Device/DMM/34401A/Dev0/model",
                "34401A",
                true,
            );
            assert!(!state.collected.is_empty());
            state
        };

        // A live press wipes it.
        let mut state = seeded();
        ingest(&mut state, CLEAR_TOPIC, "1", false);
        assert!(state.collected.is_empty());

        // A RETAINED replay must not. The browser leaves one on this topic, so
        // every reconnect would otherwise empty the mirror — and an empty mirror
        // prunes every tab off disk.
        let mut state = seeded();
        ingest(&mut state, CLEAR_TOPIC, "1", true);
        assert!(!state.collected.is_empty(), "retained Clear wiped the mirror");

        // Nor may a falsey payload. `{"value":0}` is the button at rest — and is
        // exactly what sits retained on this bench's broker.
        let mut state = seeded();
        ingest(&mut state, CLEAR_TOPIC, r#"{"value":0}"#, false);
        assert!(!state.collected.is_empty(), "falsey Clear wiped the mirror");
    }
}
