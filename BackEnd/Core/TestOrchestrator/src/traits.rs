use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GuiCommand {
    pub topic: String,
    pub payload: serde_json::Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrchestratorStepResult {
    pub status: String,
    pub data: serde_json::Value,
}

pub trait TestOrchestrator: Send + Sync {
    fn name(&self) -> &'static str;
    fn topic_prefix(&self) -> &'static str;
    fn initialize(&mut self) -> bool;
    fn handle_gui_command(&mut self, cmd: GuiCommand) -> Option<serde_json::Value>;
    fn execute_step(&mut self) -> OrchestratorStepResult;
    fn is_running(&self) -> bool;
}
