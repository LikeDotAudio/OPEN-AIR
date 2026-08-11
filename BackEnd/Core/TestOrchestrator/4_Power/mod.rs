use serde::{Deserialize, Serialize};
use serde_json::json;
use crate::traits::{GuiCommand, OrchestratorStepResult, TestOrchestrator};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PowerTestOrchestrator {
    pub psu_linked: bool,
    pub master_v_max: f64,
    pub master_i_max: f64,
    pub master_output_on: bool,
}

impl PowerTestOrchestrator {
    pub fn new() -> Self {
        Self {
            psu_linked: true,
            master_v_max: 24.0,
            master_i_max: 5.0,
            master_output_on: false,
        }
    }
}

impl TestOrchestrator for PowerTestOrchestrator {
    fn name(&self) -> &'static str {
        "Power_Test"
    }

    fn topic_prefix(&self) -> &'static str {
        "OpenAir/Tests/Power"
    }

    fn initialize(&mut self) -> bool {
        self.psu_linked = true;
        self.master_v_max = 24.0;
        self.master_i_max = 5.0;
        self.master_output_on = false;
        true
    }

    fn handle_gui_command(&mut self, cmd: GuiCommand) -> Option<serde_json::Value> {
        if cmd.topic.ends_with("/Master/LinkMode") {
            if let Some(val) = cmd.payload.as_bool() {
                self.psu_linked = val;
                return Some(json!({ "psu_linked": self.psu_linked }));
            }
        } else if cmd.topic.ends_with("/Master/VoltageMax") {
            if let Some(val) = cmd.payload.as_f64() {
                self.master_v_max = val;
                return Some(json!({ "master_v_max": self.master_v_max }));
            }
        } else if cmd.topic.ends_with("/Master/CurrentMax") {
            if let Some(val) = cmd.payload.as_f64() {
                self.master_i_max = val;
                return Some(json!({ "master_i_max": self.master_i_max }));
            }
        } else if cmd.topic.ends_with("/Master/OutputToggle") {
            if let Some(val) = cmd.payload.as_bool() {
                self.master_output_on = val;
                return Some(json!({ "master_output_on": self.master_output_on }));
            }
        }
        None
    }

    fn execute_step(&mut self) -> OrchestratorStepResult {
        if !self.master_output_on {
            return OrchestratorStepResult {
                status: "OUTPUT_OFF".to_string(),
                data: json!({ "total_power_w": 0.0 }),
            };
        }

        let psu_total_w = 134.8;
        let load_1_w = 30.05;
        let load_2_w = 49.99;
        let eff_val: f64 = ((load_1_w + load_2_w) / psu_total_w) * 100.0;

        OrchestratorStepResult {
            status: "OUTPUT_ACTIVE".to_string(),
            data: json!({
                "total_psu_power_w": psu_total_w,
                "dc_load_1_power_w": load_1_w,
                "dc_load_2_power_w": load_2_w,
                "efficiency_percent": (eff_val * 10.0).round() / 10.0
            }),
        }
    }

    fn is_running(&self) -> bool {
        self.master_output_on
    }
}
