// oaAudioMixer/Core/oaAudioMixer_rs/src/manager.rs

#[derive(Debug)]
pub struct AudioApp {
    pub name: String,
    pub is_active: bool,
}

pub trait AudioConnectionManager: Send + Sync {
    /// Gets the master volume of the default device (0.0 to 1.0)
    fn get_master_volume(&self) -> Result<f32, String>;
    
    /// Sets the master volume (0.0 to 1.0)
    fn set_master_volume(&mut self, level: f32) -> Result<(), String>;
    
    /// Discovers all software currently holding an audio session
    fn get_connected_software(&self) -> Result<Vec<AudioApp>, String>;
}
