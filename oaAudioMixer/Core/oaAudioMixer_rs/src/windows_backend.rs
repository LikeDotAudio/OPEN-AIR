// oaAudioMixer/Core/oaAudioMixer_rs/src/windows_backend.rs
#[cfg(target_os = "windows")]
pub struct WindowsAudioManager {}
#[cfg(target_os = "windows")]
impl WindowsAudioManager { pub fn new() -> Self { WindowsAudioManager {} } }
#[cfg(target_os = "windows")]
impl crate::manager::AudioConnectionManager for WindowsAudioManager {
    fn get_master_volume(&self) -> Result<f32, String> { Ok(0.75) }
    fn set_master_volume(&mut self, _l: f32) -> Result<(), String> { Ok(()) }
    fn set_device_volume(&mut self, _i: String, _l: f32) -> Result<(), String> { Ok(()) }
    fn set_app_volume(&mut self, _i: u32, _l: f32) -> Result<(), String> { Ok(()) }
    fn get_connected_software(&self) -> Result<Vec<crate::manager::AudioApp>, String> { Ok(vec![]) }
    fn get_available_devices(&self) -> Result<Vec<crate::manager::AudioDevice>, String> { Ok(vec![]) }
    fn get_available_sources(&self) -> Result<Vec<crate::manager::AudioDevice>, String> { Ok(vec![]) }
}
