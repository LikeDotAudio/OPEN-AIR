// oaAudioMixer/Core/oaAudioMixer_rs/src/linux_backend.rs
use std::process::Command;

#[cfg(target_os = "linux")]
pub struct LinuxAudioManager {}

#[cfg(target_os = "linux")]
impl LinuxAudioManager {
    pub fn new() -> Self { LinuxAudioManager {} }

    fn run_wpctl_status(&self) -> Result<String, String> {
        let output = Command::new("wpctl").arg("status").output().map_err(|e| e.to_string())?;
        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    }

    fn run_wpctl_set_volume(&self, target: &str, level: f32) -> Result<(), String> {
        let level_str = format!("{:.2}", level);
        Command::new("wpctl").args(&["set-volume", target, &level_str]).output().map_err(|e| e.to_string())?;
        Ok(())
    }

    fn parse_devices_from_section(&self, status: &str, section_header: &str) -> Vec<crate::manager::AudioDevice> {
        let mut devices = Vec::new();
        let mut in_section = false;
        for line in status.lines() {
            if line.contains(section_header) { in_section = true; continue; }
            if in_section && line.trim().is_empty() { in_section = false; continue; }
            if in_section && (line.contains('.') || line.contains('*')) {
                let is_default = line.contains('*');
                let clean = line.replace(['│','└','├','─','*'], "").trim().to_string();
                if let Some(dot_idx) = clean.find('.') {
                    let id = &clean[..dot_idx].trim();
                    let mut desc = clean[dot_idx+1..].trim().to_string();
                    let mut vol = 1.0;
                    if let Some(v_idx) = desc.find("[vol: ") {
                        if let Some(end) = desc[v_idx+6..].find(']') {
                            vol = desc[v_idx+6..v_idx+6+end].parse().unwrap_or(1.0);
                        }
                        desc = desc[..v_idx].trim().to_string();
                    }
                    devices.push(crate::manager::AudioDevice {
                        name: id.to_string(),
                        description: desc,
                        sample_rate: 48000,
                        channels: 2,
                        volume: vol,
                        is_default,
                    });
                }
            }
        }
        devices
    }
}

#[cfg(target_os = "linux")]
impl crate::manager::AudioConnectionManager for LinuxAudioManager {
    fn get_master_volume(&self) -> Result<f32, String> {
        let status = self.run_wpctl_status()?;
        for line in status.lines() {
            if line.contains('*') && line.contains("[vol:") {
                if let Some(v_idx) = line.find("vol: ") {
                    if let Some(end) = line[v_idx+5..].find(']') {
                        return Ok(line[v_idx+5..v_idx+5+end].parse().unwrap_or(0.5));
                    }
                }
            }
        }
        Ok(0.5)
    }

    fn set_master_volume(&mut self, level: f32) -> Result<(), String> {
        self.run_wpctl_set_volume("@DEFAULT_AUDIO_SINK@", level)
    }

    fn set_device_volume(&mut self, id: String, level: f32) -> Result<(), String> {
        self.run_wpctl_set_volume(&id, level)
    }

    fn set_app_volume(&mut self, id: u32, level: f32) -> Result<(), String> {
        self.run_wpctl_set_volume(&id.to_string(), level)
    }

    fn get_connected_software(&self) -> Result<Vec<crate::manager::AudioApp>, String> {
        let status = self.run_wpctl_status()?;
        let mut apps = Vec::new();
        let mut in_streams = false;
        for line in status.lines() {
            if line.contains("Streams:") { in_streams = true; continue; }
            if in_streams && line.trim().is_empty() { in_streams = false; continue; }
            if in_streams && line.contains('.') && !line.contains("output_") {
                let clean = line.replace(['│','└','├','─'], "").trim().to_string();
                if let Some(dot_idx) = clean.find('.') {
                    let id_str = &clean[..dot_idx].trim();
                    let mut name = clean[dot_idx+1..].trim().to_string();
                    let mut vol = 1.0;
                    if let Some(v_idx) = name.find("[vol: ") {
                        if let Some(end) = name[v_idx+6..].find(']') {
                            vol = name[v_idx+6..v_idx+6+end].parse().unwrap_or(1.0);
                        }
                        name = name[..v_idx].trim().to_string();
                    }
                    if let Ok(id) = id_str.parse::<u32>() {
                        apps.push(crate::manager::AudioApp {
                            name,
                            pid: id,
                            driver: "PipeWire".to_string(),
                            volume: vol,
                            is_active: status.contains("[active]"),
                        });
                    }
                }
            }
        }
        Ok(apps)
    }

    fn get_available_devices(&self) -> Result<Vec<crate::manager::AudioDevice>, String> {
        Ok(self.parse_devices_from_section(&self.run_wpctl_status()?, "Sinks:"))
    }

    fn get_available_sources(&self) -> Result<Vec<crate::manager::AudioDevice>, String> {
        Ok(self.parse_devices_from_section(&self.run_wpctl_status()?, "Sources:"))
    }
}
