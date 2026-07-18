//! Payload-vector suite — consumes the SAME vectors/payloads and
//! vectors/identity.json as the TypeScript tests, but through the
//! typify-GENERATED types: this is the codegen-fidelity proof (step 3b).

use openair_contracts::device_record::{map_v40_visa_record, DeviceRecord, LegacyVisaRecordV0};
use openair_contracts::heartbeat::{AgentHeartbeat, LegacyFailoverHeartbeatV0};
use openair_contracts::{identity, time};
use serde_json::Value;
use std::fs;
use std::path::PathBuf;

fn vectors_dir() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../vectors")
}

fn docs_in(rel: &str) -> Vec<(String, String)> {
    let dir = vectors_dir().join("payloads").join(rel);
    let mut out = vec![];
    for entry in fs::read_dir(&dir).unwrap_or_else(|e| panic!("read {dir:?}: {e}")) {
        let path = entry.unwrap().path();
        if path.extension().is_some_and(|e| e == "json") {
            out.push((
                format!("{rel}/{}", path.file_name().unwrap().to_string_lossy()),
                fs::read_to_string(&path).unwrap(),
            ));
        }
    }
    assert!(!out.is_empty(), "no vectors under {rel}");
    out
}

#[test]
fn agent_heartbeat_valid() {
    for (name, json) in docs_in("AgentHeartbeat/valid") {
        serde_json::from_str::<AgentHeartbeat>(&json).unwrap_or_else(|e| panic!("{name}: {e}"));
    }
}

#[test]
fn agent_heartbeat_invalid() {
    for (name, json) in docs_in("AgentHeartbeat/invalid") {
        assert!(serde_json::from_str::<AgentHeartbeat>(&json).is_err(), "{name} should fail");
    }
}

#[test]
fn agent_heartbeat_legacy_named_not_v1() {
    for (name, json) in docs_in("AgentHeartbeat/legacy-v0") {
        serde_json::from_str::<LegacyFailoverHeartbeatV0>(&json)
            .unwrap_or_else(|e| panic!("{name} as v0: {e}"));
        assert!(serde_json::from_str::<AgentHeartbeat>(&json).is_err(), "{name} must not pass v1");
    }
}

#[test]
fn device_record_valid() {
    for (name, json) in docs_in("DeviceRecord/valid") {
        serde_json::from_str::<DeviceRecord>(&json).unwrap_or_else(|e| panic!("{name}: {e}"));
    }
}

#[test]
fn device_record_invalid() {
    for (name, json) in docs_in("DeviceRecord/invalid") {
        assert!(serde_json::from_str::<DeviceRecord>(&json).is_err(), "{name} should fail");
    }
}

#[test]
fn device_record_legacy_named_not_v1() {
    for (name, json) in docs_in("DeviceRecord/legacy-v0") {
        serde_json::from_str::<LegacyVisaRecordV0>(&json)
            .unwrap_or_else(|e| panic!("{name} as v0: {e}"));
        assert!(serde_json::from_str::<DeviceRecord>(&json).is_err(), "{name} must not pass v1");
    }
}

#[test]
fn map_v40_visa_record_vectors() {
    for (name, json) in docs_in("DeviceRecord/map") {
        let doc: Value = serde_json::from_str(&json).unwrap();
        let v0: LegacyVisaRecordV0 = serde_json::from_value(doc["input"].clone())
            .unwrap_or_else(|e| panic!("{name} input: {e}"));
        let expected: DeviceRecord = serde_json::from_value(doc["expected"].clone())
            .unwrap_or_else(|e| panic!("{name} expected: {e}"));
        let got = map_v40_visa_record(&v0).unwrap_or_else(|e| panic!("{name}: {e}"));
        assert_eq!(got, expected, "{name}");
    }
}

#[test]
fn identity_and_time_vectors() {
    let v: Value =
        serde_json::from_str(&fs::read_to_string(vectors_dir().join("identity.json")).unwrap())
            .unwrap();
    for case in v["deviceId"].as_array().unwrap() {
        let input = &case["input"];
        let got = identity::device_id_for(
            input["protocol"].as_str().unwrap(),
            input["serial"].as_str(),
            input["address"].as_str(),
            input["make"].as_str(),
            input["model"].as_str(),
        );
        assert_eq!(got, case["deviceId"].as_str().unwrap(), "case {case}");
    }
    for case in v["fnv1a64"].as_array().unwrap() {
        assert_eq!(
            identity::fnv1a64(case["input"].as_str().unwrap()),
            case["hex"].as_str().unwrap()
        );
    }
    for case in v["fromUnixSeconds"].as_array().unwrap() {
        assert_eq!(
            time::from_unix_seconds(case["seconds"].as_f64().unwrap()),
            case["iso"].as_str().unwrap()
        );
    }
}
