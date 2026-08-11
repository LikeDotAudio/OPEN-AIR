pub mod traits;

#[path = "../1_Spectrum/mod.rs"]
pub mod spectrum;

#[path = "../2_Waveform/mod.rs"]
pub mod waveform;

#[path = "../4_Audio/mod.rs"]
pub mod audio;

#[path = "../4_Power/mod.rs"]
pub mod power;

use std::collections::HashMap;
use serde_json::Value;

pub use traits::{GuiCommand, OrchestratorStepResult, TestOrchestrator};
pub use spectrum::SpectrumTestOrchestrator;
pub use waveform::WaveformTestOrchestrator;
pub use audio::AudioTestOrchestrator;
pub use power::PowerTestOrchestrator;

pub struct TestOrchestratorManager {
    pub orchestrators: HashMap<String, Box<dyn TestOrchestrator>>,
}

impl TestOrchestratorManager {
    pub fn new() -> Self {
        let mut map: HashMap<String, Box<dyn TestOrchestrator>> = HashMap::new();
        map.insert("Spectrum_Test".to_string(), Box::new(SpectrumTestOrchestrator::new()));
        map.insert("Waveform_Test".to_string(), Box::new(WaveformTestOrchestrator::new()));
        map.insert("Audio_Test".to_string(), Box::new(AudioTestOrchestrator::new()));
        map.insert("Power_Test".to_string(), Box::new(PowerTestOrchestrator::new()));

        Self { orchestrators: map }
    }

    pub fn initialize_all(&mut self) {
        for (name, orch) in self.orchestrators.iter_mut() {
            orch.initialize();
            println!("[TestOrchestratorManager] Initialized Rust Test Orchestrator: {}", name);
        }
    }

    pub fn dispatch_gui_command(&mut self, test_name: &str, topic: String, payload: Value) -> Option<Value> {
        if let Some(orch) = self.orchestrators.get_mut(test_name) {
            let cmd = GuiCommand { topic, payload };
            orch.handle_gui_command(cmd)
        } else {
            None
        }
    }

    pub fn step_all(&mut self) -> HashMap<String, OrchestratorStepResult> {
        let mut results = HashMap::new();
        for (name, orch) in self.orchestrators.iter_mut() {
            if orch.is_running() {
                results.insert(name.clone(), orch.execute_step());
            }
        }
        results
    }
}
