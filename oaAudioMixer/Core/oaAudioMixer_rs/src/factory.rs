// oaAudioMixer/Core/oaAudioMixer_rs/src/factory.rs
use crate::manager::AudioConnectionManager;

#[cfg(target_os = "windows")]
use crate::windows_backend::WindowsAudioManager;

#[cfg(target_os = "linux")]
use crate::linux_backend::LinuxAudioManager;

#[cfg(target_os = "macos")]
use crate::macos_backend::MacosAudioManager;

// The Factory Function
pub fn get_os_manager() -> Box<dyn AudioConnectionManager> {
    #[cfg(target_os = "windows")]
    {
        Box::new(WindowsAudioManager::new())
    }
    
    #[cfg(target_os = "linux")]
    {
        Box::new(LinuxAudioManager::new())
    }

    #[cfg(target_os = "macos")]
    {
        Box::new(MacosAudioManager::new())
    }
    
    #[cfg(not(any(target_os = "windows", target_os = "linux", target_os = "macos")))]
    {
        unimplemented!("Unsupported Operating System!");
    }
}
