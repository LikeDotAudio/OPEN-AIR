//! Hand-written mirror of `contracts/src/topics/` — build + parse for the
//! whole OpenAir namespace. Behavior is pinned to the TypeScript side by
//! `contracts/vectors/topics.json`; change a vector, not just this file.
//! Zero dependencies beyond serde (no regex crate — validation is manual).

use serde::{Deserialize, Serialize};
use std::fmt;

pub const ROOT: &str = "OpenAir";
pub const GUI_ROOT: &str = "OpenAir/Gui";

pub const YAK_VERBS: [&str; 4] = ["set", "rig", "nab", "do"];
pub const MONITOR_DIRS: [&str; 2] = ["in", "out"];
pub const LOG_LEVELS: [&str; 5] = ["trace", "debug", "info", "warn", "error"];

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TopicError {
    pub what: &'static str,
    pub value: String,
}

impl fmt::Display for TopicError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "invalid topic {}: {:?}", self.what, self.value)
    }
}

impl std::error::Error for TopicError {}

fn err(what: &'static str, value: &str) -> TopicError {
    TopicError { what, value: value.to_string() }
}

/// Plain segment: `[A-Za-z0-9_-]+` (guidelines T4 — no spaces, no wildcards).
pub fn is_segment(s: &str) -> bool {
    !s.is_empty() && s.chars().all(|c| c.is_ascii_alphanumeric() || c == '_' || c == '-')
}

/// Device identity (guidelines D2): `{protocol}:{stableKey}`, where the key
/// may carry VISA-resource characters (`.`, `:`) but never `/ + #` or spaces.
pub fn is_device_id(s: &str) -> bool {
    match s.split_once(':') {
        Some((proto, key)) => {
            !proto.is_empty()
                && proto.chars().all(|c| c.is_ascii_lowercase() || c.is_ascii_digit())
                && !key.is_empty()
                && key.chars().all(|c| {
                    c.is_ascii_alphanumeric() || matches!(c, '.' | '_' | ':' | '-')
                })
        }
        None => false,
    }
}

/// Capability id (guidelines Y3): dotted path of plain segments.
pub fn is_capability(s: &str) -> bool {
    !s.is_empty() && s.split('.').all(is_segment)
}

fn seg(what: &'static str, s: &str) -> Result<(), TopicError> {
    if is_segment(s) { Ok(()) } else { Err(err(what, s)) }
}

// ---------------------------------------------------------------- builders

pub fn discovery(protocol: &str, device_id: &str) -> Result<String, TopicError> {
    seg("protocol", protocol)?;
    if !is_device_id(device_id) {
        return Err(err("deviceId", device_id));
    }
    Ok(format!("{ROOT}/Discovery/{protocol}/{device_id}"))
}

pub fn discovery_wildcard(protocol: Option<&str>) -> Result<String, TopicError> {
    match protocol {
        None => Ok(format!("{ROOT}/Discovery/#")),
        Some(p) => {
            seg("protocol", p)?;
            Ok(format!("{ROOT}/Discovery/{p}/+"))
        }
    }
}

pub fn gui_wildcard() -> String {
    format!("{GUI_ROOT}/#")
}

pub fn yak_cmd(verb: &str, device_class: &str, model: &str) -> Result<String, TopicError> {
    if !YAK_VERBS.contains(&verb) {
        return Err(err("verb", verb));
    }
    seg("deviceClass", device_class)?;
    seg("model", model)?;
    Ok(format!("{ROOT}/Yak/cmd/{verb}/{device_class}/{model}"))
}

pub fn yak_state(device_class: &str, model: &str, capability: &str) -> Result<String, TopicError> {
    seg("deviceClass", device_class)?;
    seg("model", model)?;
    if !is_capability(capability) {
        return Err(err("capability", capability));
    }
    Ok(format!("{ROOT}/Yak/state/{device_class}/{model}/{capability}"))
}

pub fn yak_monitor(dir: &str) -> Result<String, TopicError> {
    if !MONITOR_DIRS.contains(&dir) {
        return Err(err("monitor dir", dir));
    }
    Ok(format!("{ROOT}/Yak/monitor/{dir}"))
}

pub fn agents(agent: &str) -> Result<String, TopicError> {
    seg("agent", agent)?;
    Ok(format!("{ROOT}/System/Agents/{agent}"))
}

pub fn agents_wildcard() -> String {
    format!("{ROOT}/System/Agents/+")
}

pub fn config(agent: &str) -> Result<String, TopicError> {
    seg("agent", agent)?;
    Ok(format!("{ROOT}/System/Config/{agent}"))
}

pub fn log(source: &str, level: &str) -> Result<String, TopicError> {
    seg("source", source)?;
    if !LOG_LEVELS.contains(&level) {
        return Err(err("log level", level));
    }
    Ok(format!("{ROOT}/System/Log/{source}/{level}"))
}

// ------------------------------------------------------------------ parse

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(tag = "kind")]
pub enum ParsedTopic {
    #[serde(rename = "discovery")]
    Discovery {
        protocol: String,
        #[serde(rename = "deviceId")]
        device_id: String,
    },
    #[serde(rename = "gui")]
    Gui { segments: Vec<String> },
    #[serde(rename = "yakCmd")]
    YakCmd {
        verb: String,
        #[serde(rename = "deviceClass")]
        device_class: String,
        model: String,
    },
    #[serde(rename = "yakState")]
    YakState {
        #[serde(rename = "deviceClass")]
        device_class: String,
        model: String,
        capability: String,
    },
    #[serde(rename = "yakMonitor")]
    YakMonitor { dir: String },
    #[serde(rename = "agents")]
    Agents { agent: String },
    #[serde(rename = "config")]
    Config { agent: String },
    #[serde(rename = "log")]
    Log { source: String, level: String },
    #[serde(rename = "legacy")]
    Legacy(LegacyTopic),
    #[serde(rename = "unknown")]
    Unknown { raw: String },
}

/// The v40 namespace map (guidelines T7) — same families as topics/legacy.ts.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct LegacyTopic {
    pub family: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub protocol: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub channel: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub guid: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub segments: Option<Vec<String>>,
}

impl LegacyTopic {
    fn new(family: &str) -> Self {
        LegacyTopic { family: family.to_string(), protocol: None, channel: None, guid: None, segments: None }
    }
}

fn classify_legacy(segs: &[&str]) -> Option<LegacyTopic> {
    let s1 = segs.get(1).copied();
    let s2 = segs.get(2).copied();
    let s3 = segs.get(3).copied();
    let rest: Vec<&str> = segs.iter().skip(4).copied().collect();

    if s1 == Some("Protocol") {
        if let Some(channel) = s2 {
            let mut t = LegacyTopic::new("wsSideBus");
            t.channel = Some(channel.to_string());
            t.segments = Some(segs.iter().skip(3).map(|s| s.to_string()).collect());
            return Some(t);
        }
        return None;
    }
    if s1 != Some("System") {
        return None;
    }
    if s2 == Some("Failover") && s3 == Some("WEB") && rest.len() == 2 && rest[0] == "Heartbeat" {
        let mut t = LegacyTopic::new("failoverWebHeartbeat");
        t.guid = Some(rest[1].to_string());
        return Some(t);
    }
    if s2 != Some("Protocols") {
        return None;
    }
    let proto = s3?;
    if proto == "visa" && rest.first() == Some(&"Device") {
        let mut t = LegacyTopic::new("visaDeviceTree");
        t.segments = Some(rest.iter().skip(1).map(|s| s.to_string()).collect());
        return Some(t);
    }
    if proto == "midi" && rest.first() == Some(&"Device") {
        let mut t = LegacyTopic::new("midiDeviceTree");
        t.segments = Some(rest.iter().skip(1).map(|s| s.to_string()).collect());
        return Some(t);
    }
    if proto == "yak" {
        let mut t = LegacyTopic::new("yakAgent");
        t.channel = Some(rest.join("/"));
        return Some(t);
    }
    if rest.is_empty() || rest == ["status"] {
        let mut t = LegacyTopic::new("protocolStatus");
        t.protocol = Some(proto.to_string());
        return Some(t);
    }
    if rest == ["config"] {
        let mut t = LegacyTopic::new("protocolConfig");
        t.protocol = Some(proto.to_string());
        return Some(t);
    }
    None
}

pub fn parse(raw: &str) -> ParsedTopic {
    let segs: Vec<&str> = raw.split('/').collect();
    let unknown = ParsedTopic::Unknown { raw: raw.to_string() };
    if segs.first() != Some(&ROOT) || segs.iter().any(|s| s.is_empty()) {
        return unknown;
    }
    if let Some(legacy) = classify_legacy(&segs) {
        return ParsedTopic::Legacy(legacy);
    }
    let s2 = segs.get(2).copied();
    let s3 = segs.get(3).copied();
    let s4 = segs.get(4).copied();
    let s5 = segs.get(5).copied();
    match segs.get(1).copied() {
        Some("Discovery") => match (s2, s3, s4) {
            (Some(p), Some(id), None) if is_segment(p) && is_device_id(id) => ParsedTopic::Discovery {
                protocol: p.to_string(),
                device_id: id.to_string(),
            },
            _ => unknown,
        },
        Some("Gui") => ParsedTopic::Gui {
            segments: segs.iter().skip(2).map(|s| s.to_string()).collect(),
        },
        Some("Yak") => match (s2, s3, s4, s5) {
            (Some("monitor"), Some(dir), None, _) if MONITOR_DIRS.contains(&dir) => {
                ParsedTopic::YakMonitor { dir: dir.to_string() }
            }
            (Some("cmd"), Some(verb), Some(class), Some(model))
                if segs.len() == 6 && YAK_VERBS.contains(&verb) && is_segment(class) && is_segment(model) =>
            {
                ParsedTopic::YakCmd {
                    verb: verb.to_string(),
                    device_class: class.to_string(),
                    model: model.to_string(),
                }
            }
            (Some("state"), Some(class), Some(model), Some(cap))
                if segs.len() == 6 && is_segment(class) && is_segment(model) =>
            {
                ParsedTopic::YakState {
                    device_class: class.to_string(),
                    model: model.to_string(),
                    capability: cap.to_string(),
                }
            }
            _ => unknown,
        },
        Some("System") => match (s2, s3, s4, s5) {
            (Some("Agents"), Some(agent), None, _) if is_segment(agent) => {
                ParsedTopic::Agents { agent: agent.to_string() }
            }
            (Some("Config"), Some(agent), None, _) if is_segment(agent) => {
                ParsedTopic::Config { agent: agent.to_string() }
            }
            (Some("Log"), Some(source), Some(level), None) if is_segment(source) && LOG_LEVELS.contains(&level) => {
                ParsedTopic::Log {
                    source: source.to_string(),
                    level: level.to_string(),
                }
            }
            _ => unknown,
        },
        _ => unknown,
    }
}

pub fn is_legacy(raw: &str) -> bool {
    matches!(parse(raw), ParsedTopic::Legacy(_))
}

// --------------------------------------------- panel path → GUI topic

/// Canonized `topicMaker.jsx` semantics — the TS twin is
/// `contracts/src/topics/gui-path.ts`; the vector suite pins both.
pub fn gui_prefix_from_panel_path(file_path: &str) -> String {
    let segs = gui_segments_from_panel_path(file_path);
    if segs.is_empty() {
        GUI_ROOT.to_string()
    } else {
        format!("{GUI_ROOT}/{}", segs.join("/"))
    }
}

pub fn gui_segments_from_panel_path(file_path: &str) -> Vec<String> {
    let mut parts: Vec<&str> = file_path.split('/').filter(|p| !p.is_empty()).collect();
    if let Some(last) = parts.last() {
        if has_file_extension(last) {
            parts.pop();
        }
    }
    parts.iter().filter_map(|p| {
        let n = normalize_part(p);
        if n.is_empty() { None } else { Some(n) }
    }).collect()
}

const SKIP_TOKENS: [&str; 6] = ["display", "window", "left", "right", "top", "bottom"];

fn has_file_extension(s: &str) -> bool {
    match s.rfind('.') {
        Some(i) => {
            let ext = &s[i + 1..];
            !ext.is_empty() && ext.chars().all(|c| c.is_ascii_alphanumeric())
        }
        None => false,
    }
}

fn normalize_part(raw: &str) -> String {
    if raw.is_empty() {
        return String::new();
    }
    if raw.eq_ignore_ascii_case("oagui") {
        return "GUI".to_string();
    }
    if raw.chars().all(|c| c.is_ascii_digit()) {
        return String::new();
    }
    // strip a leading "<n>_" / "<n>-" ordering prefix
    let digits_end = raw.find(|c: char| !c.is_ascii_digit()).unwrap_or(raw.len());
    let mut clean = &raw[digits_end..];
    if digits_end > 0 {
        clean = clean.strip_prefix(['_', '-']).unwrap_or(clean);
    }
    if clean.is_empty() {
        return String::new();
    }
    // base = clean with a trailing "[_-]?<digits>" suffix removed, lowercased
    let bytes = clean.as_bytes();
    let mut i = bytes.len();
    while i > 0 && bytes[i - 1].is_ascii_digit() {
        i -= 1;
    }
    let mut base_end = bytes.len();
    if i < bytes.len() {
        base_end = i;
        if i > 0 && (bytes[i - 1] == b'_' || bytes[i - 1] == b'-') {
            base_end = i - 1;
        }
    }
    let base = clean[..base_end].to_lowercase();
    if SKIP_TOKENS.contains(&base.as_str()) {
        return String::new();
    }
    // whitespace runs → single '_'
    let mut out = String::with_capacity(clean.len());
    let mut in_ws = false;
    for c in clean.chars() {
        if c.is_whitespace() {
            if !in_ws {
                out.push('_');
                in_ws = true;
            }
        } else {
            out.push(c);
            in_ws = false;
        }
    }
    out
}
