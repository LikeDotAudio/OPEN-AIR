use serde::{Deserialize, Serialize};
use serde_json::Value;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct YakHandler {
    #[serde(default)]
    pub enable: bool,
    #[serde(default)]
    pub yak_type: String, // "set", "rig", "nab", "do"
    #[serde(default)]
    pub sub_path: String,
    #[serde(default)]
    pub command: String,
    #[serde(default)]
    pub input_name: String,
    #[serde(default)]
    pub converter: String,

    /// Where this control's SCPI goes — the VISA daemon's Write topic for ONE
    /// instrument (`.../visa/Device/DMM/34401A/Dev3/Write`).
    ///
    /// Stamped per instance by Deployment/build_instrument_panels.py, so eight
    /// discovered 34401As get eight panels that each drive their own meter.
    /// Absent on hand-authored panels, which fall back to the global publish
    /// topic — historically the only path, and one nothing subscribes to, which
    /// is why panels never actually moved an instrument.
    #[serde(default)]
    pub target: Option<String>,

    /// The instrument model this instance is bound to, so SCPI lookup uses that
    /// model's command table instead of "first command of this name found in
    /// any model" — a fallback that silently sends a Rigol's syntax to an
    /// Agilent when two models share a command name.
    #[serde(default)]
    pub model: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IncomingMessage {
    #[serde(default)]
    pub handler: String,
    pub yak_handler: Option<YakHandler>,
    
    // Optional metadata to identify the target model
    pub model: Option<String>,
    pub device: Option<String>,
    
    // Capture any additional fields, such as the actual value to set (e.g. hz_value)
    #[serde(flatten)]
    pub extra: Value,
}
