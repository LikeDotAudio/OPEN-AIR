use serde::{Deserialize, Serialize};
use serde_json::json;
use crate::traits::{GuiCommand, OrchestratorStepResult, TestOrchestrator};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WaveformTestOrchestrator {
    pub start_freq_mhz: f64,
    pub stop_freq_mhz: f64,
    pub step_mhz: f64,
    pub current_scan_freq_mhz: f64,
    pub oscillators_linked: bool,
    pub is_running_state: bool,
}

impl WaveformTestOrchestrator {
    pub fn new() -> Self {
        Self {
            start_freq_mhz: 1.0,
            stop_freq_mhz: 100.0,
            step_mhz: 5.0,
            current_scan_freq_mhz: 1.0,
            oscillators_linked: true,
            is_running_state: false,
        }
    }
}

impl TestOrchestrator for WaveformTestOrchestrator {
    fn name(&self) -> &'static str {
        "Waveform_Test"
    }

    fn topic_prefix(&self) -> &'static str {
        "OpenAir/Tests/Waveform"
    }

    fn initialize(&mut self) -> bool {
        self.start_freq_mhz = 1.0;
        self.stop_freq_mhz = 100.0;
        self.step_mhz = 5.0;
        self.current_scan_freq_mhz = 1.0;
        self.oscillators_linked = true;
        self.is_running_state = false;
        true
    }

    fn handle_gui_command(&mut self, cmd: GuiCommand) -> Option<serde_json::Value> {
        if cmd.topic.ends_with("/Scan/StartFreqMHz") {
            if let Some(val) = cmd.payload.as_f64() {
                self.start_freq_mhz = val;
                return Some(json!({ "start_freq_mhz": self.start_freq_mhz }));
            }
        } else if cmd.topic.ends_with("/Scan/StopFreqMHz") {
            if let Some(val) = cmd.payload.as_f64() {
                self.stop_freq_mhz = val;
                return Some(json!({ "stop_freq_mhz": self.stop_freq_mhz }));
            }
        } else if cmd.topic.ends_with("/Scan/MasterEnable") {
            if let Some(val) = cmd.payload.as_bool() {
                self.is_running_state = val;
                return Some(json!({ "scan_running": self.is_running_state }));
            }
        } else if cmd.topic.ends_with("/Oscillators/LinkAll") {
            if let Some(val) = cmd.payload.as_bool() {
                self.oscillators_linked = val;
                return Some(json!({ "oscillators_linked": self.oscillators_linked }));
            }
        }
        None
    }

    fn execute_step(&mut self) -> OrchestratorStepResult {
        if !self.is_running_state {
            return OrchestratorStepResult {
                status: "IDLE".to_string(),
                data: json!({ "current_scan_freq_mhz": self.current_scan_freq_mhz }),
            };
        }

        self.current_scan_freq_mhz += self.step_mhz;
        if self.current_scan_freq_mhz > self.stop_freq_mhz {
            self.current_scan_freq_mhz = self.start_freq_mhz;
        }

        let mut channel_readouts = Vec::with_capacity(8);
        for i in 0..8 {
            let attenuation = (1.0 - (self.current_scan_freq_mhz / 500.0) * ((i % 4) as f64 + 1.0) * 0.1).max(0.2);
            channel_readouts.push((attenuation * 100.0).round() / 100.0);
        }

        OrchestratorStepResult {
            status: "SWEEPING".to_string(),
            data: json!({
                "scan_point_mhz": format!("{:.3} MHz", self.current_scan_freq_mhz),
                "channel_vpp_readouts": channel_readouts,
                "sync_lock": "LOCKED"
            }),
        }
    }

    fn is_running(&self) -> bool {
        self.is_running_state
    }
}
