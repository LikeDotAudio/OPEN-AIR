// oaAudioMixer/Core/oaAudioMixer_rs/src/manager.rs

#[derive(Debug)]
pub struct AudioApp {
    pub name: String,
    pub pid: u32,
    pub driver: String,
    pub volume: f32,
    pub is_active: bool,
}

#[derive(Debug)]
pub struct AudioDevice {
    pub name: String,
    pub description: String,
    pub sample_rate: u32,
    pub channels: u8,
    pub volume: f32,
    pub is_default: bool,
}

pub trait AudioConnectionManager: Send + Sync {
    fn get_master_volume(&self) -> Result<f32, String>;
    fn set_master_volume(&mut self, level: f32) -> Result<(), String>;

    fn set_device_volume(&mut self, id: String, level: f32) -> Result<(), String>;
    fn set_app_volume(&mut self, id: u32, level: f32) -> Result<(), String>;
    
    fn get_connected_software(&self) -> Result<Vec<AudioApp>, String>;
    fn get_available_devices(&self) -> Result<Vec<AudioDevice>, String>;
    fn get_available_sources(&self) -> Result<Vec<AudioDevice>, String>;
}
