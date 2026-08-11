//! Golden-vector suite — consumes the SAME ../../vectors/topics.json as the
//! TypeScript tests. Add cases to the vector file, not here.

use openair_contracts::topics;
use serde_json::Value;

static VECTORS: &str = include_str!("../../vectors/topics.json");

fn vectors() -> Value {
    serde_json::from_str(VECTORS).expect("vectors/topics.json parses")
}

fn s<'a>(v: &'a Value, key: &str) -> &'a str {
    v[key].as_str().unwrap_or_else(|| panic!("missing string {key} in {v}"))
}

fn build(family: &str, args: &Value) -> Result<String, topics::TopicError> {
    match family {
        "discovery" => topics::discovery(s(args, "protocol"), s(args, "deviceId")),
        "discoveryWildcard" => topics::discovery_wildcard(args["protocol"].as_str()),
        "guiWildcard" => Ok(topics::gui_wildcard()),
        "yakCmd" => topics::yak_cmd(s(args, "verb"), s(args, "deviceClass"), s(args, "model")),
        "yakState" => topics::yak_state(s(args, "deviceClass"), s(args, "model"), s(args, "capability")),
        "yakMonitor" => topics::yak_monitor(s(args, "dir")),
        "tests" => {
            let path: Vec<&str> = args["path"]
                .as_array()
                .map(|a| a.iter().map(|v| v.as_str().expect("path segment is a string")).collect())
                .unwrap_or_default();
            topics::tests(s(args, "suite"), &path)
        }
        "testsPrefix" => topics::tests_prefix(s(args, "suite")),
        "testsWildcard" => topics::tests_wildcard(args["suite"].as_str()),
        "agents" => topics::agents(s(args, "agent")),
        "agentsWildcard" => Ok(topics::agents_wildcard()),
        "config" => topics::config(s(args, "agent")),
        "log" => topics::log(s(args, "source"), s(args, "level")),
        other => panic!("vector family not implemented in Rust: {other}"),
    }
}

#[test]
fn build_vectors() {
    for v in vectors()["build"].as_array().expect("build array") {
        let family = s(v, "family");
        let topic = build(family, &v["args"]).unwrap_or_else(|e| panic!("{family}: {e}"));
        assert_eq!(topic, s(v, "topic"), "family {family}");
    }
}

#[test]
fn build_invalid_vectors() {
    for v in vectors()["buildInvalid"].as_array().expect("buildInvalid array") {
        let family = s(v, "family");
        let why = s(v, "why");
        assert!(build(family, &v["args"]).is_err(), "{family} should reject: {why}");
    }
}

#[test]
fn parse_vectors() {
    for v in vectors()["parse"].as_array().expect("parse array") {
        let topic = s(v, "topic");
        let got = serde_json::to_value(topics::parse(topic)).expect("serialize parse result");
        assert_eq!(got, v["parsed"], "parse {topic}");
    }
}

#[test]
fn gui_from_panel_path_vectors() {
    for v in vectors()["guiFromPanelPath"].as_array().expect("guiFromPanelPath array") {
        let path = s(v, "filePath");
        assert_eq!(topics::gui_prefix_from_panel_path(path), s(v, "topic"), "path {path:?}");
    }
}

#[test]
fn is_legacy_matches_parse_kind() {
    for v in vectors()["parse"].as_array().expect("parse array") {
        let topic = s(v, "topic");
        let expected = v["parsed"]["kind"] == "legacy";
        assert_eq!(topics::is_legacy(topic), expected, "isLegacy {topic}");
    }
}
