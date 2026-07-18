//! AgentHeartbeat wrapper — re-exports the generated types (gen/ is typify
//! output, never hand-edited) and adds the behavior half of the contract:
//! the H2 LWT helper. Twin of `contracts/src/heartbeat.ts`.

use serde::{Deserialize, Serialize};

pub use crate::gen::agent_heartbeat::{
    AgentHeartbeat, AgentHeartbeatAgent, AgentHeartbeatLastBeat, AgentHeartbeatStartedAt,
    AgentHeartbeatStatus,
};

type ConvErr = crate::gen::agent_heartbeat::error::ConversionError;

/// H2 — the exact Last Will every connecting agent (and browser) registers.
/// `startedAt`/`lastBeat` are fixed at connect time; a delivered LWT means
/// "died no later than keepalive after lastBeat".
pub fn heartbeat_lwt(
    agent: &str,
    connected_at_iso: &str,
    partition: Option<&str>,
) -> Result<(String, AgentHeartbeat), String> {
    let topic = crate::topics::agents(agent).map_err(|e| e.to_string())?;
    let payload = AgentHeartbeat {
        agent: agent.parse().map_err(|e: ConvErr| e.to_string())?,
        host: None,
        last_beat: connected_at_iso.parse().map_err(|e: ConvErr| e.to_string())?,
        partition: partition.map(String::from),
        pid: None,
        schema_version: 1.0,
        started_at: connected_at_iso.parse().map_err(|e: ConvErr| e.to_string())?,
        status: AgentHeartbeatStatus::Offline,
        version: None,
    };
    Ok((topic, payload))
}

/// v0 (the wild west): today's browser Failover payload
/// (MqttProvider.jsx:85-93) — typed so tooling can NAME what it finds on the
/// bus. Never emitted by new code.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct LegacyFailoverHeartbeatV0 {
    pub guid: String,
    pub full_id: String,
    pub partition: String,
    pub active: bool,
    pub start_ts: f64,
    pub timestamp: f64,
}
