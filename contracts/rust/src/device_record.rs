//! DeviceRecord wrapper — re-exports the generated types and adds the v40
//! extraction path: the typed VISA merge object and the lossless mapping
//! into the canonical document. Twin of `contracts/src/device-record.ts`.

use serde::{Deserialize, Serialize};

pub use crate::gen::device_record::{
    DeviceRecord, DeviceRecordDeviceId, DeviceRecordExtra, DeviceRecordExtraMidi,
    DeviceRecordExtraVisa, DeviceRecordFirstSeen, DeviceRecordLastSeen, DeviceRecordProtocol,
    DeviceRecordStatus,
};

type ConvErr = crate::gen::device_record::error::ConversionError;

/// v0: the VISA agent's merge object (orchestrator main.rs:267-295).
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct LegacyVisaRecordV0 {
    pub manufacturer: String,
    pub model: String,
    pub serial: String,
    pub firmware: String,
    pub raw_idn: String,
    pub resource: String,
    /// "found" | "identified"
    pub status: String,
    pub device_type: String,
    pub notes: String,
    /// unix seconds, stamped once at scan time
    pub last_online: f64,
    /// 0 | 1 — the boolean-that-goes-stale D4 bans in v41
    pub connected: u8,
}

fn none_if_empty(s: &str) -> Option<String> {
    if s.is_empty() { None } else { Some(s.to_string()) }
}

/// The step-3e replay proof (mirror of `mapV40VisaRecord`): today's VISA
/// fields map losslessly into a valid DeviceRecord. `Dev{n}` scan-order
/// identity is deliberately DISCARDED in favor of the D2 derivation.
/// Status rule: `found` → `discovered`; `identified` + `connected:1` →
/// `identified`; `identified` + `connected:0` → `unresponsive`.
pub fn map_v40_visa_record(v0: &LegacyVisaRecordV0) -> Result<DeviceRecord, String> {
    let last_seen = crate::time::from_unix_seconds(v0.last_online);
    let status = if v0.status == "found" {
        DeviceRecordStatus::Discovered
    } else if v0.connected == 1 {
        DeviceRecordStatus::Identified
    } else {
        DeviceRecordStatus::Unresponsive
    };
    let device_id = crate::identity::device_id_for(
        "visa",
        Some(&v0.serial),
        Some(&v0.resource),
        Some(&v0.manufacturer),
        Some(&v0.model),
    );
    Ok(DeviceRecord {
        address: v0.resource.clone(),
        device_class: v0.device_type.clone(),
        device_id: device_id.parse().map_err(|e: ConvErr| e.to_string())?,
        extra: Some(DeviceRecordExtra {
            midi: None,
            visa: Some(DeviceRecordExtraVisa { resource: v0.resource.clone() }),
        }),
        firmware: none_if_empty(&v0.firmware),
        first_seen: last_seen.parse().map_err(|e: ConvErr| e.to_string())?,
        last_seen: last_seen.parse().map_err(|e: ConvErr| e.to_string())?,
        make: v0.manufacturer.clone(),
        model: v0.model.clone(),
        notes: none_if_empty(&v0.notes),
        protocol: "visa".parse().map_err(|e: ConvErr| e.to_string())?,
        raw_idn: none_if_empty(&v0.raw_idn),
        schema_version: 1.0,
        serial: none_if_empty(&v0.serial),
        status,
    })
}
