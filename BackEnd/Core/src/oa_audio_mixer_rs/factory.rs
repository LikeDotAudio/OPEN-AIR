/**
 * Header: factory.rs
 * Purpose: factory.rs implementation.
 * Description: Logic and implementation for factory.rs implementation.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// oaAudioMixer/Core/oaAudioMixer_rs/factory.rs
// Author: Gemini Architect
// Version: 20260413.1400.1
//
// Description: Factory for cross-platform audio manager instantiation. 
// Dispatches to OS-specific backends (Linux, Windows, MacOS).

use crate::oa_audio_mixer_rs::manager::AudioConnectionManager;

#[cfg(target_os = "windows")]
use crate::oa_audio_mixer_rs::windows_backend::WindowsAudioManager;

#[cfg(target_os = "linux")]
use crate::oa_audio_mixer_rs::linux_backend::LinuxAudioManager;

#[cfg(target_os = "macos")]
use crate::oa_audio_mixer_rs::macos_backend::MacosAudioManager;

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
