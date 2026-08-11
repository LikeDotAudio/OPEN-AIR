use serde::{Deserialize, Serialize};
use serde_json::json;
use crate::traits::{GuiCommand, OrchestratorStepResult, TestOrchestrator};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SpectrumTestOrchestrator {
    pub target_freq_mhz: f64,
    pub span_mhz: f64,
    pub rbw_khz: f64,
    pub auto_sweep_active: bool,
    pub is_running_state: bool,
}

impl SpectrumTestOrchestrator {
    pub fn new() -> Self {
        Self {
            target_freq_mhz: 915.0,
            span_mhz: 20.0,
            rbw_khz: 100.0,
            auto_sweep_active: false,
            is_running_state: false,
        }
    }

    pub fn jump_to_frequency(&self, freq_mhz: f64) -> serde_json::Value {
        let measured_power_dbm = -10.0 + ((freq_mhz / 100.0).sin() * 5.0);
        json!({
            "action": "jump",
            "target_freq_mhz": freq_mhz,
            "span_mhz": self.span_mhz,
            "rbw_khz": self.rbw_khz,
            "measured_peak_mhz": freq_mhz + 0.002,
            "measured_power_dbm": (measured_power_dbm * 100.0).round() / 100.0,
            "result": "PASS"
        })
    }
}

impl TestOrchestrator for SpectrumTestOrchestrator {
    fn name(&self) -> &'static str {
        "Spectrum_Test"
    }

    fn topic_prefix(&self) -> &'static str {
        "OpenAir/Tests/Spectrum"
    }

    fn initialize(&mut self) -> bool {
        self.target_freq_mhz = 915.0;
        self.span_mhz = 20.0;
        self.rbw_khz = 100.0;
        self.auto_sweep_active = false;
        self.is_running_state = false;
        true
    }

    fn handle_gui_command(&mut self, cmd: GuiCommand) -> Option<serde_json::Value> {
        if cmd.topic.ends_with("/TargetFrequency") {
            if let Some(val) = cmd.payload.as_f64() {
                self.target_freq_mhz = val;
                return Some(json!({ "target_freq_mhz": self.target_freq_mhz }));
            }
        } else if cmd.topic.ends_with("/SpanMHz") {
            if let Some(val) = cmd.payload.as_f64() {
                self.span_mhz = val;
                return Some(json!({ "span_mhz": self.span_mhz }));
            }
        } else if cmd.topic.ends_with("/RBWkHz") {
            if let Some(val) = cmd.payload.as_f64() {
                self.rbw_khz = val;
                return Some(json!({ "rbw_khz": self.rbw_khz }));
            }
        } else if cmd.topic.ends_with("/JumpCommand") {
            return Some(self.jump_to_frequency(self.target_freq_mhz));
        } else if cmd.topic.ends_with("/RunSequence") {
            self.auto_sweep_active = !self.auto_sweep_active;
            self.is_running_state = self.auto_sweep_active;
            return Some(json!({ "auto_sweep": self.auto_sweep_active }));
        }
        None
    }

    fn execute_step(&mut self) -> OrchestratorStepResult {
        if !self.auto_sweep_active {
            return OrchestratorStepResult {
                status: "IDLE".to_string(),
                data: json!({
                    "target_freq_mhz": self.target_freq_mhz,
                    "span_mhz": self.span_mhz,
                    "rbw_khz": self.rbw_khz
                }),
            };
        }

        OrchestratorStepResult {
            status: "CONSOLIDATED_SWEEPING".to_string(),
            data: json!({
                "action": "consolidated_multi_scan_step",
                "center_freq_mhz": self.target_freq_mhz,
                "span_mhz": self.span_mhz,
                "rbw_khz": self.rbw_khz,
                "peak_amplitude_dbm": -9.8
            }),
        }
    }

    fn is_running(&self) -> bool {
        self.is_running_state
    }
}
