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
