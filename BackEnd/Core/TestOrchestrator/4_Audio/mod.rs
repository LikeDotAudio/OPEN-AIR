use serde::{Deserialize, Serialize};
use serde_json::json;
use std::f64::consts::PI;
use crate::traits::{GuiCommand, OrchestratorStepResult, TestOrchestrator};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AudioTestOrchestrator {
    pub start_freq_hz: f64,
    pub stop_freq_hz: f64,
    pub sweep_time_sec: f64,
    pub current_freq_hz: f64,
    pub is_running_state: bool,
}

impl AudioTestOrchestrator {
    pub fn new() -> Self {
        Self {
            start_freq_hz: 20.0,
            stop_freq_hz: 20000.0,
            sweep_time_sec: 5.0,
            current_freq_hz: 20.0,
            is_running_state: false,
        }
    }
}

impl TestOrchestrator for AudioTestOrchestrator {
    fn name(&self) -> &'static str {
        "Audio_Test"
    }

    fn topic_prefix(&self) -> &'static str {
        "OpenAir/Tests/Audio"
    }

    fn initialize(&mut self) -> bool {
        self.start_freq_hz = 20.0;
        self.stop_freq_hz = 20000.0;
        self.sweep_time_sec = 5.0;
        self.current_freq_hz = 20.0;
        self.is_running_state = false;
        true
    }

    fn handle_gui_command(&mut self, cmd: GuiCommand) -> Option<serde_json::Value> {
        if cmd.topic.ends_with("/Oscillator/StartFreq") {
            if let Some(val) = cmd.payload.as_f64() {
                self.start_freq_hz = val;
                return Some(json!({ "start_freq_hz": self.start_freq_hz }));
            }
        } else if cmd.topic.ends_with("/Oscillator/StopFreq") {
            if let Some(val) = cmd.payload.as_f64() {
                self.stop_freq_hz = val;
                return Some(json!({ "stop_freq_hz": self.stop_freq_hz }));
            }
        } else if cmd.topic.ends_with("/Oscillator/TriggerSweep") {
            if let Some(val) = cmd.payload.as_bool() {
                self.is_running_state = val;
                return Some(json!({ "sweep_running": self.is_running_state }));
            }
        }
        None
    }

    fn execute_step(&mut self) -> OrchestratorStepResult {
        if !self.is_running_state {
            return OrchestratorStepResult {
                status: "IDLE".to_string(),
                data: json!({ "current_freq_hz": self.current_freq_hz }),
            };
        }

        self.current_freq_hz *= 1.5;
        if self.current_freq_hz > self.stop_freq_hz {
            self.current_freq_hz = self.start_freq_hz;
        }

        let gain_db = -20.0 * (1.0 + (self.current_freq_hz / 1000.0).powi(2)).sqrt().log10();
        let phase_deg = -(self.current_freq_hz / 1000.0).atan() * (180.0 / PI);

        OrchestratorStepResult {
            status: "LOG_SWEEPING".to_string(),
            data: json!({
                "freq_hz": (self.current_freq_hz * 10.0).round() / 10.0,
                "input_vrms": 1.0,
                "output_vrms": ((10.0f64.powf(gain_db / 20.0)) * 1000.0).round() / 1000.0,
                "gain_db": (gain_db * 100.0).round() / 100.0,
                "phase_deg": (phase_deg * 10.0).round() / 10.0,
                "thd_percent": "0.05%"
            }),
        }
    }

    fn is_running(&self) -> bool {
        self.is_running_state
    }
}
